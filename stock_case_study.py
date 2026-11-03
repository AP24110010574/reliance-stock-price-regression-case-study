"""One-day-ahead Reliance Industries closing-price regression case study.

The script downloads a fixed public CSV, engineers only information available
on day t, predicts the close on day t+1, and evaluates chronologically.
It is an educational regression exercise, not investment advice.
"""

from pathlib import Path
import json
import urllib.request

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "reliance_nse_ohlcv.csv"
RESULTS = ROOT / "results"
RESULTS.mkdir(exist_ok=True)
DATA_URL = (
    "https://media.githubusercontent.com/media/Dr-Kitz28/NSE-OHLCV-Data/"
    "032b64127fa39b2910e18a7e2dc067faeb1bf5ef/P2/RELIANCE/RELIANCE_daily.csv"
)
SEED = 42


def load_data():
    if not DATA.exists():
        request = urllib.request.Request(DATA_URL, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(request, timeout=30) as response:
            DATA.write_bytes(response.read())
    df = pd.read_csv(DATA, parse_dates=["date"])
    df["date"] = pd.to_datetime(df["date"], utc=True).dt.tz_convert("Asia/Kolkata").dt.tz_localize(None)
    df = df.sort_values("date")
    df = df[(df.date >= "2015-01-01") & (df.date <= "2019-12-31")]
    required = ["open", "high", "low", "close", "volume"]
    if df[required].isna().any().any():
        raise ValueError("Required source columns contain missing data; inspect the downloaded file.")
    return df.set_index("date")


def make_supervised(df):
    close = df["close"].astype(float)
    ret = close.pct_change()
    X = pd.DataFrame(index=df.index)
    X["close_t"] = close
    for lag in (1, 2, 3, 5, 10):
        X[f"return_{lag}d"] = close.pct_change(lag)
    X["mean_return_5d"] = ret.rolling(5).mean()
    X["volatility_5d"] = ret.rolling(5).std()
    X["mean_return_20d"] = ret.rolling(20).mean()
    X["volatility_20d"] = ret.rolling(20).std()
    X["ma5_gap"] = close / close.rolling(5).mean() - 1
    X["ma20_gap"] = close / close.rolling(20).mean() - 1
    X["intraday_range"] = (df["high"] - df["low"]) / df["close"]
    X["open_gap"] = df["open"] / df["close"].shift(1) - 1
    X["volume_change_1d"] = df["volume"].pct_change()
    X["volume_mean_5d_ratio"] = df["volume"] / df["volume"].rolling(5).mean()
    y = close.shift(-1).rename("next_day_close")
    frame = X.join(y).replace([np.inf, -np.inf], np.nan).dropna()
    return frame.drop(columns=y.name), frame[y.name]


def metrics(y, pred):
    return {
        "MAE_INR": mean_absolute_error(y, pred),
        "RMSE_INR": np.sqrt(mean_squared_error(y, pred)),
        "R2": r2_score(y, pred),
    }


def main():
    raw = load_data()
    X, y = make_supervised(raw)
    n = len(X)
    train_end = int(n * 0.70)
    validation_end = int(n * 0.85)
    splits = {
        "train": np.arange(0, train_end),
        "validation": np.arange(train_end, validation_end),
        "test": np.arange(validation_end, n),
    }
    assert max(splits["train"]) < min(splits["validation"])
    assert max(splits["validation"]) < min(splits["test"])
    ytr, yv, yt = (y.iloc[splits[k]] for k in ("train", "validation", "test"))
    Xtr, Xv, Xt = (X.iloc[splits[k]] for k in ("train", "validation", "test"))

    linear_val_model = make_pipeline(StandardScaler(), LinearRegression())
    linear_val_model.fit(Xtr, ytr)

    rf_candidates = []
    for depth in (2, 4, 8, None):
        model = RandomForestRegressor(
            n_estimators=300,
            max_depth=depth,
            min_samples_leaf=2,
            random_state=SEED,
            n_jobs=-1,
        )
        model.fit(Xtr, ytr)
        pred = model.predict(Xv)
        rf_candidates.append((mean_absolute_error(yv, pred), depth))
    _, selected_depth = min(rf_candidates, key=lambda row: row[0])

    # Freeze hyperparameters from validation, then use all pre-test history.
    fit_idx = np.arange(validation_end)
    Xfit, yfit = X.iloc[fit_idx], y.iloc[fit_idx]
    linear = make_pipeline(StandardScaler(), LinearRegression()).fit(Xfit, yfit)
    forest = RandomForestRegressor(
        n_estimators=300,
        max_depth=selected_depth,
        min_samples_leaf=2,
        random_state=SEED,
        n_jobs=-1,
    ).fit(Xfit, yfit)

    models = {"Persistence baseline": None, "Linear Regression": linear, "Random Forest": forest}
    rows, predictions = [], []
    for name, model in models.items():
        pred = Xt["close_t"].to_numpy() if model is None else model.predict(Xt)
        rows.append({"model": name, **metrics(yt, pred)})
        predictions.append(pd.DataFrame({
            "date": yt.index,
            "actual_close": yt.to_numpy(),
            "predicted_close": pred,
            "absolute_error": np.abs(yt.to_numpy() - pred),
            "model": name,
        }))
    result = pd.DataFrame(rows)
    pred_frame = pd.concat(predictions, ignore_index=True)
    result.to_csv(RESULTS / "test_metrics.csv", index=False)
    pred_frame.to_csv(RESULTS / "test_predictions.csv", index=False)
    pd.DataFrame([
        {"split": key, "samples": len(indices), "start": X.index[indices[0]].date(), "end": X.index[indices[-1]].date()}
        for key, indices in splits.items()
    ]).to_csv(RESULTS / "split_counts.csv", index=False)

    ml_test = pred_frame[pred_frame.model == "Linear Regression"].sort_values("date")
    best_i = ml_test.absolute_error.idxmin()
    worst_i = ml_test.absolute_error.idxmax()
    examples = pd.DataFrame([
        {**ml_test.loc[best_i].to_dict(), "example": "smallest error"},
        {**ml_test.loc[worst_i].to_dict(), "example": "largest error"},
    ])
    examples.to_csv(RESULTS / "example_predictions.csv", index=False)

    fig, ax = plt.subplots(figsize=(9, 4.5))
    actual = pred_frame[pred_frame.model == "Linear Regression"].sort_values("date")
    persistence = pred_frame[pred_frame.model == "Persistence baseline"].sort_values("date")
    forest_pred = pred_frame[pred_frame.model == "Random Forest"].sort_values("date")
    ax.plot(actual.date, actual.actual_close, color="#222222", linewidth=1.7, label="Actual")
    ax.plot(actual.date, actual.predicted_close, color="#167D8D", linewidth=1.3, label="Linear regression")
    ax.plot(forest_pred.date, forest_pred.predicted_close, color="#8D5B9B", linewidth=1.0, label="Random forest")
    ax.plot(persistence.date, persistence.predicted_close, color="#C46A32", linewidth=1.0, alpha=.9, label="Persistence")
    ax.set(title="Reliance closing price: chronological test period", ylabel="Closing price (₹)", xlabel="Trading date")
    ax.grid(alpha=.2)
    ax.legend(frameon=False, ncol=3)
    fig.tight_layout()
    fig.savefig(RESULTS / "test_predictions.png", dpi=180)
    plt.close(fig)

    metadata = {
        "ticker": "RELIANCE (NSE)",
        "currency": "INR",
        "source": DATA_URL,
        "first_source_date": str(raw.index.min().date()),
        "last_source_date": str(raw.index.max().date()),
        "source_rows": len(raw),
        "supervised_rows": n,
        "input_features": X.columns.tolist(),
        "target": "next trading day's NSE closing price in INR",
        "selected_random_forest_max_depth": selected_depth,
        "random_state": SEED,
        "warning": "Educational historical regression only; not financial advice or a trading system.",
    }
    (RESULTS / "experiment.json").write_text(json.dumps(metadata, indent=2))
    print("Reliance NSE rows, 2015-2019:", len(raw), "| usable supervised examples:", n, "| features:", X.shape[1])
    print("Selected random forest max_depth:", selected_depth)
    print(result.to_string(index=False, float_format=lambda value: f"{value:.4f}"))
    print("Splits:\n", pd.read_csv(RESULTS / "split_counts.csv").to_string(index=False))
    print("Linear-regression examples:\n", examples.to_string(index=False))


if __name__ == "__main__":
    main()
