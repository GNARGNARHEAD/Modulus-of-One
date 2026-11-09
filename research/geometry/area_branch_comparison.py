"""Exact area-inspection certificates and a read-only U160 graph audit.

See AREA_INSPECTION_BRANCH_20261001.pre.md. Larger stages are predictions for
specified integer certificates, not observed graph events. Geometry, selection,
ordering and counting remain external interpretations. No pi is an input.
"""
from __future__ import annotations

import argparse
from contextlib import closing
from fractions import Fraction as F
import json
from math import gcd, isqrt, log10
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from moo.research_utils import connect_readonly, file_sha256, require_strict_alignment
from moo.shell_branch_search import WitnessReader

LEVELS = (1, 2, 4, 8, 16, 32, 64)
DEFAULT_CORPUS = ROOT / "research/geometry/results/2026-10-01-square-area-inspection-v1/current_u160.sqlite"


class Registry:
    def __init__(self):
        self.edges = []
        self.lookup = {}

    def add(self, a, op, b):
        assert isinstance(a, int) and isinstance(b, int) and min(a, b) >= 1
        key = (a, op, b)
        if key not in self.lookup:
            value = {"+": lambda: F(a+b), "-": lambda: F(a-b),
                     "*": lambda: F(a*b), "/": lambda: F(a,b)}[op]()
            idx = len(self.edges)
            self.lookup[key] = idx
            self.edges.append(dict(id=idx, a=str(a), op=op, b=str(b),
                                   result=str(value), predicted_stage=str(max(a,b))))
        return self.lookup[key]


class Trace:
    def __init__(self, registry):
        self.registry = registry
        self.refs = set()
        self.zero_specializations = 0
        self.op(1, "+", 1)
        self.op(2, "*", 2)

    def op(self, a, op, b):
        idx = self.registry.add(a, op, b)
        self.refs.add(idx)
        result = F(self.registry.edges[idx]["result"])
        return result.numerator if result.denominator == 1 else result

    def add(self, a, b):
        assert min(a,b) >= 0
        if a == 0 or b == 0:
            self.zero_specializations += 1
            return a+b
        return self.op(a, "+", b)

    def mul(self, a, b):
        assert min(a,b) >= 0
        if a == 0 or b == 0:
            self.zero_specializations += 1
            self.op(1, "-", 1)
            return 0
        return self.op(a, "*", b)

    def sub(self, a, b):
        assert a >= b >= 0
        if b == 0:
            self.zero_specializations += 1
            return a
        return self.op(a, "-", b)

    def reduced(self, a, b):
        assert a >= 0 and b > 0
        if a == 0:
            self.op(1, "-", 1)
            return F(0)
        g = gcd(a,b)  # External selector; divisions certify the selected factors.
        if g != 1:
            aa, bb = self.op(a, "/", g), self.op(b, "/", g)
            assert self.mul(aa,g) == a and self.mul(bb,g) == b
            a,b = aa,bb
        self.op(a, "/", b)
        return F(a,b)

    def radd(self, x, y):
        if x == 0 or y == 0:
            return x+y
        a,b,c,d = x.numerator,x.denominator,y.numerator,y.denominator
        g = gcd(b,d)
        left = self.op(d, "/", g) if g != 1 else d
        right = self.op(b, "/", g) if g != 1 else b
        assert self.mul(left,g) == d and self.mul(right,g) == b
        return self.reduced(self.add(self.mul(a,left), self.mul(c,right)), self.mul(b,left))

    def summary(self):
        stage = max(int(self.registry.edges[i]["predicted_stage"]) for i in self.refs)
        return dict(stage=str(stage), log10_stage=log10(stage), unique_edges=len(self.refs),
                    edge_refs=sorted(self.refs), zero_specializations=self.zero_specializations)


def source_shell(trace, n, k, scale):
    a,b = scale*n,scale*k
    aa,bb = trace.mul(a,a),trace.mul(b,b)
    x,y,r = trace.sub(aa,bb),trace.mul(2,trace.mul(a,b)),trace.add(aa,bb)
    xx,yy,rr = trace.mul(x,x),trace.mul(y,y),trace.mul(r,r)
    assert trace.add(xx,yy) == rr
    point = [trace.reduced(x,r), trace.reduced(y,r)]
    squares = [trace.reduced(xx,rr), trace.reduced(yy,rr)]
    return dict(parameter=str(F(k,n)), raw=[a,b], shell=[x,y,r],
                point=list(map(str,point)), squares=list(map(str,squares)))


def rounded_units(trace, numerator, denominator, D, upward):
    scaled = trace.mul(numerator,D)
    units = (scaled+denominator-1)//denominator if upward else scaled//denominator
    product = trace.mul(units,denominator)
    gap = trace.sub(product,scaled) if upward else trace.sub(scaled,product)
    assert trace.sub(denominator,gap) > 0
    return units


def polygons(registry, n, scale, rounded=False):
    trace = Trace(registry)
    sources = [source_shell(trace,n,k,scale) for k in range(n+1)]
    D = trace.mul(trace.mul(n,n),n) if rounded else None
    lo,hi = F(0),F(0)
    lower_units=upper_units=0
    terms=[]
    raw_n=scale*n
    for k in range(n):
        wnum=trace.mul(scale,raw_n)
        wden=trace.add(trace.mul(raw_n,raw_n),trace.mul(scale*k,scale*(k+1)))
        w=trace.reduced(wnum,wden)
        p,q=w.numerator,w.denominator
        lower_num=trace.mul(4,trace.mul(p,q))
        lower_den=trace.add(trace.mul(p,p),trace.mul(q,q))
        upper_num=trace.mul(4,p)
        if rounded:
            lu=rounded_units(trace,lower_num,lower_den,D,False)
            uu=rounded_units(trace,upper_num,q,D,True)
            lower_units=trace.add(lower_units,lu)
            upper_units=trace.add(upper_units,uu)
            terms.append(dict(k=k,w=str(w),lower_units=lu,upper_units=uu))
        else:
            lower=trace.reduced(lower_num,lower_den)
            upper=trace.reduced(upper_num,q)
            lo,hi=trace.radd(lo,lower),trace.radd(hi,upper)
            terms.append(dict(k=k,w=str(w),lower=str(lower),upper=str(upper)))
    if rounded:
        lo,hi=trace.reduced(lower_units,D),trace.reduced(upper_units,D)
    return lo,hi,trace,dict(sources=sources,terms=terms,rounding_denominator=D)


def grid(registry,n,scale,shape):
    trace=Trace(registry)
    radius=scale*n
    rr=trace.mul(radius,radius)
    ss=trace.mul(scale,scale)
    trace.reduced(ss,rr)  # The rational-square cell area, (scale/radius)^2.
    counts=[]
    lower_count=upper_count=0
    for i in range(n+1):
        xi=scale*i
        xx=trace.mul(xi,xi)
        trace.reduced(xx,rr)
        if shape == "disk":
            j=isqrt(n*n-i*i)
            yj=scale*j
            yy=trace.mul(yj,yj)
            near=trace.add(xx,yy)
            inside_gap=trace.sub(rr,near)
            next_y=trace.add(yj,scale)
            far=trace.add(xx,trace.mul(next_y,next_y))
            outside_gap=trace.sub(far,rr)
            assert outside_gap > 0
        elif shape == "diamond":
            j=n-i
            near=trace.add(xi,scale*j)
            inside_gap=trace.sub(radius,near)
            far=trace.add(xi,trace.add(scale*j,scale))
            outside_gap=trace.sub(far,radius)
            assert inside_gap == 0 and outside_gap > 0
        elif shape == "square":
            j=n
            inside_gap=trace.sub(radius,scale*j)
            outside_gap=trace.sub(trace.add(scale*j,scale),radius)
        else:
            raise ValueError(shape)
        if i>=1:
            lower_count=trace.add(lower_count,j)
        if i<n:
            upper_count=trace.add(upper_count,min(n,trace.add(j,1)))
        counts.append(dict(i=i,last_inside=j,inside_gap=str(inside_gap),outside_gap=str(outside_gap)))
    lo=trace.reduced(trace.mul(4,trace.mul(lower_count,ss)),rr)
    hi=trace.reduced(trace.mul(4,trace.mul(upper_count,ss)),rr)
    return lo,hi,trace,dict(rows=counts,lower_count=lower_count,upper_count=upper_count)


def polygon_control(registry,scale,shape):
    trace=Trace(registry)
    trace.reduced(scale,scale)
    trace.reduced(trace.mul(scale,scale),trace.mul(scale,scale))
    area=F(2 if shape=="diamond" else 4)
    trace.reduced(area.numerator,1)
    return area,area,trace,dict(exact_boundary_polygon=True)


def roots():
    return sorted({F(p,q) for q in range(1,33) for p in range(1,2*q+1) if gcd(p,q)==1})


def classification(value,lo,hi):
    if value < lo:
        return "below"
    if value > hi:
        return "above"
    if lo == hi == value:
        return "exact"
    return "unresolved"


def comparison_certificate(registry,root,lo,hi):
    trace=Trace(registry)
    p,q=root.numerator,root.denominator
    pp,qq=trace.mul(p,p),trace.mul(q,q)
    trace.reduced(p,q)
    trace.reduced(pp,qq)
    tests=[]
    for label,bound in (("lower",lo),("upper",hi)):
        left=trace.mul(pp,bound.denominator)
        right=trace.mul(bound.numerator,qq)
        gap=trace.sub(max(left,right),min(left,right))
        tests.append(dict(bound=label,left=str(left),right=str(right),gap=str(gap),
                          relation="equal" if left==right else "less" if left<right else "greater"))
    return dict(root=str(root),value=str(root*root),classification=classification(root*root,lo,hi),
                tests=tests,certificate=trace.summary())


def shoelace(vertices):
    return abs(sum((x*v-y*u for (x,y),(u,v) in zip(vertices,vertices[1:]+vertices[:1])),F(0)))/2


def explicit_polygon_areas(n):
    quarter=[]
    for k in range(n):
        t=F(k,n)
        quarter.append(((1-t*t)/(1+t*t),2*t/(1+t*t)))
    vertices=[]
    for turn in range(4):
        for x,y in quarter:
            for _ in range(turn):
                x,y=-y,x
            vertices.append((x,y))
    tangents=[]
    for (x,y),(u,v) in zip(vertices,vertices[1:]+vertices[:1]):
        determinant=x*v-y*u
        point=((v-y)/determinant,(x-u)/determinant)
        assert x*point[0]+y*point[1] == u*point[0]+v*point[1] == 1
        tangents.append(point)
    return shoelace(vertices),shoelace(tangents)


def validate(records,candidates):
    lookup={(r["shape"],r["method"],r["n"],r["scale"]):r for r in records}
    for row in records:
        n=row["n"]
        lo,hi=F(row["lower"]),F(row["upper"])
        assert 0<=lo<=hi<=4
        mate=lookup[row["shape"],row["method"],n,3-row["scale"]]
        assert (row["lower"],row["upper"],row["classes"]) == (mate["lower"],mate["upper"],mate["classes"])
        if row["shape"]=="disk":
            if row["method"]=="polygon_exact":
                assert (lo,hi)==explicit_polygon_areas(n)
                assert hi-lo<=F(4,n*n)
            elif row["method"]=="polygon_rounded":
                el,eu=explicit_polygon_areas(n)
                assert lo<=el<=eu<=hi and hi-lo<=F(6,n*n)
            else:
                assert hi-lo == F(4*(2*n-1),n*n)
        else:
            target=2 if row["shape"]=="diamond" else 4
            assert lo<=target<=hi
        if row["method"]=="grid" and n<=16:
            def inside(i,j):
                if row["shape"]=="disk": return i*i+j*j<=n*n
                if row["shape"]=="diamond": return i+j<=n
                return max(i,j)<=n
            lc=sum(inside(i+1,j+1) for i in range(n) for j in range(n))
            uc=sum(inside(i,j) for i in range(n) for j in range(n))
            assert (lo,hi)==(F(4*lc,n*n),F(4*uc,n*n))
    # All definite statements agree with all other methods and levels.
    for shape in ("disk","diamond","square"):
        seen={str(root):set() for root in candidates}
        for row in records:
            if row["shape"]!=shape: continue
            for status,items in row["classes"].items():
                if status!="unresolved":
                    for root in items: seen[root].add(status)
        assert all(len(statuses)<=1 for statuses in seen.values())
    return dict(representation_invariance=True, independent_shoelace=True,
                independent_grid_enumeration_through_n16=True,
                theoretical_width_bounds=True, no_definite_conflicts=True,
                all_continuation_levels_pass=True)


def audit_edges(registry,corpus):
    before=file_sha256(corpus)
    with closing(connect_readonly(corpus)) as con:
        alignment=require_strict_alignment(con)
        reader=WitnessReader(con)
        present=outside=0
        for edge in registry.edges:
            a,b=int(edge["a"]),int(edge["b"])
            if max(a,b)>reader.stage:
                edge["observation"]="outside_saved_aperture"
                outside+=1
                continue
            witness=reader.edge(a,edge["op"],b)
            assert witness["present"], witness
            assert witness["value"]==edge["result"]
            assert witness["edge"]["stage"]==int(edge["predicted_stage"])
            edge["observation"]="recorded"
            edge["graph_witness"]=witness
            present+=1
    assert file_sha256(corpus)==before
    return dict(path=str(corpus),sha256=before,alignment=alignment,
                recorded_edges=present,outside_aperture_edges=outside,
                preservation="unchanged")


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir",required=True,type=Path)
    parser.add_argument("--corpus",type=Path,default=DEFAULT_CORPUS)
    args=parser.parse_args()
    out=args.output_dir.resolve()
    out.mkdir(parents=True,exist_ok=False)
    registry=Registry()
    candidates=roots()
    records=[]
    for n in LEVELS:
        for scale in (1,2):
            for shape in ("disk","diamond","square"):
                methods=("polygon_exact","polygon_rounded","grid") if shape=="disk" else ("polygon_exact","grid")
                for method in methods:
                    if method=="grid":
                        lo,hi,trace,details=grid(registry,n,scale,shape)
                    elif shape!="disk":
                        lo,hi,trace,details=polygon_control(registry,scale,shape)
                    else:
                        lo,hi,trace,details=polygons(registry,n,scale,method=="polygon_rounded")
                    classes={key:[] for key in ("below","above","exact","unresolved")}
                    for root in candidates:
                        classes[classification(root*root,lo,hi)].append(str(root))
                    comparisons=[]
                    for status,items in classes.items():
                        if items:
                            # Fixed sample: first sorted candidate in each category.
                            comparisons.append(comparison_certificate(registry,F(items[0]),lo,hi))
                    certificate=trace.summary()
                    rational_bounds=[b for b in (lo,hi) if b.denominator>1]
                    landing_floor=max((max(b.numerator,b.denominator) for b in rational_bounds),default=1)
                    assert int(certificate["stage"])>=landing_floor
                    records.append(dict(shape=shape,method=method,n=n,scale=scale,
                                        cohort="calibration" if n<=8 else "continuation",
                                        lower=str(lo),upper=str(hi),width=str(hi-lo),
                                        width_float=float(hi-lo),certificate=certificate,
                                        noninteger_final_landing_stage_floor=str(landing_floor),
                                        classes=classes,comparison_samples=comparisons,details=details))
    validation=validate(records,candidates)
    audit=audit_edges(registry,args.corpus.resolve())
    for row in records:
        row["recorded_certificate_edges"]=sum(registry.edges[i]["observation"]=="recorded" for i in row["certificate"]["edge_refs"])
        row["fully_recorded_in_u160"]=(row["recorded_certificate_edges"]==row["certificate"]["unique_edges"])
        row["candidate_cohort_counts"]={cohort:{status:sum((F(root).denominator<=16)==(cohort=="calibration") for root in items)
                                                    for status,items in row["classes"].items()}
                                       for cohort in ("calibration","continuation")}
    frontier=[]
    for scale in (1,2):
        disk=[r for r in records if r["shape"]=="disk" and r["scale"]==scale]
        for row in disk:
            dominated=any(int(other["certificate"]["stage"])<=int(row["certificate"]["stage"])
                          and F(other["width"])<=F(row["width"])
                          and (int(other["certificate"]["stage"])<int(row["certificate"]["stage"])
                               or F(other["width"])<F(row["width"])) for other in disk)
            if not dominated:
                frontier.append({key:row[key] for key in ("method","n","scale","width")}|dict(stage=row["certificate"]["stage"]))
    report=dict(evidence_layer="external_probe",claim_status="observation",
                definition_status="Candidate witness-indexed area-comparison cut, conditional on external geometry and a shrinking interval family.",
                preregistration=str(Path(__file__).with_name("AREA_INSPECTION_BRANCH_20261001.pre.md")),
                source_hashes={str(path.relative_to(ROOT)):file_sha256(path) for path in
                               (Path(__file__),Path(__file__).with_name("AREA_INSPECTION_BRANCH_20261001.pre.md"),
                                ROOT/'moo/research_utils.py',ROOT/'moo/shell_branch_search.py')},
                graph_audit=audit,validation=validation,
                grounding="Positive integer operands are references to the counting spine at their stated stages. Beyond U160 this is an admissibility certificate with an implicit spine, not a stored full corpus.",
                arithmetic_conventions="Zero terms are specialized externally; gcd/isqrt/rounding selectors have integer checks. Rational outputs are never operands. Stage counts omit external selector search and geometric proof costs.",
                candidates=[dict(root=str(r),square=str(r*r),cohort="calibration" if r.denominator<=16 else "continuation") for r in candidates],
                records=records,edges=registry.edges,finite_tested_frontier=frontier)
    (out/"report.json").write_text(json.dumps(report,indent=2)+"\n")
    compact=[]
    for row in records:
        if row["shape"]=="disk" and row["scale"]==1:
            compact.append(dict(n=row["n"],method=row["method"],width=row["width_float"],
                                stage=row["certificate"]["stage"],edges=row["certificate"]["unique_edges"],
                                unresolved=len(row["classes"]["unresolved"]),
                                fully_recorded=row["fully_recorded_in_u160"]))
    summary=dict(graph_audit=audit,validation=validation,rows=compact,finite_tested_frontier=frontier)
    (out/"summary.json").write_text(json.dumps(summary,indent=2)+"\n")
    print(json.dumps(summary,indent=2))


if __name__=="__main__":
    main()
