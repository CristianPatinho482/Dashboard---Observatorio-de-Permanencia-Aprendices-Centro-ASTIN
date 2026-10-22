import csv, numpy as np
from pathlib import Path
from sklearn.model_selection import StratifiedGroupKFold, cross_val_predict
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, brier_score_loss
D=Path('data/processed')
def rd(n): return list(csv.DictReader(open(D/n,encoding='utf-8-sig')))
f=rd('FactMatricula.csv'); fi={x['FichaID']:x for x in rd('DimFicha.csv')}; ap={x['AprendizID']:x for x in rd('DimAprendiz.csv')}; pr={x['ProgramaID']:x for x in rd('DimPrograma.csv')}
import math
def fl(x,d=0.0):
    try: return float(x)
    except: return d
rows=[]
for r in f:
    a=ap[r['AprendizID']]; h=fi[r['FichaID']]
    rows.append(dict(y=int(r['EsPerdida']), ficha=r['FichaID'], prog=r['ProgramaID'], jornada='DIURNA' if r['JornadaID']=='J01' else 'NOCTURNA', tipo=a['TipoDocumento'], contacto=int(r['ContactoCompleto']), cel=int(r['TieneCelular']), email=int(r['EmailValido']), tam=fl(h['TotalMatriculas']), gen=int(h['GeneracionID'].split('-')[1]), cont=fl(h['TasaContactoIncompleto']), multi=int(a['TieneMultiplesFichas']), dominio=a['EmailDominio']))
for name, feats in [('full',['prog','jornada','tipo','contacto','tam','gen','cont','multi']),('individual',['tipo','contacto','multi']),('struct',['prog','jornada','tam','gen','cont']),('estructura_sin_contacto',['prog','jornada','tam','gen'])]:
    X=[[r[k] for k in feats] for r in rows]; y=np.array([r['y'] for r in rows]); groups=np.array([r['ficha'] for r in rows])
    cat=[i for i,k in enumerate(feats) if k in ('prog','jornada','tipo')]; num=[i for i,k in enumerate(feats) if k not in ('prog','jornada','tipo')]
    ct=ColumnTransformer([('cat',OneHotEncoder(handle_unknown='ignore',drop='first'),cat),('num',StandardScaler(),num)])
    pipe=Pipeline([('ct',ct),('lr',LogisticRegression(max_iter=5000,C=1.0))])
    cv=StratifiedGroupKFold(n_splits=5,shuffle=True,random_state=42)
    p=cross_val_predict(pipe,X,y,groups=groups,cv=cv,method='predict_proba',n_jobs=-1)[:,1]
    print(name,'AUC',round(roc_auc_score(y,p),3),'Brier',round(brier_score_loss(y,p),4),'min/max',round(p.min(),3),round(p.max(),3))
