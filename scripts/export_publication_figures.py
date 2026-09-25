"""Redraw seven current publication figures from verified numeric inputs."""
from pathlib import Path
import hashlib
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from evidence import ROOT, verify_inputs


def main():
    verify_inputs()
    OUT = ROOT / 'supplementary/figures'
    OUT.mkdir(parents=True, exist_ok=True)
    d = json.loads((ROOT / 'data/figure_inputs.json').read_text())
    r=pd.read_csv(ROOT/'validation/reference/refinement/full_generator_refinement.csv')
    plt.rcParams.update({'font.size':11,'axes.labelsize':11,'xtick.labelsize':10,'ytick.labelsize':10,'legend.fontsize':10,'pdf.fonttype':42,'svg.fonttype':'none'})
    
    def save(fig,name):
     fig.tight_layout()
     fig.savefig(OUT/(name+'.pdf'))
     fig.savefig(OUT/(name+'.svg'))
     fig.savefig(OUT/(name+'.png'),dpi=180)
     plt.close(fig)
    
    fig,ax=plt.subplots(figsize=(6.4,4.7))
    t=np.array(d['EXP_TIME_S'])
    ax.fill_between(t,d['HOLDOUT_PI_LOW'],d['HOLDOUT_PI_HIGH'],alpha=.17,label='Calibration-only 95% interval')
    ax.scatter(t,d['HOLDOUT_Y'],s=14,marker='o',label='Published 533 kV/cm trace',zorder=5)
    labels={'Single exponential':'Single exponential (2)', 'Stretched exponential':'Stretched exponential (4)',
    'Distributed relaxation':'Distributed relaxation (6)','Biexponential (six parameters)':'Biexponential (6; retrospective)'}
    for (m,p),ls in zip(d['models'].items(),[':', '--','-', '-.']):
     ax.plot(t,p,ls=ls,lw=1.7,label=labels[m])
    ax.set_xscale('log');ax.set_xlabel('Time (s)');ax.set_ylabel('Normalized polarization')
    ax.set_ylim(-.08,1.16);ax.legend(loc='upper center',bbox_to_anchor=(.5,1.37),ncol=2,frameon=False)
    save(fig,'proton_holdout')
    
    fig,ax=plt.subplots(figsize=(6.4,4.3))
    for case,mark,ls,label in [('symmetric','o','-','Symmetric background'),('ramp','s','--','Gradient background')]:
     g=r[r.case==case];ax.loglog(g.N,g.relative_L2_error,marker=mark,ls=ls,label=label)
    ns=np.array([64,1024]);err=r[(r.case=='symmetric') & (r.N==64)].relative_L2_error.iloc[0]
    ax.loglog(ns,err*(64/ns)**2*.55,ls=':',label=r'$N^{-2}$ guide')
    err=r[(r.case=='ramp') & (r.N==64)].relative_L2_error.iloc[0]
    ax.loglog(ns,err*64/ns*1.5,ls='-.',label=r'$N^{-1}$ guide')
    ax.set_xlabel('Number of coarse cells, N');ax.set_ylabel('Relative spatial error');ax.legend(frameon=False)
    save(fig,'proton_full_convergence')
    
    fig,ax=plt.subplots(figsize=(6.4,4.1))
    for case,mark,ls,label in [('symmetric','o','-','Symmetric background'),('ramp','s','--','Gradient background')]:
     g=r[r.case==case];ax.semilogx(g.N,g.gap_s_1,marker=mark,ls=ls,label=label)
    bound=json.loads((ROOT/'validation/reference/refinement/summary.json').read_text())['uniform_bound_s_1']
    ax.axhline(bound,ls=':',label='Common mesh-independent lower bound')
    ax.set_xlabel('Number of coarse cells, N');ax.set_ylabel(r'Frozen-generator spectral gap (s$^{-1}$)')
    ax.set_ylim(0,2.4e-4);ax.ticklabel_format(axis='y',style='sci',scilimits=(0,0));ax.legend(frameon=False,loc='upper center',bbox_to_anchor=(.5,1.32))
    save(fig,'proton_full_gaps')
    
    fig,ax=plt.subplots(figsize=(6.4,3.7))
    for name in ['Distributed relaxation','Biexponential (six parameters)']:
     ax.semilogx(t,np.asarray(d['models'][name])-d['HOLDOUT_Y'],marker='.',ms=4,label=labels[name])
    ax.axhline(0,ls=':');ax.set_xlabel('Time (s)');ax.set_ylabel('Prediction minus observation');ax.legend(frameon=False,loc='upper center',bbox_to_anchor=(.5,1.26))
    save(fig,'supp_polarization_residuals')
    
    fig,ax=plt.subplots(figsize=(6.4,3.9))
    for ori,ls,m in [('001','-','o'),('111','--','s')]:
     x=np.array(d['strain_pct']);y=np.array(d['K_R_'+ori]);ax.scatter(x,y,marker=m,label=f'[{ori}] curvature inputs')
     xx=np.linspace(-3,3,120);ax.plot(xx,np.exp(np.polyval(np.polyfit(x,np.log(y),1),xx)),ls=ls,label=f'[{ori}] log-linear fit')
    ax.set_xlabel('Biaxial strain (%)');ax.set_ylabel(r'Breathing stiffness (eV $\AA^{-2}$)');ax.legend(frameon=False,ncol=2,loc='upper center',bbox_to_anchor=(.5,1.29))
    save(fig,'supp_structural_curvature')
    
    fig,ax=plt.subplots(figsize=(6.4,3.9))
    sh=d['shift'];x=np.arange(5)
    ax.plot(x,[v['Δ ROC-AUC'] for v in sh],'o-',label='Recoverability')
    ax.plot(x,[v['baseline ROC-AUC'] for v in sh],'s--',label='Comparator selected on training set')
    ax.axhline(.5,ls=':');ax.set_xticks(x,['Random','Concentration','Temperature','Field','Protocol'])
    ax.set_ylabel('Receiver operating characteristic area');ax.set_ylim(.45,1.);ax.legend(frameon=False,loc='upper center',bbox_to_anchor=(.5,1.25))
    save(fig,'supp_recoverability_transfer')
    
    fig,ax=plt.subplots(figsize=(6.4,4.0))
    for key,label,ls in [('TWIN_TEST_SNR','Right-electrode continuation','-'),('TWIN_SYMMETRIC_SNR','Symmetric-control continuation','--')]:
     v=np.sort(d[key]);ax.step(v,np.arange(1,len(v)+1)/len(v),where='post',label=label,ls=ls)
    ax.axvline(3,ls=':',label='Effect-size reference: 3');ax.set_xscale('log');ax.set_xlabel('Twin separation / published residual-scale proxy')
    ax.set_ylabel('Empirical cumulative fraction');ax.set_ylim(0,1.02);ax.legend(frameon=False,loc='upper center',bbox_to_anchor=(.5,1.33))
    save(fig,'supp_hidden_twins')
    files = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(OUT.iterdir()) if p.suffix in {'.pdf', '.svg', '.png'}}
    record = {'generator': 'scripts/export_publication_figures.py', 'scope': 'Recorded-evidence redraw; no refitting or synthetic protocol rerun.', 'files': files}
    (OUT / 'manifest.json').write_text(json.dumps(record, indent=2) + '\n')
    print(f'Exported seven figures (PDF/SVG/PNG) to {OUT}')


if __name__ == '__main__':
    main()
