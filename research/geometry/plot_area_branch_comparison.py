"""Plot a saved comparison report; matplotlib is a rendering dependency only."""
import argparse
from fractions import Fraction
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("report",type=Path)
    args=parser.parse_args()
    data=json.loads(args.report.read_text())
    plt.rcParams.update({"font.family":"DejaVu Sans","font.size":10,
                         "axes.spines.top":False,"axes.spines.right":False,
                         "axes.titleweight":"bold"})
    fig,(a,b)=plt.subplots(1,2,figsize=(12.6,5.7))
    colors={"polygon_exact":"#2167a6","polygon_rounded":"#d87913","grid":"#24876d"}
    labels={"polygon_exact":"Exact rational polygons","polygon_rounded":"Certified rounded polygons","grid":"Square-grid cover"}
    for method in colors:
        rows=[r for r in data["records"] if r["shape"]=="disk" and r["scale"]==1 and r["method"]==method]
        width=[float(Fraction(r["width"])) for r in rows]
        a.loglog([r["n"] for r in rows],width,"o-",color=colors[method],label=labels[method],lw=1.8,ms=5)
        visible=[(r,w) for r,w in zip(rows,width) if int(r["certificate"]["stage"])<=10**12]
        b.loglog([int(r["certificate"]["stage"]) for r,w in visible],[w for r,w in visible],"o-",color=colors[method],lw=1.8,ms=5)
    a.axvspan(12,80,color="#eaf0f5",zorder=-5)
    a.text(25,3.3,"Reserved refinements",fontsize=9,ha="center",color="#566878")
    a.set(title="Refinement tightens all three bounds",xlabel="Subdivision N",ylabel="Certified area-interval width")
    a.set_xlim(.8,80)
    a.set_xticks([1,2,4,8,16,32,64])
    a.xaxis.set_major_formatter(ScalarFormatter())
    a.legend(loc="lower left",fontsize=8.6,framealpha=.97)
    b.set(title="Witness costs depend on the encoding",xlabel="Specified witness-bundle checkpoint U",ylabel="Certified area-interval width")
    b.set_xlim(2,10**12)
    b.axvline(160,color="#889399",lw=1,ls="--")
    b.text(230,2.8,"U160 saved graph limit\nLarger U: predicted certificates",fontsize=8.5,color="#59646d")
    b.text(2e8,.13,"Exact N16, N32, N64\nare beyond this x range",fontsize=8.5,color=colors["polygon_exact"])
    for ax in (a,b):
        ax.set_ylim(.0003,5)
        ax.grid(which="major",color="#d6dce0",alpha=.55,lw=.7)
        ax.set_axisbelow(True)
    fig.suptitle("One area boundary, different inspection costs",x=.065,y=.98,ha="left",fontsize=17,fontweight="bold")
    fig.text(.065,.922,"Unit disk under external Euclidean area assumptions. Canonical input representation; no pi supplied.",fontsize=10,color="#52606b")
    fig.text(.065,.075,"N64 checkpoint costs:  exact polygons 4.87 × 10¹⁴²   |   rounded polygons 1.34 × 10¹¹   |   grid 13,104",fontsize=10)
    fig.text(.065,.025,"Checkpoint = earliest joint availability of this witness set; not an optimal cost or a chronological execution time.",fontsize=9,color="#52606b")
    fig.subplots_adjust(top=.82,bottom=.22,left=.075,right=.98,wspace=.26)
    for ext in ("png","pdf","svg"):
        fig.savefig(args.report.with_name("area_inspection_comparison."+ext),dpi=180)
    print(args.report.with_name("area_inspection_comparison.png"))


if __name__=="__main__":
    main()
