from flask import Flask, render_template, request, jsonify
from modelo import ot, aeropuerto, ajustes, datos
import numpy as np
from scipy import stats
app = Flask(__name__)
@app.get('/')
def home(): return render_template('index.html')
@app.post('/simular')
def simular():
    try:
        d = request.get_json(); tipo = d.pop('tipo')
        if tipo not in ('ot','aeropuerto'): raise ValueError('Tipo inválido')
        for k in ('agentes','tasa','media','horizonte'):
            if k in d and d[k]<=0: raise ValueError(f'{k} debe ser positivo')
        return jsonify((ot if tipo=='ot' else aeropuerto)(**d))
    except Exception as e:
        app.logger.exception('Simulación'); return jsonify(error=str(e)),400
@app.get('/modelos')
def modelos():
    try:
        out={}; _,d,*_=datos(); d=d[(d.anio_programacion==2025)&(d.ejecutada==1)]
        for col,rows in ajustes().items():
            x=d[col].dropna().to_numpy(); x=x[x>0]; h,b=np.histogram(x,bins=30,density=True); z=(b[1:]+b[:-1])/2
            f=stats.__dict__[rows[0]['familia']]; out[col]={'ajustes':rows,'n':len(x),'x':z.tolist(),'hist':h.tolist(),'densidad':f.pdf(z,*rows[0]['parametros']).tolist()}
        return jsonify(out)
    except Exception as e:
        app.logger.exception('Modelos'); return jsonify(error=str(e)),500
if __name__=='__main__': app.run(host='0.0.0.0',port=8000)
