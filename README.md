# Reliance Industries stock-price regression case study

This regression case study predicts the next trading day's Reliance Industries closing price in Indian rupees (INR, ₹) from historical OHLCV features. It is separate from the RoadLens project.

## Reproduce

Use Python 3.10 or later. Install dependencies and run the experiment:

```bash
python -m pip install -r requirements.txt
python stock_case_study.py
```

The script uses the included CSV, or downloads a pinned source snapshot if the CSV is absent. It filters to 2015-01-01 through 2019-12-31, builds 16 features from current/past values only, and uses chronological 70/15/15 train/validation/test splits. Validation selects random-forest depth; final models are refit on all pre-test data. Metrics, predictions, split counts, example predictions, experiment metadata, and a comparison plot are written to `results/`.

To rebuild the report with the course template, set `CLA3_TEMPLATE_PATH` to your local copy of `CLA3_Case_Study_Template.docx` and run `python build_stock_report.py`. The template itself is not included.

## Dataset and interpretation

Dataset: Dr-Kitz28, `NSE-OHLCV-Data`, `P2/RELIANCE/RELIANCE_daily.csv`, pinned at commit [`032b64127fa39b2910e18a7e2dc067faeb1bf5ef`](https://github.com/Dr-Kitz28/NSE-OHLCV-Data/tree/032b64127fa39b2910e18a7e2dc067faeb1bf5ef/P2/RELIANCE). The dataset is licensed CC BY-NC 4.0; attribution is required and non-commercial-use terms apply. The provider does not document its corporate-action adjustment procedure.

This experiment contains 1,234 source rows and 1,213 usable supervised examples. The held-out test has 182 examples. In the recorded run, test MAE was ₹7.89 for the persistence baseline, ₹8.01 for linear regression, and ₹27.99 for random forest. The baseline performed best. Results cover one company and one historical window; they are for coursework, not investment advice or evidence of future returns.

## Files

- `Reliance_Stock_Closing_Price_Case_Study.docx`: report based on the supplied CLA-3 template.
- `stock_case_study.py`: runnable implementation.
- `reliance_nse_ohlcv.csv`: downloaded source data (the model uses the stated date range).
- `results/`: executed outputs used in the report.
- `build_stock_report.py`: optional report builder; requires the course template supplied separately.
