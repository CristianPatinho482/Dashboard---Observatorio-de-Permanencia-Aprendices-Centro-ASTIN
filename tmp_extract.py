import re
from pathlib import Path
html=Path('dashboard/index.html').read_text(encoding='utf-8')
scripts=re.findall(r'<script>(.*?)</script>', html, re.S)
print('scripts:',len(scripts))
# last script is app code
Path('tmp_app.js').write_text(scripts[-1],encoding='utf-8')
# chart.js is first
Path('tmp_chart.js').write_text(scripts[0],encoding='utf-8')
print('app chars',len(scripts[-1]),'chart chars',len(scripts[0]))
