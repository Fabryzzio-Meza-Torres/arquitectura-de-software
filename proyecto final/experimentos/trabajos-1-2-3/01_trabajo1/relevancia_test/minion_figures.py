"""Publication figures and examples, generated only on Khipu."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from minion_test import ROUTES, COLORS, load_dataset, dump

def figures(ctx):
    out=ctx['out']; folder=out/'figs'; notes={}
    metrics=pd.read_csv(out/'metrics.csv'); ci=pd.read_csv(out/'metric_ci.csv')
    boot=pd.read_csv(out/'bootstrap.csv'); judged=pd.read_csv(out/'judged.csv')
    condensed=pd.read_csv(out/'condensed.csv')
    per=pd.read_csv(out/'per_query_metrics.csv',dtype={'query_id':str})
    plt.rcParams.update({'font.size':11,'axes.spines.top':False,'axes.spines.right':False,
                         'figure.constrained_layout.use':True})

    def save(fig,name,note):
        fig.savefig(folder/name,dpi=200,bbox_inches='tight')
        plt.close(fig); notes[name]=note

    curve=pd.read_csv(out/'alpha_curve.csv')
    fig,ax=plt.subplots(figsize=(8,4.5))
    ax.plot(curve.alpha,curve.precision_at_3,'o-',color=COLORS['lex'],label='Precision@3')
    ax.plot(curve.alpha,curve.ndcg_at_3,'s-',color=COLORS['sem'],label='nDCG@3')
    ax.axvline(.85,color='black',ls='--',label='α fijado = 0,85')
    ax.set(xlabel='α (peso semántico)',ylabel='Métrica (0–1)',title='Resultado de desarrollo (FiQA-dev)')
    ax.legend(); ax.grid(alpha=.2)
    save(fig,'R3_alpha_fiqa_dev.png',
        'La curva proviene del archivo validado de desarrollo: no se recalculó ni se usó test para ajustar α.\n'
        'El valor fijo 0,85 se aplica sin cambios a FiQA-test y TREC-COVID.')
    examples=['# R9 — Ejemplos de reranking\n\nSe selecciona una consulta con la mayor mejora y una con la mayor caída de P@3 por dataset.\n']
    paper=[]
    for ds in ['fiqa','trec-covid']:
        label='FiQA-test' if ds=='fiqa' else 'TREC-COVID-test'
        m=metrics[metrics.dataset==ds].set_index('route')
        b=boot[boot.dataset==ds].iloc[0]
        p=per[per.dataset==ds]; qids=sorted(p.query_id.unique())
        c=pd.read_parquet(out/f'cands_{ds}_test.parquet')
        fp=p[p.route=='fused'].set_index('query_id').loc[qids]
        rp=p[p.route=='reranked'].set_index('query_id').loc[qids]
        delta=rp.precision_at_3-fp.precision_at_3
        verdict='positivo' if b.ci_95_low>0 else ('negativo' if b.ci_95_high<0 else 'compatible con cero')

        fig,ax=plt.subplots(figsize=(9,4.8)); x=np.arange(3); width=.19
        names=['precision_at_3','ndcg_at_3','mrr_at_10']
        for j,route in enumerate(ROUTES):
            vals=m.loc[route,names].to_numpy(dtype=float)
            sub=ci[(ci.dataset==ds)&(ci.route==route)].set_index('metric').loc[names]
            err=np.maximum(0,np.vstack([vals-sub.ci_95_low.to_numpy(),sub.ci_95_high.to_numpy()-vals]))
            ax.bar(x+(j-1.5)*width,vals,width,yerr=err,capsize=3,color=COLORS[route],label=route)
        ax.set(xticks=x,xticklabels=['P@3','nDCG@3','MRR@10'],ylabel='Métrica (0–1)',ylim=(0,1.05),title=f'{label}: métricas e IC bootstrap 95 %')
        ax.legend(ncol=4); ax.grid(axis='y',alpha=.2)
        save(fig,f'R1_metricas_{ds}.png',
            f"P@3 pasa de {m.loc['fused','precision_at_3']:.4f} (fusión) a {m.loc['reranked','precision_at_3']:.4f} (reranking).\n"
            'Las barras muestran IC marginales; la comparación pareada de ΔP@3 está en R2. MRR de lex y sem es complementario.')

        samples=pd.read_csv(out/f'bootstrap_samples_{ds}.csv').delta_precision_at_3
        fig,ax=plt.subplots(figsize=(8,4.5))
        ax.hist(samples,bins=45,color=COLORS['fused'],alpha=.85,label='10.000 remuestreos pareados')
        ax.axvline(0,color='black',ls='--',label='Sin diferencia')
        ax.axvline(b.ci_95_low,color='#D55E00',label='IC 95 % (percentiles)')
        ax.axvline(b.ci_95_high,color='#D55E00')
        ax.set(xlabel='ΔP@3 = reranked − fused (0–1)',ylabel='Remuestreos (conteo)',title=f'{label}: incertidumbre de la mejora')
        ax.legend()
        save(fig,f'R2_bootstrap_{ds}.png',
            f'ΔP@3 = {b.delta_precision_at_3:+.4f}; IC 95 % [{b.ci_95_low:+.4f}, {b.ci_95_high:+.4f}].\n'
            f'El intervalo es {verdict}; el remuestreo conserva el emparejamiento por consulta.')

        a=np.rint(fp.precision_at_3.to_numpy()*3).astype(int)
        z=np.rint(rp.precision_at_3.to_numpy()*3).astype(int)
        matrix=np.zeros((4,4),int); np.add.at(matrix,(a,z),1)
        fig,ax=plt.subplots(figsize=(6.4,5)); im=ax.imshow(matrix,cmap='Blues',origin='upper')
        for i in range(4):
            for j in range(4): ax.text(j,i,str(matrix[i,j]),ha='center',va='center',color='white' if matrix[i,j]>matrix.max()*.5 else 'black')
        ax.set(xticks=range(4),yticks=range(4),xticklabels=['0','1/3','2/3','1'],yticklabels=['0','1/3','2/3','1'],
               xlabel='P@3 reranked',ylabel='P@3 fused',title=f'{label}: transición de P@3 por consulta')
        fig.colorbar(im,ax=ax,label='Consultas (conteo)')
        save(fig,f'R4_matriz_transicion_{ds}.png',
            f'{int((z>a).sum())} consultas mejoran, {int((z==a).sum())} empatan y {int((z<a).sum())} empeoran.\n'
            'Las celdas a la derecha y por encima de la diagonal representan mejoras; la diagonal representa empates.')

        counts=np.array([(delta>0).sum(),(delta==0).sum(),(delta<0).sum()]); pct=counts/len(qids)*100
        fig,ax=plt.subplots(figsize=(8,3)); left=0
        for value,color,name in zip(pct,[COLORS['fused'],'#999999','#D55E00'],['Mejora','Empata','Empeora']):
            ax.barh([0],[value],left=left,color=color,label=name)
            if value>4: ax.text(left+value/2,0,f'{value:.1f} %',ha='center',va='center')
            left+=value
        ax.set(xlabel='Consultas (%)',xlim=(0,100),yticks=[],title=f'{label}: gana, empata o pierde el reranker')
        ax.legend(ncol=3,loc='upper center',bbox_to_anchor=(.5,-.3))
        save(fig,f'R5_gana_empata_pierde_{ds}.png',
            f'El reranker mejora {pct[0]:.1f} %, empata {pct[1]:.1f} % y empeora {pct[2]:.1f} % de las consultas.\n'
            'El cambio promedio debe interpretarse junto con estas diferencias entre consultas.')

        s=load_dataset(ctx,ds)
        rels={q:dict(zip(g.doc_id,g.relevance)) for q,g in s['qrels'].groupby('query_id')}
        positions=np.zeros((20,20),int); origins=np.zeros(3,float); relevant=np.zeros(3,float)
        for q,g in c.groupby('query_id',sort=True):
            f=g.sort_values(['fused_score','doc_id'],ascending=[False,True],kind='stable')
            r=f.sort_values('ce_score',ascending=False,kind='stable')
            fr={d:i for i,d in enumerate(f.doc_id)}; rr={d:i for i,d in enumerate(r.doc_id)}
            for d in fr:
                if rels[q].get(d,0)>=1: positions[fr[d],rr[d]]+=1
            for _,row in g.iterrows():
                origin=2 if row.lex_rank>0 and row.sem_rank>0 else (0 if row.lex_rank>0 else 1)
                origins[origin]+=1; relevant[origin]+=rels[q].get(row.doc_id,0)>=1
        fig,ax=plt.subplots(figsize=(7.3,6)); im=ax.imshow(positions,cmap='magma',origin='upper')
        ax.set(xticks=[0,4,9,14,19],yticks=[0,4,9,14,19],xticklabels=[1,5,10,15,20],yticklabels=[1,5,10,15,20],
               xlabel='Posición después del reranking',ylabel='Posición en la lista fusionada',title=f'{label}: movimiento de documentos relevantes')
        ax.plot([-.5,19.5],[-.5,19.5],'--',color='white',lw=1,label='Posición sin cambio'); ax.legend()
        fig.colorbar(im,ax=ax,label='Documentos relevantes (conteo)')
        rescued=int(positions[3:,:3].sum()); lost=int(positions[:3,3:].sum())
        save(fig,f'R6_matriz_posiciones_{ds}.png',
            f'{rescued} relevantes entran al top 3 desde posiciones inferiores; {lost} salen del top 3.\n'
            'Cada documento es el mismo antes y después: esta figura aísla el efecto de reordenar candidatos.')

        fig,ax=plt.subplots(figsize=(7,4.7)); bottom=np.zeros(2)
        for j,(name,color) in enumerate(zip(['Solo BM25','Solo denso','Ambos'],[COLORS['lex'],COLORS['sem'],COLORS['fused']])):
            vals=np.array([origins[j],relevant[j]])/len(qids)
            ax.bar([0,1],vals,bottom=bottom,color=color,label=name); bottom+=vals
        ax.set(xticks=[0,1],xticklabels=['Candidatos','Relevantes'],ylabel='Documentos por consulta (promedio)',title=f'{label}: origen y complementariedad')
        ax.legend(); ax.grid(axis='y',alpha=.2)
        save(fig,f'R7_origen_candidatos_{ds}.png',
            f'La unión contiene {origins.sum()/len(qids):.2f} candidatos por consulta y {relevant.sum()/len(qids):.2f} relevantes juzgados.\n'
            f'Los aportes relevantes exclusivos de BM25 y denso son {relevant[0]/len(qids):.2f} y {relevant[1]/len(qids):.2f} por consulta.')

        j=judged[judged.dataset==ds].set_index('route').loc[ROUTES]
        fig,axes=plt.subplots(1,2,figsize=(10,4.4))
        axes[0].bar(ROUTES,j.judged_at_10_percent,color=[COLORS[r] for r in ROUTES])
        axes[0].set(ylabel='Documentos juzgados en top 10 (%)',ylim=(0,105),title='Cobertura de juicios')
        axes[0].legend(handles=[Patch(color=COLORS[r],label=r) for r in ROUTES],fontsize=8,
                       loc='upper center',bbox_to_anchor=(.5,-.14),ncol=4)
        changes=[0. if abs(v)<1e-12 else v for v in [b.delta_precision_at_3,b.condensed_delta_precision_at_3]]
        axes[1].bar(['Original','Condensada'],changes,color=[COLORS['fused'],COLORS['reranked']])
        axes[1].axhline(0,color='black',ls='--',label='Sin diferencia')
        axes[1].set(ylabel='ΔP@3 = reranked − fused',title='Sensibilidad a no juzgados'); axes[1].legend()
        bound=max(.02,max(abs(v) for v in changes)*1.25)
        axes[1].set_ylim(-bound,bound)
        fig.suptitle(f'{label}: juicios faltantes y listas condensadas')
        save(fig,f'R8_judged_{ds}.png',
            f"Judged@10: fusión {j.loc['fused','judged_at_10_percent']:.1f} %, reranker {j.loc['reranked','judged_at_10_percent']:.1f} %. Los grados 0 cuentan como juzgados.\n"
            f"ΔP@3 condensada = {b.condensed_delta_precision_at_3:+.4f}; {'se mantiene' if b.delta_sign_preserved else 'cambia'} el signo respecto de la evaluación original."
            + (' FiQA solo tiene juicios positivos: el empate de P@3 condensada es estructural al compartir candidatos.' if ds=='fiqa' else ''))

        docmap={d['_id']:d for d in s['docs']}
        def clean(text): return str(text).replace('|','\\|').replace('\n',' ').replace('\r',' ')
        for kind,q in [('mejora',delta.sort_values(ascending=False,kind='stable').index[0]),('caída',delta.sort_values(kind='stable').index[0])]:
            actual='mejora' if delta[q]>0 else ('caída' if delta[q]<0 else 'empate')
            examples.append(f"\n## {label} — caso de {kind}: consulta {q}\n\n{clean(s['queries'][q])}\n\nΔP@3 = {delta[q]:+.4f}; resultado observado: **{actual}**.\n")
            if actual!=kind: examples.append(f'No se observó un caso de {kind}; se muestra el extremo disponible.\n')
            examples.append('\n| Lista | Posición | ID | Grado | Texto del documento (extracto) |\n|---|---:|---|---:|---|')
            g=c[c.query_id==q].sort_values(['fused_score','doc_id'],ascending=[False,True],kind='stable')
            for route,ranked in [('fused',g),('reranked',g.sort_values('ce_score',ascending=False,kind='stable'))]:
                for rank,d in enumerate(ranked.doc_id[:3],1):
                    grade=rels[q].get(d,'no juzgado'); text=docmap[d]['title']+' '+docmap[d]['text']
                    examples.append(f'| {route} | {rank} | {d} | {grade} | {clean(text[:350])}… |')
        row=dict(dataset=ds,alpha=.85,recall_at_20_fused=m.loc['fused','recall_at_20'],**b.drop('dataset').to_dict())
        for route in ROUTES:
            for metric in ['precision_at_3','ndcg_at_3','mrr_at_10']: row[f'{metric}_{route}']=m.loc[route,metric]
            row[f'judged_at_10_{route}']=j.loc[route,'judged_at_10']
        paper.append(row)
    (out/'R9_ejemplos.md').write_text('\n'.join(examples))
    pd.DataFrame(paper).to_csv(out/'paper_table.csv',index=False)
    dump(out/'figure_notes.json',notes)
    assert len(notes)==15
    return notes
