"""CPU-only analysis for the unchanged v4 latency benchmark."""
from pathlib import Path
import json,math,os,sys,time,hashlib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import nbformat

CONDS=['L25','L50','L75','L100','NORERANK','NOHEDGE','F1','F2','F3H','F3NH','F4','F5','F6']
ROUTES=['reranked','fused_baseline','fused_fallback','lex','sem','error']
COLORS=['#CC79A7','#009E73','#009E73','#0072B2','#E69F00','#D55E00']
def percentile(vals,q=.99):
    a=sorted(float(v) for v in vals if v is not None and np.isfinite(v))
    return a[max(0,math.ceil(round(q*len(a),9))-1)] if a else np.nan
def dump(path,value): Path(path).write_text(json.dumps(value,indent=2,ensure_ascii=False,default=str)+'\n')

class Run:
    def __init__(self,root):
        self.root=Path(root).resolve(); self.data=self.root/'results_trec_covid_carga_fija_v4'
        self.fig=self.root/'figs'; self.fig.mkdir(exist_ok=True)
        self.meta=json.loads((self.data/'run_meta.json').read_text())
        self.cal=json.loads((self.data/'calibration.json').read_text())
        self.summary=pd.read_csv(self.data/'summary.csv')
        self.cache={}; self.notes={}
        assert len(self.summary)==39 and not self.summary.duplicated(['rep','condition']).any()
        assert set(self.summary.rep)=={1,2,3} and set(self.summary.condition)==set(CONDS)
    def records(self,rep,condition,post=True):
        key=(rep,condition)
        if key not in self.cache:
            p=self.data/f'requests_trec-covid_rep{rep}_{condition}.jsonl'
            self.cache[key]=[json.loads(line) for line in p.open()]
        a=self.cache[key]
        return [r for r in a if r['t_sched']>=30] if post else a
    def valid(self,rep,condition): return [r for r in self.records(rep,condition) if r['n_results']==3]
    def row(self,rep,condition): return self.summary[(self.summary.rep==rep)&(self.summary.condition==condition)].iloc[0]
    def aggregate(self):
        rows=[]
        for c in CONDS:
            g=self.summary[self.summary.condition==c]
            row=dict(condition=c,repetitions=len(g),nominal_qps=float(g.offered_qps.iloc[0]),requests=int(g.n_sent.sum()))
            for col in ['p50_ms','p95_ms','p99_ms','continuity_pct','pct_dup']:
                row[col+'_median']=float(g[col].median()); row[col+'_min']=float(g[col].min()); row[col+'_max']=float(g[col].max())
            rows.append(row)
        return pd.DataFrame(rows)
    def fitness(self):
        rows=[]
        for rep in [1,2,3]:
            load=self.summary[(self.summary.rep==rep)&self.summary.condition.isin(CONDS[:4])]
            f=self.summary[(self.summary.rep==rep)&self.summary.condition.isin(['F1','F2'])]
            d=self.summary[(self.summary.rep==rep)&self.summary.condition.isin(CONDS[:4]+['F3H'])]
            p99=float(load.p99_ms.max()); cont=float(f.continuity_pct.min()); dup=float(d.pct_dup.max())
            rows.append(dict(rep=rep,max_load_p99_ms=p99,fitness_i=p99<=2500,
                min_F1F2_continuity_pct=cont,fitness_iii=cont>=99,max_dup_pct=dup,fitness_iv=dup<=10))
        return pd.DataFrame(rows)
    def hedging(self):
        rows=[]
        for rep in [1,2,3]:
            h,n=self.row(rep,'F3H'),self.row(rep,'F3NH')
            a,b=self.records(rep,'F3H',False),self.records(rep,'F3NH',False)
            pairs=[(r['qid'],r['t_sched']) for r in a]==[(r['qid'],r['t_sched']) for r in b]
            assert pairs
            assigned=[bool(np.random.default_rng([42,rep,i]).random(4)[2]<.05) for i in range(len(a))]
            assert all(not x['delay_injected'] or d for x,d in zip(a,assigned))
            assert all(not x['delay_injected'] or d for x,d in zip(b,assigned))
            mismatches=sum(x['delay_injected']!=y['delay_injected'] for x,y in zip(a,b))
            rows.append(dict(rep=rep,p99_H_ms=float(h.p99_ms),p99_NH_ms=float(n.p99_ms),
                p99_reduction_ms=float(n.p99_ms-h.p99_ms),dup_H_pct=float(h.pct_dup),paired_inputs_equal=pairs,planned_delays_count=sum(assigned),observed_delay_mismatches=mismatches,observed_delay_mismatches_postwarm=sum(x['delay_injected']!=y['delay_injected'] for x,y in zip(a,b) if x['t_sched']>=30),observed_delays_equal=mismatches==0))
        return pd.DataFrame(rows)
    def exposure(self):
        rows=[]
        for rep in [1,2,3]:
            a,b=self.records(rep,'F3H',False),self.records(rep,'F3NH',False)
            assert [(r['qid'],r['t_sched']) for r in a]==[(r['qid'],r['t_sched']) for r in b]
            for i,(x,y) in enumerate(zip(a,b)):
                rows.append(dict(rep=rep,request_index=i,qid=x['qid'],t_sched=x['t_sched'],post_warmup=x['t_sched']>=30,
                    assigned_delay=bool(np.random.default_rng([42,rep,i]).random(4)[2]<.05),
                    invoked_H=x['rerank_invoked'],invoked_NH=y['rerank_invoked'],
                    observed_delay_H=x['delay_injected'],observed_delay_NH=y['delay_injected'],
                    route_H=x['route'],route_NH=y['route']))
        return pd.DataFrame(rows)
    def verify(self):
        checks=[]
        for rep in [1,2,3]:
            for c in CONDS:
                rows=self.records(rep,c); valid=self.valid(rep,c); expected=self.row(rep,c)
                assert len(rows)==expected.n_sent
                for q,col in [(.5,'p50_ms'),(.95,'p95_ms'),(.99,'p99_ms')]:
                    actual=percentile([r['latency_ms'] for r in valid],q)
                    assert (pd.isna(actual) and pd.isna(expected[col])) or np.isclose(actual,expected[col],atol=.0011,rtol=0)
                actual=100*sum(r['n_results']==3 and r['latency_ms']<=2500 for r in rows)/len(rows)
                assert np.isclose(actual,expected.continuity_pct,atol=.0011,rtol=0)
                originals=sum(r['rerank_invoked'] for r in rows)
                dup=100*sum(r['hedge_sent'] for r in rows)/originals if originals else 0
                assert np.isclose(dup,expected.pct_dup,atol=.0011,rtol=0)
                checks.append(dict(rep=rep,condition=c,n_requests=len(rows),metrics_match_raw=True))
        self.hedging()
        assert self.meta['node']=='ds001' and 'RTX A6000' in self.meta['nvidia_smi']
        assert self.meta['args']['subset']==0 and self.meta['args']['fake'] is False
        assert self.meta['script_sha256']=='bb027763a577074373d5c1909467fbac67f8b5484d37696b29e1f697f02f22b7'
        assert self.meta['alpha_json']['alpha']==.85
        corpus_count=sum(1 for _ in (self.root/'data/trec-covid/corpus.jsonl').open())
        qrels=pd.read_csv(self.root/'data/trec-covid/qrels/test.tsv',sep='\t',dtype={'query-id':str})
        assert corpus_count==171332 and qrels['query-id'].nunique()==50
        result=dict(passed=True,complete_conditions=39,paired_comparisons=3,checks=checks,
            source_sha256=self.meta['script_sha256'],dataset='trec-covid',node=self.meta['node'],
            corpus_documents=corpus_count,test_queries=50,protocol=self.cal['protocol'],capacity_validated=False,trec_capacity_qps=None)
        dump(self.root/'final_verification.json',result)
        return result
    def _save(self,fig,name,note):
        fig.savefig(self.fig/name,dpi=200,bbox_inches='tight'); plt.close(fig); self.notes[name]=note
    def figures(self):
        plt.rcParams.update({'font.size':10,'figure.constrained_layout.use':True})
        ramp=pd.DataFrame(self.cal['ramp_log_rounded']); C=self.cal['C_qps']
        assert self.cal['capacity_validated'] is False and self.cal['trec_capacity_qps'] is None
        fig,ax=plt.subplots(1,2,figsize=(10,4))
        ax[0].plot(ramp.offered_qps,ramp.reranked_pct_rounded,'o-',label='Ruta completa (log redondeado)')
        ax[0].axhline(99,color='black',ls='--',label='Criterio 99 %')
        ax[0].set(xlabel='QPS nominales',ylabel='Solicitudes reranked (%)',title='Calibración v4: no fija C'); ax[0].legend(fontsize=8)
        ax[1].plot(ramp.offered_qps,ramp.p99_first_half_ms_rounded,'o-',label='Primera mitad')
        ax[1].plot(ramp.offered_qps,ramp.p99_second_half_ms_rounded,'s-',label='Segunda mitad')
        ax[1].set(xlabel='QPS nominales',ylabel='p99 de respuestas válidas (ms)',title='Valores redondeados del log'); ax[1].legend(fontsize=8)
        fig.suptitle('TREC-COVID · calibración fallida, preservada por separado')
        self._save(fig,'K1_rampa_trec-covid.png','El primer escalón falla: no hay C validada en esta grilla. La rampa solo se conserva redondeada en stdout por el código original. El ensayo complementario usa 8 QPS como referencia externa de carga, no como C de TREC.')
        calib=[json.loads(line) for line in (self.root/'results_trec_covid_completo_v4/requests_trec-covid_calib_1qps.jsonl').open()]
        labels=['lex','sem','fusion','rerank','extremo a extremo']; vals=[]
        for stage in labels:
            a=[r['latency_ms'] if stage==labels[-1] else r['stage_ms'].get(stage) for r in calib]
            vals.append([v for v in a if v is not None and v>0])
        fig,ax=plt.subplots(figsize=(9,4)); ax.boxplot(vals,tick_labels=labels,showfliers=False)
        for i,limit in enumerate([50,1200,50,1200,2500],1): ax.hlines(limit,i-.3,i+.3,color='black',linestyle='--')
        ax.plot([],[],'k--',label='Plazo de etapa o SLO'); ax.legend()
        ax.set(yscale='log',ylabel='Tiempo (ms, escala log)',title='Calibración a 1 QPS por etapa')
        self._save(fig,'K2_etapas_trec-covid.png',f'Umbral de hedge = p95 de rerank en calibración: {self.cal["hedge_threshold_ms"]:.3f} ms. Las líneas son plazos de respaldo. Se muestran tiempos positivos registrados; en un timeout se mide la espera hasta vencer el plazo, no el tiempo posterior del hilo residual.')
        fig,ax=plt.subplots(figsize=(8,4))
        for c in CONDS[:4]:
            a=np.sort([r['latency_ms'] for rep in [1,2,3] for r in self.valid(rep,c)])
            ax.plot(a,np.arange(1,len(a)+1)/len(a),label=c)
        ax.axvline(2500,color='black',ls='--',label='SLO 2500 ms'); ax.legend()
        ax.set(xscale='log',xlabel='Latencia desde t programado (ms)',ylabel='Fracción acumulada',title='Carga y distribución de latencia válida')
        self._save(fig,'K3_ecdf_carga_trec-covid.png','Las ECDF reúnen respuestas válidas de las tres repeticiones después del calentamiento. La continuidad, cuyo denominador incluye errores, se muestra aparte.')
        agg=self.aggregate().set_index('condition')
        fig,ax=plt.subplots(figsize=(9,4))
        for col,name in [('p50_ms','p50'),('p95_ms','p95'),('p99_ms','p99')]:
            a=agg.loc[CONDS[:4]]; y=a[col+'_median'].to_numpy()
            err=np.vstack([y-a[col+'_min'].to_numpy(),a[col+'_max'].to_numpy()-y])
            ax.errorbar([25,50,75,100],y,yerr=err,marker='o',capsize=3,label=name)
        for c,marker in [('NORERANK','s'),('NOHEDGE','^')]: ax.scatter([100],[agg.loc[c,'p99_ms_median']],marker=marker,s=80,label=f'{c} p99')
        ax.axhline(2500,color='black',ls='--',label='SLO'); ax.legend(fontsize=8,ncol=3)
        ax.set(xlabel=f'Porcentaje de referencia externa {C:g} QPS (%)',ylabel='Latencia (ms)',title='Mediana y rango de tres repeticiones')
        self._save(fig,'K4_percentiles_carga_trec-covid.png',f'En L100, p99 mediano = {agg.loc["L100","p99_ms_median"]:.1f} ms. Las barras son rangos mínimo–máximo, no intervalos de confianza.')
        fig,axes=plt.subplots(1,2,figsize=(10,4))
        for ax,c in zip(axes,['L100','F2']):
            a=self.records(1,c,False); ax.scatter([r['t_sched'] for r in a],[r['latency_ms'] for r in a],s=8,label=c)
            ax.axvspan(0,30,color='gray',alpha=.2,label='Calentamiento excluido')
            ax.axhline(2500,color='black',ls='--',label='SLO'); ax.set(xlabel='Tiempo programado (s)',ylabel='Latencia (ms)',title=c); ax.legend(fontsize=7)
        self._save(fig,'K5_serie_tiempo_trec-covid.png','Se conserva el calentamiento en esta visualización y se sombrea, aunque se excluye de los estadísticos. F2 fuerza vencimiento del plazo del reranker.')
        routes=np.array([[np.mean([self.row(rep,c)['pct_route_'+r] for rep in [1,2,3]]) for r in ROUTES] for c in CONDS])
        fig,ax=plt.subplots(figsize=(9,7)); im=ax.imshow(routes,cmap='Blues',vmin=0,vmax=100,aspect='auto')
        for i in range(13):
            for j in range(6): ax.text(j,i,f'{routes[i,j]:.1f}',ha='center',va='center',fontsize=8,color='white' if routes[i,j]>55 else 'black')
        ax.set(xticks=range(6),xticklabels=ROUTES,yticks=range(13),yticklabels=CONDS,title='Rutas observadas por condición (%)')
        plt.setp(ax.get_xticklabels(),rotation=25,ha='right'); fig.colorbar(im,ax=ax,label='Solicitudes (%)')
        self._save(fig,'K6_matriz_rutas_trec-covid.png','La matriz distingue omitir el reranker a propósito de invocarlo y usar respaldo. Un SLO cumplido no implica ejecución de la ruta completa en todas las solicitudes.')
        fig,ax=plt.subplots(figsize=(9,4)); cs=['NORERANK','F1','F2','F4','F5','F6']
        for j,rep in enumerate([1,2,3]): ax.bar(np.arange(len(cs))+(j-1)*.24,[self.row(rep,c).continuity_pct for c in cs],.24,label=f'Rep {rep}')
        ax.axhline(99,color='black',ls='--',label='Umbral 99 %'); ax.legend(ncol=4,fontsize=8)
        ax.set(xticks=range(len(cs)),xticklabels=cs,ylabel='Tres resultados en ≤2500 ms (%)',ylim=(0,110),title='Continuidad bajo fallas')
        self._save(fig,'K7_continuidad_trec-covid.png','F1 y F2 son las pruebas de continuidad ante error o lentitud del reranker. En F6 fallan las dos rutas y se espera error controlado, no continuidad.')
        fig,axes=plt.subplots(1,3,figsize=(12,4))
        for c,color in [('F3H','#CC79A7'),('F3NH','#0072B2')]:
            for ax,stage in zip(axes[:2],['rerank','e2e']):
                a=sorted(r['latency_ms'] if stage=='e2e' else r['stage_ms']['rerank'] for rep in [1,2,3] for r in self.valid(rep,c) if stage=='e2e' or r['rerank_invoked'])
                ax.plot(a,np.arange(1,len(a)+1)/len(a),color=color,label=c)
                ax.axvline(percentile(a),color=color,ls='--',alpha=.7)
                ax.set(xlabel='Tiempo (ms)',ylabel='Fracción acumulada',title=stage); ax.legend()
        hd=self.hedging(); axes[2].bar([1,2,3],hd.dup_H_pct,color='#CC79A7',label='F3H')
        axes[2].axhline(10,color='black',ls='--',label='Límite 10 %'); axes[2].set(xticks=[1,2,3],xlabel='Repetición',ylabel='Copias / originales (%)',title='Costo del hedge'); axes[2].legend(fontsize=8)
        self._save(fig,'K8_hedging_trec-covid.png',f'La reducción NH−H del p99 extremo a extremo por repetición es {hd.p99_reduction_ms.round(1).tolist()} ms. La CDF de etapa incluye solo invocaciones; la CDF extremo a extremo incluye toda respuesta válida. IDs y llegadas coinciden; las demoras efectivas difieren en {hd.observed_delay_mismatches_postwarm.tolist()} solicitudes poscalentamiento por repetición por rutas previas. No es una estimación causal aislada del hedge.')
        fitness=self.fitness(); matrix=np.array([fitness.fitness_i.astype(float),[.5]*3,fitness.fitness_iii.astype(float),fitness.fitness_iv.astype(float)])
        from matplotlib.colors import ListedColormap
        fig,ax=plt.subplots(figsize=(8,4)); ax.imshow(matrix,cmap=ListedColormap(['#D55E00','#CCCCCC','#009E73']),vmin=0,vmax=1,aspect='auto')
        for j,r in fitness.iterrows():
            for i,text in enumerate([f'{r.max_load_p99_ms:.1f} ms','Ver Trabajo 1',f'{r.min_F1F2_continuity_pct:.2f} %',f'{r.max_dup_pct:.3f} %']): ax.text(j,i,text,ha='center',va='center',fontsize=10)
        ax.set(xticks=range(3),xticklabels=['Rep 1','Rep 2','Rep 3'],yticks=range(4),yticklabels=['(i) p99 ≤2500 ms','(ii) relevancia','(iii) F1/F2 ≥99 %','(iv) copias ≤10 %'],title='Fitness por repetición')
        ax.legend(handles=[Patch(color='#009E73',label='Cumple'),Patch(color='#D55E00',label='No cumple'),Patch(color='#CCCCCC',label='Otra corrida')],loc='upper center',bbox_to_anchor=(.5,-.15),ncol=3)
        self._save(fig,'K9_fitness_trec-covid.png','Las fitness temporales se calculan por repetición. La relevancia se evalúa en el Trabajo 1: no se convierte una prueba de continuidad en una prueba de mejora de P@3.')
        dump(self.root/'figure_notes.json',self.notes)
        assert len(self.notes)==9
        return self.notes
