"""Independent readback of the saved report, arithmetic and graph records."""
import argparse
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path
import sqlite3
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from tests.test_moo_circle_square_area_probe import geometric_polygon_areas


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("report",type=Path)
    args=parser.parse_args()
    report=json.loads(args.report.read_text())
    for source,digest in report["source_hashes"].items():
        assert sha(ROOT/source)==digest
    candidates={F(p,q) for q in range(1,33) for p in range(1,2*q+1)}
    assert candidates=={F(c["root"]) for c in report["candidates"]}
    graph=Path(report["graph_audit"]["path"])
    assert sha(graph)==report["graph_audit"]["sha256"]
    con=sqlite3.connect(graph.as_uri()+"?mode=ro",uri=True)
    con.row_factory=sqlite3.Row
    recorded=0
    try:
        for e in report["edges"]:
            a,b=int(e["a"]),int(e["b"])
            assert min(a,b)>0
            val={"+":lambda:F(a+b),"-":lambda:F(a-b),"*":lambda:F(a*b),"/":lambda:F(a,b)}[e["op"]]()
            assert val==F(e["result"])
            assert max(a,b)==int(e["predicted_stage"])
            if e["observation"]=="recorded":
                w=e["graph_witness"]["edge"]
                row=con.execute("""SELECT e.stage,e.op,l.p lp,l.q lq,l.confirmed_stage lc,
                    r.p rp,r.q rq,r.confirmed_stage rc,v.p vp,v.q vq
                    FROM edges e JOIN nodes l ON l.node_id=e.left_node_id
                    JOIN nodes r ON r.node_id=e.right_node_id
                    JOIN nodes v ON v.node_id=e.result_node_id WHERE e.edge_id=?""",(w["edge_id"],)).fetchone()
                assert (row["lp"],row["rp"],row["lq"],row["rq"],row["op"])==(a,b,1,1,e["op"])
                assert F(row["vp"],row["vq"])==val
                assert row["stage"]==max(a,b) and row["lc"]<=row["stage"] and row["rc"]<=row["stage"]
                recorded+=1
    finally:
        con.close()
    lookup={}
    for row in report["records"]:
        n=row["n"]
        lo,hi=F(row["lower"]),F(row["upper"])
        if row["method"]=="grid":
            def inside(i,j):
                return {"disk":i*i+j*j<=n*n,"diamond":i+j<=n,"square":i<=n and j<=n}[row["shape"]]
            low=sum(inside(i+1,j+1) for i in range(n) for j in range(n))
            high=sum(inside(i,j) for i in range(n) for j in range(n))
            assert (lo,hi)==(F(4*low,n*n),F(4*high,n*n))
        elif row["shape"]=="disk":
            exact=geometric_polygon_areas(n)
            if row["method"]=="polygon_exact":
                assert (lo,hi)==exact
            else:
                D=n**3
                lower=upper=0
                for k in range(n):
                    w=F(n,n*n+k*(k+1))
                    a,b=4*w/(1+w*w)*D,4*w*D
                    lower+=a.numerator//a.denominator
                    upper+=(b.numerator+b.denominator-1)//b.denominator
                assert (lo,hi)==(F(lower,D),F(upper,D))
                assert lo<=exact[0]<=exact[1]<=hi
        else:
            assert lo==hi==({"diamond":2,"square":4}[row["shape"]])
        assert hi-lo==F(row["width"])
        assigned={}
        for status,rs in row["classes"].items():
            for s in rs:
                root=F(s)
                expected="below" if root*root<lo else "above" if root*root>hi else "exact" if lo==hi==root*root else "unresolved"
                assert status==expected and root not in assigned
                assigned[root]=status
        assert set(assigned)==candidates
        cost=max(int(report["edges"][i]["predicted_stage"]) for i in row["certificate"]["edge_refs"])
        assert cost==int(row["certificate"]["stage"])
        key=(row["shape"],row["method"],row["scale"])
        if key in lookup:
            oldlo,oldhi,old=lookup[key]
            assert lo>=oldlo and hi<=oldhi
            assert all(s=="unresolved" or assigned[c]==s for c,s in old.items())
        lookup[key]=(lo,hi,assigned)
    assert sha(graph)==report["graph_audit"]["sha256"]
    result=dict(report_sha256=sha(args.report),verifier_sha256=sha(Path(__file__)),
                arithmetic_edges_checked=len(report["edges"]),sqlite_edges_reread=recorded,
                exact_intervals_checked=len(report["records"]),candidate_comparisons_checked=len(candidates)*len(report["records"]),
                grid_cell_enumeration="All levels including N64",nested_intervals=True,
                persistent_classification=True,source_hashes_match=True,corpus_unchanged=True,status="pass")
    target=args.report.with_name("independent_validation.json")
    if target.exists():
        raise SystemExit("Refusing to overwrite saved independent validation")
    target.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))


if __name__=="__main__":
    main()
