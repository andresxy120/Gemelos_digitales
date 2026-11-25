from pathlib import Path
import pandas as pd
import numpy as np
from scipy import stats
from functools import lru_cache
D=Path(__file__).parent/'data'
def read(n): return pd.read_csv(next(D.glob(f'{n:02d}*')))
@lru_cache(None)
def datos():
 p=read(1); h=read(2); d=p.merge(h,on='id_ot'); return p,d,read(5),read(6),read(7)
@lru_cache(None)
def ajustes():
 _,d,*_=datos(); d=d[(d.anio_programacion==2025)&(d.ejecutada==1)]; out={}
 for col in ['tiempo_servicio_real_min','tiempo_desplazamiento_min']:
  x=d[col].dropna().to_numpy(); x=x[x>0]; rows=[]
  for name in ['lognorm','gamma','invgauss','expon']:
   f=getattr(stats,name); par=f.fit(x,floc=0); ll=f.logpdf(x,*par).sum(); k=len(par)-1; rows.append(dict(familia=name,parametros=list(par),aic=float(2*k-2*ll),bic=float(k*np.log(len(x))-2*ll),p5=float(f.ppf(.05,*par)),p95=float(f.ppf(.95,*par))))
  out[col]=sorted(rows,key=lambda a:a['aic'])
 return out

def mamdani(holgura,prioridad):
 u=np.clip(1-holgura/5,0,1); p=np.clip(prioridad/100,0,1); x=np.linspace(0,100,101); low=np.maximum(0,1-x/50); mid=np.maximum(0,1-abs(x-50)/50); high=np.maximum(0,(x-50)/50); y=np.maximum.reduce([np.minimum(min(1-u,1-p),low),np.minimum(max(min(u,1-p),min(1-u,p)),mid),np.minimum(min(u,p),high)]); return float((x*y).sum()/max(y.sum(),1e-9))

@lru_cache(None)
def caso(fecha):
 p,d,c,cal,e=datos(); t=pd.Timestamp(fecha); end=t+pd.Timedelta(days=1); p=p[(pd.to_datetime(p.fecha_programacion)==t)&(pd.to_datetime(p.fecha_hora_recibo)<t+pd.Timedelta(hours=6,minutes=30))].copy(); e=e[pd.to_datetime(e.fecha_evento)<t+pd.Timedelta(hours=6,minutes=30)].sort_values('fecha_evento'); first=datos()[4].sort_values('fecha_evento').drop_duplicates('id_ot').set_index('id_ot').fecha_limite_anterior; last=e.drop_duplicates('id_ot',keep='last').set_index('id_ot'); p['limite']=p.id_ot.map(first).fillna(p.fecha_limite_ans_vigente); p['limite']=p.id_ot.map(last.fecha_limite_nueva).fillna(p.limite); p['suspendida']=p.id_ot.map(last.tipo_evento).eq('SUSPENSION'); return p.to_dict('records'),c.to_dict('records'),bool(cal.loc[cal.fecha==fecha,'es_dia_habil'].sum())

def ot(fecha='2026-06-03',estrategia='FIFO',extra=0,kits=200,seed=42,horizonte=540):
 jobs,crews,habil=caso(fecha); rng=np.random.default_rng(seed); a=ajustes(); durations={}
 for j in jobs:
  durations[j['id_ot']]=[max(1,round(getattr(stats,a[col][0]['familia']).rvs(*a[col][0]['parametros'],random_state=rng))) for col in a]
 crews=[dict(c) for c in crews]; crews+= [dict(crews[i%len(crews)],id_cuadrilla=f'EXTRA-{i+1}') for i in range(extra)]; free={c['id_cuadrilla']:0 for c in crews}; rows=[]; start=pd.Timestamp(fecha)+pd.Timedelta(hours=6,minutes=30); pending=[j for j in jobs if j['apta_programacion']==1 and not j['suspendida']]; blocked=len(jobs)-len(pending)
 def score(j,c):
  slack=(pd.Timestamp(j['limite'])-start).total_seconds()/86400; travel=(35 if j['tipo_direccion']=='URBANO' else 65)+(0 if j['subzona']==c['subzona_base'] else 25)
  return {'FIFO':j['fecha_hora_recibo'],'Vencimiento':j['limite'],'Traslado':travel,'Mamdani':-mamdani(slack,j['prioridad_proxy_0_100']),'Optimizador':(max(0,slack)*1440+travel+j['tiempo_target_min'])}[estrategia]
 if habil:
  for c in sorted(crews,key=lambda c:c['id_cuadrilla']):
   cid=c['id_cuadrilla']; cap=min(horizonte,c['capacidad_min_dia']);
   while kits>0:
    eligible=[j for j in pending if j['especialidad_requerida']==c['especialidad'] and free[cid]+j['tiempo_target_min']+38<=cap]
    if not eligible: break
    j=min(eligible,key=lambda j:score(j,c)); service,travel=durations[j['id_ot']]; begin=free[cid]; finish=begin+3+travel+service
    if finish>cap: break
    pending.remove(j); kits-=1; free[cid]=finish; rows.append(dict(id=j['id_ot'],cuadrilla=cid,inicio=begin,material=begin+3,traslado=begin+3+travel,fin=finish,tarde=bool(start+pd.Timedelta(minutes=finish)>pd.Timestamp(j['limite']))))
 done={r['id'] for r in rows}; overdue=sum(start+pd.Timedelta(minutes=horizonte)>pd.Timestamp(j['limite']) for j in jobs if j['id_ot'] not in done); late=sum(r['tarde'] for r in rows); return dict(total=len(jobs),terminadas=len(rows),abiertas=len(jobs)-len(rows),bloqueadas=blocked,vencidas=overdue,tarde=late,incumplidas=overdue+late,kits=kits,plan=rows)

def aeropuerto(agentes=3,tasa=30,media=5,seed=42,horizonte=120):
 r=np.random.default_rng(seed); free=np.zeros(agentes); rows=[]; t=0
 while True:
  t+=r.exponential(60/tasa)
  if t>horizonte: break
  duration=r.gamma(2,media/2); k=int(free.argmin()); begin=max(t,free[k]); finish=begin+duration; free[k]=finish; rows.append(dict(llegada=t,inicio=begin,fin=finish,agente=k+1,riesgo=bool(finish>t+30)))
 started=[x for x in rows if x['inicio']<=horizonte]; return dict(total=len(rows),terminadas=int(sum(x['fin']<=horizonte for x in rows)),fila=int(sum(x['inicio']>horizonte for x in rows)),espera=float(np.mean([x['inicio']-x['llegada'] for x in started])) if started else 0,riesgo=sum(x['riesgo'] for x in rows),plan=rows)
