from flask import Flask,render_template,request,jsonify
from modelo import ot,aeropuerto,ajustes
app=Flask(__name__)
@app.route('/')
def home(): return render_template('index.html')
@app.post('/simular')
def simular():
 d=request.get_json(); tipo=d.pop('tipo'); return jsonify((ot if tipo=='ot' else aeropuerto)(**d))
@app.get('/modelos')
def modelos(): return jsonify(ajustes())
if __name__=='__main__': app.run(host='0.0.0.0',port=8000)
