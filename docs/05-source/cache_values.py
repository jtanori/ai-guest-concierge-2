"""Injects cached formula results into financial-model.xlsx so that programmatic
readers (pandas/openpyxl), Google Sheets and preview panes see values, while Excel
still keeps the live formulas and recalculates on open."""
import re, shutil, zipfile, os
import formulas

SRC = 'financial-model.xlsx'
TMP = '_fm_tmp.xlsx'

# 1. compute the solution
print("calculating ...")
sol = formulas.ExcelModel().loads(SRC).finish().calculate()

# 2. build SHEET!CELL -> value map
vals = {}
for k, v in sol.items():
    m = re.match(r"^'\[financial-model\.xlsx\]([^']+)'!([A-Z]+\d+)$", k)
    if not m:
        continue
    sheet, cell = m.group(1), m.group(2)
    try:
        val = v.value[0, 0]
    except Exception:
        val = v
    if isinstance(val, float) and val != val:  # NaN -> 0
        val = 0
    vals[(sheet.upper(), cell)] = val
print(f"  {len(vals)} computed cells")

# 3. map sheet name -> worksheet xml path
with zipfile.ZipFile(SRC) as z:
    wbxml = z.read('xl/workbook.xml').decode('utf-8')
    rels = z.read('xl/_rels/workbook.xml.rels').decode('utf-8')
targets = {}
for tag in re.findall(r'<Relationship\b[^>]*/?>', rels):
    rid = re.search(r'Id="([^"]+)"', tag)
    tgt = re.search(r'Target="([^"]+)"', tag)
    if rid and tgt:
        targets[rid.group(1)] = tgt.group(1)
sheetmap = {}
for tag in re.findall(r'<sheet\b[^>]*/?>', wbxml):
    name = re.search(r'name="([^"]+)"', tag)
    rid = re.search(r'r:id="(rId\d+)"', tag)
    if name and rid:
        t = targets[rid.group(1)].lstrip('/')
        if not t.startswith('xl/'):
            t = 'xl/' + t
        sheetmap[name.group(1).upper()] = t
print(f"  sheets mapped: {len(sheetmap)}")

CELL_RE = re.compile(r'<c r="([A-Z]+\d+)"([^>]*?)>(<f>.*?</f>)(?:<v>.*?</v>)?</c>', re.S)

def patch(xml, sheetname):
    hits = 0
    def repl(m):
        nonlocal hits
        cell, attrs, f = m.group(1), m.group(2), m.group(3)
        if (sheetname, cell) not in vals:
            return m.group(0)
        v = vals[(sheetname, cell)]
        attrs = re.sub(r'\s*t="[^"]*"', '', attrs)
        if isinstance(v, (bool,)) or type(v).__name__ == 'bool_':
            return f'<c r="{cell}"{attrs} t="b">{f}<v>{1 if v else 0}</v></c>'
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            hits += 1
            num = float(v)
            if num.is_integer() and abs(num) < 1e15:
                out = str(int(num))
            else:
                out = repr(num)
            return f'<c r="{cell}"{attrs}>{f}<v>{out}</v></c>'
        s = str(v).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        hits += 1
        return f'<c r="{cell}"{attrs} t="str">{f}<v>{s}</v></c>'
    out = CELL_RE.sub(repl, xml)
    return out, hits

total = 0
with zipfile.ZipFile(SRC) as zin, zipfile.ZipFile(TMP, 'w', zipfile.ZIP_DEFLATED) as zout:
    for item in zin.infolist():
        data = zin.read(item.filename)
        for sheetname, path in sheetmap.items():
            if item.filename == path:
                xml = data.decode('utf-8')
                xml, hits = patch(xml, sheetname)
                total += hits
                data = xml.encode('utf-8')
        zout.writestr(item, data)
print(f"  cached values written: {total}")

shutil.move(TMP, SRC)
print("done ->", SRC)
