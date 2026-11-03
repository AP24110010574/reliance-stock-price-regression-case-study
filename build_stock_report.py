from copy import deepcopy
import os
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import shutil
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent
TEMPLATE = Path(os.environ.get('CLA3_TEMPLATE_PATH', Path(__file__).resolve().parent / 'CLA3_Case_Study_Template.docx'))
RESULTS = ROOT / 'results'
OUTPUT = ROOT / 'Reliance_Stock_Closing_Price_Case_Study.docx'
PLOT = RESULTS / 'test_predictions.png'

W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
R = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
WP = 'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing'
A = 'http://schemas.openxmlformats.org/drawingml/2006/main'
PIC = 'http://schemas.openxmlformats.org/drawingml/2006/picture'
PKG_REL = 'http://schemas.openxmlformats.org/package/2006/relationships'
CT = 'http://schemas.openxmlformats.org/package/2006/content-types'
NS = {'w': W, 'r': R, 'wp': WP, 'a': A, 'pic': PIC}
def q(ns, name): return f'{{{ns}}}{name}'

def ptext(p):
    return ''.join(x.text or '' for x in p.findall('.//w:t', NS)).strip()

def make_p(text, prototype):
    p = deepcopy(prototype)
    for child in list(p):
        if child.tag != q(W, 'pPr'):
            p.remove(child)
    run = ET.SubElement(p, q(W, 'r'))
    existing_rpr = prototype.find('.//w:rPr', NS)
    if existing_rpr is not None:
        run.append(deepcopy(existing_rpr))
    node = ET.SubElement(run, q(W, 't'))
    node.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
    node.text = text
    return p

def make_table(rows):
    tbl = ET.Element(q(W, 'tbl'))
    props = ET.SubElement(tbl, q(W, 'tblPr'))
    width = ET.SubElement(props, q(W, 'tblW')); width.set(q(W, 'w'), '9360'); width.set(q(W, 'type'), 'dxa')
    borders = ET.SubElement(props, q(W, 'tblBorders'))
    for name in ('top','left','bottom','right','insideH','insideV'):
        edge = ET.SubElement(borders, q(W, name)); edge.set(q(W, 'val'), 'single'); edge.set(q(W, 'sz'), '5'); edge.set(q(W, 'color'), '8A8A8A')
    grid = ET.SubElement(tbl, q(W, 'tblGrid'))
    widths = [3300, 2020, 2020, 2020]
    for value in widths:
        col = ET.SubElement(grid, q(W, 'gridCol')); col.set(q(W, 'w'), str(value))
    for ri, values in enumerate(rows):
        tr = ET.SubElement(tbl, q(W, 'tr'))
        if ri == 0:
            trpr = ET.SubElement(tr, q(W, 'trPr')); ET.SubElement(trpr, q(W, 'tblHeader'))
        for ci, value in enumerate(values):
            tc = ET.SubElement(tr, q(W, 'tc'))
            tcpr = ET.SubElement(tc, q(W, 'tcPr'))
            tcw = ET.SubElement(tcpr, q(W, 'tcW')); tcw.set(q(W, 'w'), str(widths[ci])); tcw.set(q(W, 'type'), 'dxa')
            if ri == 0:
                shd = ET.SubElement(tcpr, q(W, 'shd')); shd.set(q(W, 'val'), 'clear'); shd.set(q(W, 'fill'), 'E7E7E7')
            p = ET.SubElement(tc, q(W, 'p'))
            ppr = ET.SubElement(p, q(W, 'pPr'))
            jc = ET.SubElement(ppr, q(W, 'jc')); jc.set(q(W, 'val'), 'center')
            run = ET.SubElement(p, q(W, 'r'))
            rpr = ET.SubElement(run, q(W, 'rPr'))
            fonts = ET.SubElement(rpr, q(W, 'rFonts')); fonts.set(q(W, 'ascii'), 'Arial'); fonts.set(q(W, 'hAnsi'), 'Arial')
            size = ET.SubElement(rpr, q(W, 'sz')); size.set(q(W, 'val'), '18')
            if ri == 0: ET.SubElement(rpr, q(W, 'b'))
            t = ET.SubElement(run, q(W, 't')); t.text = value
    return tbl

def make_picture(rel_id):
    p = ET.Element(q(W, 'p'))
    ppr = ET.SubElement(p, q(W, 'pPr'))
    jc = ET.SubElement(ppr, q(W, 'jc')); jc.set(q(W, 'val'), 'center')
    run = ET.SubElement(p, q(W, 'r'))
    drawing = ET.SubElement(run, q(W, 'drawing'))
    inline = ET.SubElement(drawing, q(WP, 'inline'))
    inline.set('distT','0'); inline.set('distB','0'); inline.set('distL','0'); inline.set('distR','0')
    ET.SubElement(inline, q(WP, 'extent'), {'cx':'5120640','cy':'2560320'})
    ET.SubElement(inline, q(WP, 'docPr'), {'id':'1','name':'Reliance stock test-period predictions'})
    frame = ET.SubElement(inline, q(WP, 'cNvGraphicFramePr'))
    locks = ET.SubElement(frame, q(A, 'graphicFrameLocks')); locks.set('noChangeAspect','1')
    graphic = ET.SubElement(inline, q(A, 'graphic'))
    gd = ET.SubElement(graphic, q(A, 'graphicData')); gd.set('uri', PIC)
    pic = ET.SubElement(gd, q(PIC, 'pic'))
    nv = ET.SubElement(pic, q(PIC, 'nvPicPr'))
    ET.SubElement(nv, q(PIC, 'cNvPr'), {'id':'0','name':'test_predictions.png'})
    ET.SubElement(nv, q(PIC, 'cNvPicPr'))
    fill = ET.SubElement(pic, q(PIC, 'blipFill'))
    ET.SubElement(fill, q(A, 'blip'), {q(R, 'embed'):rel_id})
    stretch = ET.SubElement(fill, q(A, 'stretch')); ET.SubElement(stretch, q(A, 'fillRect'))
    sp = ET.SubElement(pic, q(PIC, 'spPr'))
    xfrm = ET.SubElement(sp, q(A, 'xfrm')); ET.SubElement(xfrm, q(A, 'off'), {'x':'0','y':'0'})
    ET.SubElement(xfrm, q(A, 'ext'), {'cx':'5120640','cy':'2560320'})
    geom = ET.SubElement(sp, q(A, 'prstGeom')); geom.set('prst','rect'); ET.SubElement(geom, q(A, 'avLst'))
    return p

results = __import__('pandas').read_csv(RESULTS / 'test_metrics.csv').set_index('model')
examples = __import__('pandas').read_csv(RESULTS / 'example_predictions.csv')
lr = results.loc['Linear Regression']; rf = results.loc['Random Forest']; base = results.loc['Persistence baseline']
easy, hard = examples.iloc[0], examples.iloc[1]

sections = {
    '1. Introduction and Problem Statement': [
        'Stock prices change from one trading day to the next and are influenced by company news, investor expectations, and wider market conditions. This case study asks a narrow regression question: using only information available by the end of a trading day, how closely can a model estimate Reliance Industries Limited’s closing price in Indian rupees (₹) on the next trading day?',
        'We compare linear regression with a random forest regressor and include a persistence baseline that predicts tomorrow’s close as today’s close. This baseline matters because daily prices often move gradually. The experiment evaluates prediction error on a later time period; it does not test a trading strategy or claim that stock prices can be reliably forecast.'
    ],
    '2. Base Paper Summary': [
        'Vijh, Chandola, Tikkiwal, and Kumar studied next-day closing-price prediction using historical financial variables. They used open, high, low, and close prices to create model inputs, then compared an artificial neural network with a random forest on five companies. Their paper reports RMSE and MAPE as evaluation measures [1]. This is a relevant base paper because it frames stock-price forecasting as a supervised regression task and uses a tree ensemble similar to one model in our experiment.',
        'Our work is a small classroom comparison, not a replication: it uses daily Reliance Industries data in ₹, linear regression and random forest, an explicit chronological holdout, and a persistence baseline. The paper’s results are not directly comparable to ours because its companies, date ranges, features, splits, and implementation differ.'
    ],
    '3. Method / Model Explanation': [
        'The target for date t is the closing price in ₹ on the next trading date, denoted y(t+1). Sixteen predictors are constructed only from date t and earlier: current close; returns over 1, 2, 3, 5, and 10 trading days; 5- and 20-day mean returns and volatility; gaps from 5- and 20-day moving averages; intraday high-low range; opening gap; daily volume change; and volume relative to its 5-day mean.',
        'Linear regression estimates coefficients that minimize squared residuals. Its prediction is ŷ(t+1) = β₀ + Σⱼ βⱼxⱼ. Here ŷ(t+1) is the predicted next closing price, xⱼ is one of the 16 input features, βⱼ is its learned weight, and β₀ is the intercept. Before fitting, numeric inputs are standardized using pre-test training data. A random forest averages predictions from many decision trees, each trained on a bootstrap sample; its maximum depth was selected on the validation period.',
        f'Worked example from the test predictions: for {easy.date}, linear regression predicted ₹{easy.predicted_close:.4f}; the recorded close was ₹{easy.actual_close:.4f}. The absolute error is |{easy.actual_close:.4f} - {easy.predicted_close:.4f}| = ₹{easy.absolute_error:.4f}. Mean absolute error (MAE) averages absolute errors in rupees; root mean squared error (RMSE) penalizes larger errors more; R² compares squared error with predicting the test-set mean. Lower MAE/RMSE is better; R² nearer 1 is better, but none alone establishes trading value.'
    ],
    '4. Implementation': [
        'The dataset is Reliance Industries Limited daily OHLCV history in ₹, downloaded from a public NSE-data repository. The selected period, 2015-01-01 through 2019-12-31, contains 1,234 daily rows with six columns: date, open, high, low, close, and volume. After creating lagged/rolling features and removing rows without a complete 20-day history or a next-day target, 1,213 examples remain [2].',
        'The Python implementation uses pandas, NumPy, scikit-learn, and Matplotlib. Rows are kept in date order: the first 70% (849 examples) train the models, the next 15% (182) select random-forest depth, and the final 15% (182) form the untouched test set. After depth selection, both ML models are refit on the pre-test training and validation history. The random forest uses 300 trees, a fixed random seed of 42, and minimum leaf size 2. Results, predictions, split dates, and the comparison graph are saved in the accompanying case-study folder.',
        'A key implementation risk is temporal leakage: a random split could place later observations in training and earlier observations in testing. The code therefore uses chronological splits and builds every feature from current or past values. The dataset is limited to one company and five calendar years, so this setup is suitable for demonstration, not robust financial research.'
    ],
    '5. Results and Discussion': [
        ('p', 'The final test period contains 182 trading days from 2019-04-01 to 2019-12-30. Table 1 compares the two regressors with the persistence baseline on exactly the same dates.'),
        ('table', [
            ['Model', 'MAE (₹)', 'RMSE (₹)', 'R²'],
            ['Persistence baseline', f"₹{base.MAE_INR:.2f}", f"₹{base.RMSE_INR:.2f}", f"{base.R2:.4f}"],
            ['Linear regression', f"₹{lr.MAE_INR:.2f}", f"₹{lr.RMSE_INR:.2f}", f"{lr.R2:.4f}"],
            ['Random forest', f"₹{rf.MAE_INR:.2f}", f"₹{rf.RMSE_INR:.2f}", f"{rf.R2:.4f}"],
        ]),
        ('p', 'Table 1. Next-trading-day Reliance closing-price regression results on the chronological test set.'),
        ('image',),
        ('caption', 'Fig. 1. Actual closing prices and model predictions over the held-out test dates (₹).'),
        ('p', f'The persistence baseline performed best: its MAE was ₹{base.MAE_INR:.2f}, compared with ₹{lr.MAE_INR:.2f} for linear regression and ₹{rf.MAE_INR:.2f} for random forest. Linear regression was the stronger of the two machine-learning models, but it still did not improve on carrying forward the latest close. The high R² values reflect the gradual movement of the price level in this period; they do not mean the model predicts profitable price changes.'),
        ('p', f'One close prediction was made on {easy.date}: actual ₹{easy.actual_close:.4f}, predicted ₹{easy.predicted_close:.4f}, absolute error ₹{easy.absolute_error:.4f}. A larger-error case was {hard.date}: actual ₹{hard.actual_close:.4f}, predicted ₹{hard.predicted_close:.4f}, absolute error ₹{hard.absolute_error:.4f}. The second case illustrates that a model can lag a sharp move. These examples are selected by smallest/largest absolute error from the linear-regression test predictions, not chosen to imply general performance.'),
        ('p', 'The main limitations are one company, one historical test window, and the use of price/volume history without news, fundamentals, market indices, or transaction costs. The provider does not identify its corporate-action adjustment procedure, which can affect long-range price comparability. Results are historical measurements, not current prices, and should not be used to make investment decisions.')
    ],
    '6. Conclusion': [
        f'For this Reliance sample, the persistence baseline gave the lowest test MAE (₹{base.MAE_INR:.2f}). Linear regression was more accurate than random forest among the two ML models, but neither beat the baseline. This suggests that the chosen historical indicators did not add enough information for this one-day-ahead task in the selected period. The experiment demonstrates chronological regression evaluation and the importance of a simple baseline. It does not establish future market predictability or support investment decisions.'
    ],
    '7. References': [
        '[1] M. Vijh, D. Chandola, V. A. Tikkiwal, and A. Kumar, “Stock Closing Price Prediction using Machine Learning Techniques,” Procedia Computer Science, vol. 167, pp. 599–606, 2020, doi: 10.1016/j.procs.2020.03.326.',
        '[2] Dr-Kitz28, “NSE-OHLCV-Data: RELIANCE daily OHLCV,” GitHub repository, commit 032b64127fa39b2910e18a7e2dc067faeb1bf5ef, accessed Nov. 3, 2026. Dataset licensed CC BY-NC 4.0; attribution and non-commercial-use terms apply. [Online]. Available: https://github.com/Dr-Kitz28/NSE-OHLCV-Data',
        '[3] Scikit-learn developers, “LinearRegression” and “RandomForestRegressor” documentation, accessed Nov. 3, 2026. [Online]. Available: https://scikit-learn.org/stable/modules/linear_model.html and https://scikit-learn.org/stable/modules/ensemble.html#forest',
        '[4] R. Kanishk, “Reliance Stock Closing Price Case Study,” Python implementation and saved test outputs, 2026. Source code and results accompany this report.'
    ],
    '8. Declaration': [
        'I confirm that I have reviewed the methods and results in this report. The results were generated by executing the included Python code on the cited public dataset. The base paper, dataset, and software documentation are acknowledged above.'
    ]
}

with ZipFile(TEMPLATE) as source:
    package = {item.filename: source.read(item.filename) for item in source.infolist()}
for _, uri in ET.iterparse(__import__('io').BytesIO(package['word/document.xml']), events=('start-ns',)):
    prefix, namespace = uri
    if prefix:
        ET.register_namespace(prefix, namespace)
ET.register_namespace('w', W); ET.register_namespace('r', R); ET.register_namespace('wp', WP)
ET.register_namespace('a', A); ET.register_namespace('pic', PIC)
doc = ET.fromstring(package['word/document.xml'])
doc.attrib.pop('{http://schemas.openxmlformats.org/markup-compatibility/2006}Ignorable', None)
body = doc.find('w:body', NS)

# Fill the fixed metadata cells without changing their styles or layout.
replacements = {
    '[Title]': 'Next-Day Reliance Industries Closing Price Prediction Using Machine Learning Regression',
    '[Authors, title, year]': 'Vijh et al., Stock Closing Price Prediction using Machine Learning Techniques, 2020',
    '[DD-MM-YYYY]': '03-11-2026',
    '[Roll No.]': 'AP24110010574',
    '[Name]': 'Ravipati Kanishk',
    'I confirm that this case study is my own work and that all results reported were obtained by me.':
        'I confirm that I have reviewed the methods and results in this report. The results were generated by executing the included Python code on the cited public dataset. The base paper, dataset, and software documentation are acknowledged above.',
}
for p in list(body.findall('.//w:p', NS)):
    text = ptext(p)
    if text.startswith('Instructions:') or text.startswith('What to write'):
        parent = next((x for x in body.iter() if p in list(x)), None)
        if parent is not None: parent.remove(p)
        continue
    if text in replacements:
        text_nodes = p.findall('.//w:t', NS)
        if text_nodes:
            text_nodes[0].text = replacements[text]
            for extra in text_nodes[1:]:
                extra.text = ''
    elif text == 'Roll No.:':
        node = p.find('.//w:t', NS)
        if node is not None: node.text = 'Roll No.: AP24110010574'
    elif text == 'Name:':
        node = p.find('.//w:t', NS)
        if node is not None: node.text = 'Name: Ravipati Kanishk'

rels = ET.fromstring(package['word/_rels/document.xml.rels'])
rid_nums = [int(e.get('Id')[3:]) for e in rels if (e.get('Id') or '').startswith('rId') and e.get('Id')[3:].isdigit()]
image_rel_id = f'rId{max(rid_nums, default=0)+1}'
ET.SubElement(rels, q(PKG_REL, 'Relationship'), {
    'Id':image_rel_id,
    'Type':'http://schemas.openxmlformats.org/officeDocument/2006/relationships/image',
    'Target':'media/stock_test_predictions.png'
})
ET.register_namespace('', PKG_REL)
package['word/_rels/document.xml.rels'] = ET.tostring(rels, encoding='utf-8', xml_declaration=True)
content_types = ET.fromstring(package['[Content_Types].xml'])
if not any(x.get('Extension') == 'png' for x in content_types.findall(q(CT,'Default'))):
    ET.SubElement(content_types, q(CT,'Default'), {'Extension':'png','ContentType':'image/png'})
ET.register_namespace('', CT)
package['[Content_Types].xml'] = ET.tostring(content_types, encoding='utf-8', xml_declaration=True)
package['word/media/stock_test_predictions.png'] = PLOT.read_bytes()

for heading, content in sections.items():
    paras = list(body.findall('w:p', NS))
    hidx = next(i for i, p in enumerate(paras) if ptext(p) == heading)
    if heading == '8. Declaration':
        continue
    if heading == '7. References':
        reference_idxs = [i for i in range(hidx + 1, len(paras)) if ptext(paras[i]).startswith(('[1] [Reference]', '[2] [Reference]', '[3] [Reference]'))]
        if len(reference_idxs) != 3:
            raise RuntimeError(f'Expected three reference slots, found {len(reference_idxs)}')
        prototype = paras[reference_idxs[0]]
        last_new = None
        for offset, text in enumerate(content):
            if offset < 3:
                target = paras[reference_idxs[offset]]
                replacement = make_p(text, target)
                body.insert(list(body).index(target), replacement)
                body.remove(target)
                last_new = replacement
            else:
                addition = make_p(text, prototype)
                body.insert(list(body).index(last_new) + 1, addition)
                last_new = addition
        continue
    placeholder_idx = next(i for i in range(hidx + 1, len(paras)) if ptext(paras[i]) == '[Write here]')
    placeholder = paras[placeholder_idx]
    if ptext(placeholder) != '[Write here]':
        raise RuntimeError(f'Missing expected placeholder following {heading}: {ptext(placeholder)!r}')
    for note in paras[hidx + 1:placeholder_idx]:
        body.remove(note)
    prototype = placeholder
    insert_at = list(body).index(placeholder)
    body.remove(placeholder)
    nodes = []
    for item in content:
        if isinstance(item, tuple) and item[0] == 'table':
            nodes.append(make_table(item[1]))
        elif isinstance(item, tuple) and item[0] == 'image':
            nodes.append(make_picture(image_rel_id))
        elif isinstance(item, tuple) and item[0] in ('p','caption'):
            nodes.append(make_p(item[1], prototype))
        else:
            nodes.append(make_p(item, prototype))
    for offset, node in enumerate(nodes):
        body.insert(insert_at + offset, node)

ET.register_namespace('w', W); ET.register_namespace('r', R); ET.register_namespace('wp', WP)
ET.register_namespace('a', A); ET.register_namespace('pic', PIC)
package['word/document.xml'] = ET.tostring(doc, encoding='utf-8', xml_declaration=True)
with ZipFile(OUTPUT, 'w', ZIP_DEFLATED) as archive:
    for name, data in package.items():
        archive.writestr(name, data)
print(OUTPUT)
