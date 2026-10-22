import json
d=json.load(open('outputs/04_modelo_predictivo.json',encoding='utf-8'))
for c in d['coeficientes'][:14]:
    print(c['variable'], c['coeficiente'], c['or'], '[',c['or_ic95_inf'],'-',c['or_ic95_sup'],']')
print('--- prio ---')
for k,v in d['distribucion_probabilidad']['conteo_prioridad'].items(): print(k,v)
