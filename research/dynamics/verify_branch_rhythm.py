"""Independent arithmetic, enumeration, graph and chronological readback."""
from fractions import Fraction as F
import hashlib
import json
from math import isqrt
from pathlib import Path
import sqlite3
import sys

ROOT=Path(__file__).resolve().parents[2]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    path=Path(sys.argv[1]).resolve()
    report=json.loads(path.read_text())
    for source,digest in report['source_hashes'].items(): assert sha(ROOT/source)==digest
    db=Path(report['graph_audit']['path'])
    assert sha(db)==report['graph_audit']['sha256']
    con=sqlite3.connect(db.as_uri()+'?mode=ro',uri=True)
    con.row_factory=sqlite3.Row
    recorded=0
    try:
        for edge in report['edges']:
            a,b=edge['a'],edge['b']
            assert min(a,b)>0
            value={'+':lambda:F(a+b),'-':lambda:F(a-b),'*':lambda:F(a*b),'/':lambda:F(a,b)}[edge['op']]()
            assert value==F(edge['value']) and max(a,b)==edge['predicted_stage']
            if edge['status']=='recorded':
                witness=edge['witness']['edge']
                row=con.execute('''SELECT e.stage,e.op,l.p lp,l.q lq,l.confirmed_stage lc,
                    r.p rp,r.q rq,r.confirmed_stage rc,v.p vp,v.q vq FROM edges e
                    JOIN nodes l ON l.node_id=e.left_node_id JOIN nodes r ON r.node_id=e.right_node_id
                    JOIN nodes v ON v.node_id=e.result_node_id WHERE e.edge_id=?''',(witness['edge_id'],)).fetchone()
                assert (row['lp'],row['rp'],row['lq'],row['rq'],row['op'])==(a,b,1,1,edge['op'])
                assert F(row['vp'],row['vq'])==value and row['stage']==max(a,b)
                assert row['lc']<=row['stage'] and row['rc']<=row['stage']
                recorded+=1
    finally:
        con.close()
    brute=[(n,m) for m in range(1,513) for n in range(1,2*m+1) if abs(n*n-2*m*m)==1]
    assert brute==[(row['n'],row['m']) for row in report['near_alignments']]
    for row in report['near_alignments']:
        n,m=row['n'],row['m']
        steps=0
        while (n,m)!=(1,1):
            nn,mm=2*m-n,n-m
            assert nn>0 and 0<mm<m and abs(nn*nn-2*mm*mm)==1
            n,m=nn,mm
            steps+=1
        assert steps==row['index']-1
        for variant in row['variants']+row['neighbors']:
            x,y=map(F,variant['roots'])
            assert F(variant['directed_defect'])==x*x-2*y*y
            assert F(variant['relative_defect'])==(x*x-2*y*y)/(y*y)
            a,b=variant['primitive']
            assert a*a-2*b*b==variant['primitive_defect']
    for row in report['rational_comparisons']:
        H=row['H']; c=F(row['coefficient'])
        roots={F(a,b) for a in range(1,H+1) for b in range(1,H+1)}
        cn,cd=isqrt(c.numerator),isqrt(c.denominator)
        if cn*cn==c.numerator and cd*cd==c.denominator:
            ratio=F(cn,cd)
            expected={(ratio*y,y) for y in roots if (ratio*y).numerator<=H and (ratio*y).denominator<=H}
        else:
            expected=set()  # Lowest-term rational square criterion, proved in the note.
        actual={tuple(map(F,pair)) for pair in row['matches']}
        assert expected==actual and len(actual)==row['count'] and len(roots)==row['roots']
    assert sha(db)==report['graph_audit']['sha256']
    assert sha(Path(report['area_reinspection']['source']))==report['area_reinspection']['sha256']
    result=dict(status='pass',report_sha256=sha(path),verifier_sha256=sha(Path(__file__)),
                arithmetic_requests_checked=len(report['edges']),sqlite_edges_reread=recorded,
                independent_integer_pairs_tested=sum(2*m for m in range(1,513)),
                near_pairs=len(brute),rational_windows_checked=len(report['rational_comparisons']),
                inverse_recurrence_checks=True,source_hashes_match=True,corpus_unchanged=True)
    dest=path.with_name('independent_validation.json')
    if dest.exists(): raise SystemExit('Refusing to overwrite validation')
    dest.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__': main()
