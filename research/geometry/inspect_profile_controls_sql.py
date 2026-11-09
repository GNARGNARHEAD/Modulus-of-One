"""Independent direct-SQL inspection of orientation, scale, and composition routes."""
from contextlib import closing
from fractions import Fraction
import argparse,hashlib,json
from pathlib import Path
import sqlite3

WIDE=Path('out/scratch/shell_composition_20260920_current_v1/wide_u576.sqlite')
NARROW=Path('out/scratch/shell_composition_20260920_current_v1/narrow_u80.sqlite')
INDEX=Path('out/scratch/node_profiles_20261104_reviewed/associations.sqlite')


def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda:handle.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


def read(path):
    conn=sqlite3.connect(path.resolve().as_uri()+'?mode=ro',uri=True)
    conn.row_factory=sqlite3.Row
    return conn


class Raw:
    def __init__(self,conn):
        self.conn=conn
        self.config=json.loads(conn.execute("SELECT value FROM meta WHERE key='config_json'").fetchone()[0])
        self.stage=conn.execute('SELECT MAX(stage) FROM stages').fetchone()[0]
        telemetry=conn.execute('SELECT stage,candidate_events FROM stages ORDER BY stage').fetchall()
        self.contiguous_candidate_telemetry=(len(telemetry)==self.stage and all(row['stage']==i and row['candidate_events']==4*(2*i-1) for i,row in enumerate(telemetry,1)))
        self.nodes={}

    def node(self,value):
        value=Fraction(value)
        if value not in self.nodes:
            row=self.conn.execute('SELECT node_id,first_stage,confirmed_stage FROM nodes WHERE p=? AND q=?',(value.numerator,value.denominator)).fetchone()
            self.nodes[value]=dict(row) if row else None
        return self.nodes[value]

    def request(self,role,a,op,b):
        a,b=Fraction(a),Fraction(b)
        c={'+':lambda:a+b,'-':lambda:a-b,'*':lambda:a*b,'/':lambda:a/b}[op]()
        ids=[self.node(v) for v in (a,b,c)]
        positive=a.denominator==b.denominator==1 and a>=1 and b>=1
        candidate=int(max(a,b)) if positive else None
        within=positive and candidate<=self.stage
        cfg=self.config
        retained=None if not positive else bool((cfg.get('retain_confirmed_edges',True) and c.denominator==1 and 1<=c<=candidate) or (abs(c.numerator)<=cfg['max_abs_p'] and c.denominator<=cfg['max_abs_q'] and (cfg['max_abs_value'] is None or abs(c)<=Fraction(str(cfg['max_abs_value'])))))
        rows=[]
        if all(node is not None for node in ids):
            rows=self.conn.execute('''SELECT edge_id,stage,left_node_id,right_node_id,result_node_id
                FROM edges WHERE left_node_id=? AND op=? AND right_node_id=? AND result_node_id=?
                  AND stage<=? ORDER BY stage,edge_id''',(ids[0]['node_id'],op,ids[1]['node_id'],ids[2]['node_id'],self.stage)).fetchall()
        if rows:
            assert within and retained
            assert all(ids[0]['confirmed_stage']<=row['stage'] and ids[1]['confirmed_stage']<=row['stage'] for row in rows)
        blocker=None if rows else ('operand_not_positive_spine' if not positive else 'candidate_beyond_checkpoint' if not within else 'result_excluded_at_candidate_stage' if not retained else 'missing_saved_edge')
        return {'role':role,'left':str(a),'op':op,'right':str(b),'result':str(c),
                'positive_spine_operands':positive,'candidate_stage':candidate,'within_checkpoint':within,
                'retained_by_config_at_candidate_stage':retained,'observed':bool(rows),
                'first_observed_stage':rows[0]['stage'] if rows else None,'blocker':blocker,
                'edge_refs':[dict(row) for row in rows]}

    def shell(self,triple):
        x,y,r=triple
        assert x*x+y*y==r*r
        requests=[self.request('x_square',x,'*',x),self.request('y_square',y,'*',y),self.request('radius_square',r,'*',r),self.request('square_sum',x*x,'+',y*y)]
        return bundle(requests)


def bundle(requests,dependencies=()):
    full=all(r['observed'] for r in requests) and all(d['status']=='witnessed' for d in dependencies)
    some=any(r['observed'] for r in requests) or any(d['status']!='unwitnessed' for d in dependencies)
    stages=[r['first_observed_stage'] for r in requests if r['observed']]+[d['completion_stage'] for d in dependencies if d['status']=='witnessed']
    potential=[r['candidate_stage'] if r['positive_spine_operands'] and r['retained_by_config_at_candidate_stage'] else None for r in requests]+[d['same_rule_candidate_stage'] for d in dependencies]
    return {'status':'witnessed' if full else 'partial' if some else 'unwitnessed',
            'completion_stage':max(stages) if full and stages else None,
            'same_rule_candidate_stage':max(potential) if potential and all(s is not None for s in potential) else None,
            'local_requests_complete':all(r['observed'] for r in requests) if requests else None,
            'local_completion_stage':max(r['first_observed_stage'] for r in requests) if requests and all(r['observed'] for r in requests) else None,
            'requests':requests}


def profile_support(index,ref):
    row=index.execute('SELECT data FROM certificates WHERE ref=?',(ref,)).fetchone()
    if row is None:return {'selected':False,'meaning':'No such certificate in this bounded fixed-seed index; not a negative mathematical or graph result.'}
    payload=json.loads(row[0])['support']
    return {'selected':True,'status':payload['status'],'completion_stage':payload['first_supported_stage']}


def sequence(reader,index,seed):
    a,b,c=seed
    source_shell=reader.shell(seed)
    previous=None
    x,y,r=seed
    result=[]
    for n in range(1,10):
        requests=[]
        if n>1:
            px,py,pr=x,y,r
            ac,bd,ad,bc=px*a,py*b,px*b,py*a
            requests=[reader.request('ac',px,'*',a),reader.request('bd',py,'*',b),
                      reader.request('ad',px,'*',b),reader.request('bc',py,'*',a),
                      reader.request('x',ac,'-',bd),reader.request('y',ad,'+',bc),
                      reader.request('radius',pr,'*',c)]
            x,y,r=ac-bd,ad+bc,pr*c
        linked=bundle(requests,(source_shell,) if previous is None else (source_shell,previous))
        direct=reader.shell((x,y,r))
        assert x*x+y*y==r*r
        ref=f'spiral:{a},{b},{c}:{n}#scalar_lineage'
        selected=profile_support(index,ref)
        if selected['selected']:
            assert selected['status']==linked['status'] and selected['completion_stage']==linked['completion_stage']
        shell_ref=f'shell:{x},{y},{r}#literal'
        selected_shell=profile_support(index,shell_ref)
        if selected_shell['selected']:
            assert selected_shell['status']==direct['status'] and selected_shell['completion_stage']==direct['completion_stage']
        nodes=[]
        for role,value in (('x',x),('y',y),('radius',r)):
            node=reader.node(value)
            entry=index.execute('SELECT snapshot FROM nodes WHERE value=?',(str(value),)).fetchone()
            nodes.append({'role':role,'value':str(value),'present_in_source':node is not None,
                          'source_node':node,'present_in_profile_participants':entry is not None})
        result.append({'iteration':n,'triple':[x,y,r],'unit_normalization':[str(Fraction(x,r)),str(Fraction(y,r)),'1'],'exact_norm_identity':True,'linked_lineage':linked,
                       'direct_literal_shell':direct,'source_nodes':nodes,
                       'profile_lineage':selected,'profile_direct_shell':selected_shell})
        previous=linked
        if linked['status']!='witnessed':break
    return {'seed':list(seed),'stop':'First incomplete linked-lineage step under the selected source/operand rules.',
            'steps':result}


def summary(payload):
    return {k:v for k,v in payload.items() if k!='requests'}


def pair_requests(reader,left,right):
    a,b,r=left
    c,d,s=right
    ac,bd,ad,bc=a*c,b*d,a*d,b*c
    requests=[reader.request('ac',a,'*',c),reader.request('bd',b,'*',d),
              reader.request('ad',a,'*',d),reader.request('bc',b,'*',c),
              reader.request('x',ac,'-',bd),reader.request('y',ad,'+',bc),
              reader.request('radius',r,'*',s)]
    return (ac-bd,ad+bc,r*s),requests


def all_splits(reader,index,family):
    seed=tuple(family['seed'])
    powers={1:seed}
    for n in range(2,5):
        previous=powers[n-1]
        powers[n]=(previous[0]*seed[0]-previous[1]*seed[1],
                   previous[0]*seed[1]+previous[1]*seed[0],previous[2]*seed[2])
    sequential={step['iteration']:step for step in family['steps']}
    rows=[]
    for n in range(2,5):
        for i in range(1,n):
            j=n-i
            target,requests=pair_requests(reader,powers[i],powers[j])
            assert target==powers[n]
            assert target[0]*target[0]+target[1]*target[1]==target[2]*target[2]
            scalar=bundle(requests)
            lineages=[sequential[k]['linked_lineage'] for k in (i,j)]
            source_shells=[sequential[k]['direct_literal_shell'] for k in (i,j)]
            rows.append({'target_iteration':n,'ordered_split':[i,j],
                         'left_source':list(powers[i]),'right_source':list(powers[j]),'target':list(target),
                         'scalar_only':scalar,
                         'with_selected_source_lineages':summary(bundle(requests,lineages)),
                         'with_direct_source_shells':summary(bundle(requests,source_shells)),
                         'source_evidence_location':'families[].steps with iterations i,j; repeated equal inputs share the same source certificate, not independent evidence.',
                         'target_direct_literal_shell':summary(reader.shell(target)),
                         'fixed_profile_sequential_lineage':profile_support(index,f"spiral:{seed[0]},{seed[1]},{seed[2]}:{n}#scalar_lineage")})
    return rows


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write',type=Path,required=True)
    args=parser.parse_args()
    if args.write.exists():parser.error('Refusing to overwrite '+str(args.write))
    paths=(WIDE,NARROW,INDEX)
    before={str(p.resolve()):digest(p) for p in paths}
    with closing(read(WIDE)) as wide,closing(read(NARROW)) as narrow,closing(read(INDEX)) as index:
        manifest=json.loads(index.execute("SELECT value FROM metadata WHERE key='manifest'").fetchone()[0])
        assert manifest['source']['sha256']==before[str(WIDE.resolve())]
        wr,nr=Raw(wide),Raw(narrow)
        families=[sequence(wr,index,seed) for seed in ((4,3,5),(3,4,5),(8,6,10))]
        for family in families:
            family['ordered_composition_splits_through_four']=all_splits(wr,index,family)
        scale_checks=[]
        for base,scaled in zip(families[0]['steps'],families[2]['steps']):
            factor=2**base['iteration']
            assert scaled['triple']==[factor*v for v in base['triple']]
            assert scaled['unit_normalization']==base['unit_normalization']
            scale_checks.append({'iteration':base['iteration'],'raw_scale_factor':factor,'equal_unit_normalization':True})
        narrow_control=[{'seed':list(seed),'literal_seed_shell':nr.shell(seed),
                         'coordinate_nodes':[{'value':str(v),'source_node':nr.node(v)} for v in seed]} for seed in ((4,3,5),(3,4,5))]
        result={'method':'Independent exact pair multiplication and direct SQLite witness queries. No profile selector/support functions or tests are used for truth; saved profile claims are compared afterward.',
                'scope':'One fixed seed, its coordinate-swapped control and scale-two control. Sequential lineage is inspected through its first incomplete step; every ordered split i+j=n for2<=n<=4 is separately inspected. No claim of all spirals, all algebraic rewrites, or a new timing law.',
                'input_sha256':before,'auditor_sha256':digest(Path(__file__)),
                'wide_source':{'checkpoint':wr.stage,'config':wr.config,'contiguous_expected_candidate_telemetry':wr.contiguous_candidate_telemetry},
                'families':families,'scale_control_checks':scale_checks,'narrow_retention_control':{'checkpoint':nr.stage,'config':nr.config,'contiguous_expected_candidate_telemetry':nr.contiguous_candidate_telemetry,'seed_inspections':narrow_control},
                'interpretation':{'ordered_orientation':'Swapping seed coordinates changes signed iterates; taking absolute values would change the repeated construction.',
                                  'lineage_vs_norm':'A witnessed transition can precede its direct target-shell certificate, or produce a negative output whose next reuse is forbidden. These are joint certificate availability stages, not chronological execution traces; scalar inputs may exist by other routes before the preceding selected transition completes.',
                                  'conditional_prediction':'same_rule_candidate_stage is derived from positive-integer operand readiness and the retained-result rule, conditional on extending the frontier to that stage. It is not an observed stage beyond the saved checkpoint; null means this named certificate cannot be completed without changing an operand or retention assumption.',
                                  'selection':'The frozen reviewed index used for historical comparison selects only seed(4,3,5) and its sequential scalar_lineage criterion. Missing seed/split associations are selection limits, even where SQL supplies complete alternative construction support. This does not describe any later parameterized builder.',
                                  'node_presence':'A target value can exist via unrelated operations while the selected spiral transition is blocked.',
                                  'split_criteria':'scalar_only asks only for the seven pair-product requests. with_selected_source_lineages additionally binds each source to its seed power; with_direct_source_shells instead requires direct literal source norm certificates. These are different criteria. A failed sequential route is not a proof that the power has no other supported construction.',
                                  'retention':'Narrow-source literal seed shells can be unwitnessed despite coordinate nodes being present; this is a retained-edge aperture limitation.'}}
    after={str(p.resolve()):digest(p) for p in paths}
    assert before==after
    result['inputs_unchanged']=True
    output=args.write
    output.parent.mkdir(parents=True,exist_ok=True)
    with output.open('x') as handle:
        handle.write(json.dumps(result,indent=2,sort_keys=True)+'\n')
    brief={'output':str(output),'families':[{'seed':f['seed'],'steps':[{'n':s['iteration'],'triple':s['triple'],'lineage_status':s['linked_lineage']['status'],'lineage_stage':s['linked_lineage']['completion_stage'],'candidate_stage':s['linked_lineage']['same_rule_candidate_stage'],'direct_status':s['direct_literal_shell']['status'],'direct_stage':s['direct_literal_shell']['completion_stage'],'profile_selected':s['profile_lineage']['selected']} for s in f['steps']]} for f in families], 'narrow_seed_statuses':[s['literal_seed_shell']['status'] for s in narrow_control],'inputs_unchanged':True}
    print(json.dumps(brief,indent=2))


if __name__=='__main__':main()
