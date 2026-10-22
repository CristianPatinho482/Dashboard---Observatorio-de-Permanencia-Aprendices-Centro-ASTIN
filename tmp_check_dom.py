import re
from pathlib import Path
h=Path('tmp_dom.html').read_text(encoding='utf-8',errors='replace')
for pat in ['id="kpis"','id="critical-cards"','id="tb-programas"','id="tb-fichas"']:
    i=h.find(pat)
    print('\n---',pat,'---')
    print(h[i:i+900] if i>=0 else 'NOT FOUND')
print('\nNaN count',h.count('NaN'),'undefined count',h.count('undefined'))
