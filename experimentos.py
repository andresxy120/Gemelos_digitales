import argparse
import pandas as pd
from modelo import ot,aeropuerto

def main():
 p=argparse.ArgumentParser(); p.add_argument('--replicas',type=int,default=10); p.add_argument('--fecha',default='2026-06-03'); a=p.parse_args(); rows=[]
 for i in range(a.replicas):
  for estrategia in ['FIFO','Vencimiento','Traslado','Mamdani']:
   for escenario,extra,kits in [('base',0,200),('cuadrilla',1,200),('kits',0,210)]:
    r=ot(a.fecha,estrategia,extra,kits,7000+i); r.pop('plan'); rows.append(dict(replica=i,estrategia=estrategia,escenario=escenario,**r))
 df=pd.DataFrame(rows); df.to_csv('experimentos_ot.csv',index=False); print(df.groupby(['estrategia','escenario'])[['terminadas','abiertas','incumplidas']].mean())
if __name__=='__main__': main()
