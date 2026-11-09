"""Render the three clocks from a saved calibration report."""
import json
from pathlib import Path
import sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def main():
    path=Path(sys.argv[1])
    report=json.loads(path.read_text())
    rows=report['near_alignments']
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,
                         'axes.spines.top':False,'axes.spines.right':False})
    fig,(a,b,c)=plt.subplots(1,3,figsize=(14,5.5))
    blue,orange='#226ca6','#ce7114'
    for value in range(6,37,6): a.axvline(value,color='#dbe2e8',lw=1,zorder=0)
    for offset,step,color in ((1,2,blue),(0,3,orange)):
        points=list(range(step,37,step))
        a.scatter(points,[offset]*len(points),c=color,s=34,zorder=4)
        a.hlines(offset,0,37,color='#abb7bf',lw=.8)
    a.set(yticks=[0,1],yticklabels=['3n','2n'],ylim=(-.6,1.6),xlim=(0,37),
          xlabel='Output value — not runtime stage',title='Regular output-value coincidences')
    a.set_xticks(range(0,37,6))
    a.text(18,-.43,'Shared outputs: 6, 12, 18, 24, …',ha='center',fontsize=9)
    for row in rows:
        idx,sign=row['index'],row['norm']
        color=blue if sign>0 else orange
        b.vlines(idx,0,sign,color=color,lw=1.5)
        filled=row['variants'][0]['bundle']['fully_recorded']
        b.scatter(idx,sign,s=65,facecolors=color if filled else 'white',edgecolors=color,zorder=4,lw=1.8)
    b.axhline(0,color='#bdc6cc',lw=.8)
    b.set(xlim=(.5,8.5),ylim=(-1.5,1.5),xticks=range(1,9),yticks=[-1,0,1],
          xlabel='Step of (n, m) → (n + 2m, n + m)',ylabel='Signed discrepancy  n² − 2m²',
          title='A two-step pattern in the discrepancy')
    stages=[row['integer_certificate_stage'] for row in rows]
    c.semilogy(range(1,9),stages,color=blue,lw=1.6)
    for idx,stage in enumerate(stages,1):
        c.scatter(idx,stage,s=48,facecolors=blue if stage<=160 else 'white',edgecolors=blue,zorder=4,lw=1.6)
        c.annotate(f'{stage:,}',(idx,stage),xytext=(0,9),textcoords='offset points',ha='center',fontsize=8.5)
    c.axhline(160,color='#8f9ca5',ls='--',lw=1)
    c.text(4.1,85,'Saved graph limit U160',fontsize=8.5,color='#596774')
    c.set(xlim=(.5,8.5),ylim=(1,2000000),xticks=range(1,9),xlabel='Recurrence step',
          ylabel='Certificate checkpoint U (log scale)',title='The same events have expanding stage gaps')
    for ax in (b,c):
        ax.grid(axis='y',color='#dbe2e8',lw=.7,alpha=.7)
        ax.set_axisbelow(True)
    for ax in (a,b,c): ax.title.set_fontsize(11)
    fig.suptitle('A repeated relation can have more than one rhythm',x=.06,y=.975,ha='left',fontsize=17,fontweight='bold')
    fig.text(.06,.905,'Exact output alignment, recurrence-step alternation and graph-stage timing are distinct observations.',fontsize=10.5,color='#50606b')
    fig.text(.06,.085,'Filled markers: the full discrepancy certificate is recorded in U160. Open markers: exact algebra with predicted graph checkpoints.',fontsize=9.5)
    fig.text(.06,.032,'Classical Pell calibration. The circle-area record supplies no established π-specific period.',fontsize=9.5,color='#50606b')
    fig.subplots_adjust(left=.065,right=.98,top=.8,bottom=.24,wspace=.4)
    for ext in ('png','pdf','svg'): fig.savefig(path.with_name('branch_rhythm_clocks.'+ext),dpi=175)
    print(path.with_name('branch_rhythm_clocks.png'))


if __name__=='__main__': main()
