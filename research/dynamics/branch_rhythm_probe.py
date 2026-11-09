"""Clock-explicit branch rhythm calibration. No native recurrence-frame change."""
from __future__ import annotations

import argparse
from contextlib import closing
from fractions import Fraction as F
import json
from math import gcd,isqrt
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from moo.research_utils import connect_readonly,file_sha256,require_strict_alignment
from moo.shell_branch_search import WitnessReader

CORPUS=ROOT/"research/geometry/results/2026-10-01-square-area-inspection-v1/current_u160.sqlite"
AREA=ROOT/"research/geometry/results/2026-10-01-area-branch-comparison-v1/report.json"


class Evidence:
    def __init__(self):
        self.edges=[]
        self.index={}

    def edge(self,a,op,b):
        assert isinstance(a,int) and isinstance(b,int) and min(a,b)>0
        key=(a,op,b)
        if key not in self.index:
            value={"+":lambda:F(a+b),"-":lambda:F(a-b),"*":lambda:F(a*b),"/":lambda:F(a,b)}[op]()
            self.index[key]=len(self.edges)
            self.edges.append(dict(id=len(self.edges),a=a,op=op,b=b,value=str(value),predicted_stage=max(a,b)))
        return self.index[key]

    def bundle(self,roles):
        refs={name:self.edge(*spec) for name,spec in roles.items()}
        return dict(roles=refs,predicted_checkpoint=max(self.edges[i]["predicted_stage"] for i in refs.values()))

    def audit(self,path):
        before=file_sha256(path)
        with closing(connect_readonly(path)) as con:
            alignment=require_strict_alignment(con)
            reader=WitnessReader(con)
            for edge in self.edges:
                if edge["predicted_stage"]>reader.stage:
                    edge["status"]="outside_saved_aperture"
                    continue
                witness=reader.edge(edge["a"],edge["op"],edge["b"])
                assert witness["present"] and witness["operands_confirmed"]
                assert witness["value"]==edge["value"] and witness["edge"]["stage"]==edge["predicted_stage"]
                edge["status"]="recorded"
                edge["witness"]=witness
        assert file_sha256(path)==before
        return dict(path=str(path),sha256=before,alignment=alignment,
                    recorded=sum(e["status"]=="recorded" for e in self.edges),
                    predicted=sum(e["status"]!="recorded" for e in self.edges),unchanged=True)

    def observed_bundle(self,bundle):
        present=all(self.edges[i]["status"]=="recorded" for i in bundle["roles"].values())
        bundle.update(fully_recorded=present,observed_checkpoint=bundle["predicted_checkpoint"] if present else None)
        return present


def square_roles(prefix,root,scale):
    p,q=root.numerator*scale,root.denominator*scale
    return {prefix+"_root":(p,"/",q),prefix+"_numerator_square":(p,"*",p),
            prefix+"_denominator_square":(q,"*",q),prefix+"_square_value":(p*p,"/",q*q)}


def rational_comparison(evidence,x,y,c,scale):
    p,q=x.numerator*scale,x.denominator*scale
    r,s=y.numerator*scale,y.denominator*scale
    a,b=c.numerator,c.denominator
    numerator,denominator=a*r*r,b*s*s
    left,right=p*p*denominator,numerator*q*q
    roles=square_roles("x",x,scale)|square_roles("y",y,scale)|{
        "coefficient":(a,"/",b),"scaled_numerator":(a,"*",r*r),
        "scaled_denominator":(b,"*",s*s),"scaled_square_value":(numerator,"/",denominator),
        "left_cross_product":(p*p,"*",denominator),"right_cross_product":(numerator,"*",q*q),
        "difference":(left,"-",right)}
    return dict(x=str(x),y=str(y),coefficient=str(c),raw_scale=scale,
                square_value=str(x*x),scaled_square_value=str(c*y*y),exact_match=left==right,
                bundle=evidence.bundle(roles))


def rational_matches(evidence):
    records=[]
    for H in (4,8,16,32,64):
        roots=sorted({F(p,q) for p in range(1,H+1) for q in range(1,H+1)})
        values={root*root:root for root in roots}
        for c in map(F,("1","4","9/4","2","3","1/2")):
            matches=[(values[c*y*y],y) for y in roots if c*y*y in values]
            is_square=isqrt(c.numerator)**2==c.numerator and isqrt(c.denominator)**2==c.denominator
            assert bool(matches)==is_square
            selected=sorted({0,len(matches)//2,len(matches)-1}) if matches else []
            pairs=[matches[i] for i in selected] if matches else [(F(1),F(1))]
            witnesses=[rational_comparison(evidence,x,y,c,scale) for x,y in pairs for scale in (1,2)]
            records.append(dict(H=H,cohort="calibration" if H<=16 else "continuation",coefficient=str(c),
                                roots=len(roots),matches=[[str(x),str(y)] for x,y in matches],
                                count=len(matches),coefficient_is_rational_square=is_square,witness_samples=witnesses))
    return records


def scan_near(cap):
    found=set()
    for m in range(1,cap+1):
        for sign in (-1,1):
            candidate=2*m*m+sign
            n=isqrt(candidate)
            if n*n==candidate: found.add((n,m))
    return sorted(found,key=lambda p:p[1])


def recurrence(cap):
    n,m=1,1
    found=[]
    while m<=cap:
        found.append((n,m))
        n,m=n+2*m,n+m
    return found


def near_certificate(evidence,n,m,scale,denominator):
    p,r,q=scale*n,scale*m,denominator
    pp,rr,qq=p*p,r*r,q*q
    doubled=2*rr
    gap=abs(pp-doubled)
    assert gap>0
    roles={"x_root":(p,"/",q),"y_root":(r,"/",q),"x_square":(p,"*",p),
           "y_square":(r,"*",r),"denominator_square":(q,"*",q),
           "x_square_value":(pp,"/",qq),"y_square_value":(rr,"/",qq),
           "double_square":(rr,"+",rr),"double_square_value":(doubled,"/",qq),
           "directed_defect":(pp,"-",doubled),"gap_magnitude":(max(pp,doubled),"-",min(pp,doubled)),
           "scaled_gap":(gap,"/",qq),"relative_gap_magnitude":(gap,"/",rr)}
    common=gcd(n,m)
    primitive=(n//common,m//common)
    return dict(n=n,m=m,scale=scale,denominator=denominator,roots=[str(F(p,q)),str(F(r,q))],
                directed_defect=str(F(pp-doubled,qq)),relative_defect=str(F(pp-doubled,rr)),
                primitive=list(primitive),primitive_defect=primitive[0]**2-2*primitive[1]**2,
                raw_unit_defect=abs(n*n-2*m*m)==1,bundle=evidence.bundle(roles))


def calibrations(evidence):
    records=[]
    for n in range(1,129):
        records.append(dict(source=n,square=evidence.edge(n,"*",n),self_add=evidence.edge(n,"+",n),
                            triple=evidence.edge(3,"*",n),cohort="calibration" if n<=64 else "continuation"))
    double_values={2*n:n for n in range(1,129)}
    triple_values={3*n:n for n in range(1,129)}
    square_values={n*n:n for n in range(1,129)}
    linear=[dict(value=v,double_source=double_values[v],triple_source=triple_values[v])
            for v in sorted(double_values.keys()&triple_values.keys())]
    squares=[dict(value=v,double_source=double_values[v],square_source=square_values[v])
             for v in sorted(double_values.keys()&square_values.keys())]
    assert [r["value"] for r in linear]==[6*k for k in range(1,43)]
    assert [r["value"] for r in squares]==[4*k*k for k in range(1,9)]
    return dict(records=records,linear_output_coincidences=linear,square_output_coincidences=squares,
                same_source_square_self_add=[n for n in range(1,129) if n*n==2*n],
                same_source_square_triple=[n for n in range(1,129) if n*n==3*n])


def area_reinspection(path):
    report=json.loads(path.read_text())
    methods={}
    for method in ("polygon_exact","polygon_rounded","grid"):
        rows=[r for r in report["records"] if (r["shape"],r["method"],r["scale"])==("disk",method,1)]
        seen=set()
        events=[]
        for row in rows:
            certain=set(row["classes"]["below"]+row["classes"]["above"]+row["classes"]["exact"])
            assert seen<=certain
            events.append(dict(N=row["n"],new_definite=len(certain-seen),unresolved=len(row["classes"]["unresolved"]),
                               checkpoint=row["certificate"]["stage"]))
            seen=certain
        methods[method]=events
    return dict(source=str(path),sha256=file_sha256(path),status="retrospective, seven prescribed dyadic checkpoints; no period inference",methods=methods)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir",type=Path,required=True)
    args=parser.parse_args()
    out=args.output_dir.resolve()
    out.mkdir(parents=True,exist_ok=False)
    e=Evidence()
    basic=calibrations(e)
    rational=rational_matches(e)
    pairs=scan_near(512)
    assert pairs==recurrence(512)
    near=[]
    for index,(n,m) in enumerate(pairs):
        transition=e.bundle({"double_m":(m,"+",m),"next_n":(n,"+",2*m),"next_m":(n,"+",m)})
        norm=n*n-2*m*m
        assert norm==(-1 if index%2==0 else 1)
        assert (n+2*m)**2-2*(n+m)**2==-norm
        variants=[near_certificate(e,n,m,s,q) for s in (1,2) for q in (1,3)]
        controls=[near_certificate(e,n+1,m,s,q) for s in (1,2) for q in (1,3)]
        assert len({v["relative_defect"] for v in variants})==1
        near.append(dict(index=index+1,n=n,m=m,cohort="calibration" if m<=32 else "continuation",
                         norm=norm,integer_certificate_stage=max(n*n,2*m*m),transition=transition,
                         target=[n+2*m,n+m],variants=variants,neighbors=controls))
    costs=[row["integer_certificate_stage"] for row in near]
    assert all(costs[k+2]==6*costs[k+1]-costs[k]-2 for k in range(len(costs)-2))
    audit=e.audit(CORPUS)
    for row in rational:
        for sample in row["witness_samples"]:
            if e.observed_bundle(sample["bundle"]):
                roles=sample["bundle"]["roles"]
                a=e.edges[roles["x_square_value"]]["witness"]["edge"]["result_node_id"]
                b=e.edges[roles["scaled_square_value"]]["witness"]["edge"]["result_node_id"]
                assert (a==b)==sample["exact_match"]
    causal=[]
    for i,row in enumerate(near):
        full=e.observed_bundle(row["transition"])
        for sample in row["variants"]+row["neighbors"]: e.observed_bundle(sample["bundle"])
        roles=row["transition"]["roles"]
        double=e.edges[roles["double_m"]]
        nextn=e.edges[roles["next_n"]]
        assert double["predicted_stage"]<=nextn["predicted_stage"] and nextn["predicted_stage"]>=2*row["m"]
        if full:
            assert double["witness"]["edge"]["result_node_id"]==nextn["witness"]["edge"]["right_node_id"]
        if i:
            prev=near[i-1]
            previous_n=e.edges[prev["transition"]["roles"]["next_n"]]
            previous_m=e.edges[prev["transition"]["roles"]["next_m"]]
            assert previous_n["predicted_stage"]<=nextn["predicted_stage"]
            assert previous_m["predicted_stage"]<=double["predicted_stage"]
            recorded=full and prev["transition"]["fully_recorded"]
            if recorded:
                assert previous_n["witness"]["edge"]["result_node_id"]==nextn["witness"]["edge"]["left_node_id"]
                assert previous_m["witness"]["edge"]["result_node_id"]==double["witness"]["edge"]["left_node_id"]
            causal.append(dict(from_index=i,to_index=i+1,chronological_prediction=True,node_continuity_recorded=recorded))
    for row in basic["records"]:
        assert e.edges[row["square"]]["witness"]["edge"]["stage"]==row["source"]
        assert e.edges[row["self_add"]]["witness"]["edge"]["stage"]==row["source"]
    report=dict(evidence_layer="external_probe",claim_status="observation",
                design=str(Path(__file__).with_name("BRANCH_RHYTHM_20261002.pre.md")),
                source_hashes={str(p.relative_to(ROOT)):file_sha256(p) for p in
                               (Path(__file__),Path(__file__).with_name("BRANCH_RHYTHM_20261002.pre.md"),
                                ROOT/'moo/shell_branch_search.py',ROOT/'moo/research_utils.py')},
                graph_audit=audit,basic=basic,rational_comparisons=rational,near_alignments=near,
                root_lineage_checks=causal,area_reinspection=area_reinspection(AREA),edges=e.edges,
                limits=["Value, occurrence stage and recurrence index are distinct clocks.",
                        "The Pell recurrence is a classical external selector audited against native integer edges.",
                        "The signed defect period is not a period of graph arrival times.",
                        "Rational squares use explicit integer encodings; no speculative fractional operands.",
                        "Outside U160, stages are predictions, not recorded edges.",
                        "No pi rhythm or privileged circle branch is established."])
    (out/"report.json").write_text(json.dumps(report,indent=2)+"\n")
    summary=dict(graph_audit=audit,near_pairs=pairs,residue_signs=[r["norm"] for r in near],
                 certificate_stages=costs,certificate_gaps=[b-a for a,b in zip(costs,costs[1:])],
                 recorded_root_transitions=sum(r["transition"]["fully_recorded"] for r in near),
                 recorded_primitive_norm_certificates=sum(r["variants"][0]["bundle"]["fully_recorded"] for r in near),
                 rational_counts=[{k:r[k] for k in ("H","coefficient","roots","count")} for r in rational],
                 normalized_neighbor_returns=[dict(pair=[r["n"]+1,r["m"]],primitive=r["neighbors"][0]["primitive"])
                                              for r in near if abs(r["neighbors"][0]["primitive_defect"])==1],
                 area_reinspection=report["area_reinspection"])
    (out/"summary.json").write_text(json.dumps(summary,indent=2)+"\n")
    print(json.dumps(summary,indent=2))


if __name__=="__main__":
    main()
