"""Read-only profile audit using only SQLite, exact fractions and saved records.

This does not import profile, selector, GraphEvidence or test code. It checks
all saved named-certificate requests directly against the source, then recomputes complete
certificate/association stages from those observed records. It is not a proof
that an arbitrary named request bundle implies its advertised mathematics.
"""
import argparse
from contextlib import closing
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import sqlite3


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def readonly(path):
    return sqlite3.connect(Path(path).resolve().as_uri() + '?mode=ro', uri=True)


def audit(source_path, index_path):
    before_source, before_index = digest(source_path), digest(index_path)
    errors, observed, keys, local = [], {}, {}, {}
    with closing(readonly(source_path)) as src, closing(readonly(index_path)) as idx:
        manifest = json.loads(idx.execute("SELECT value FROM metadata WHERE key='manifest'").fetchone()[0])
        if manifest['schema_version'] not in {'moo_node_profiles.v2', 'moo_node_profiles.v3'}:
            raise ValueError('This auditor targets saved v2/v3 certificate indexes')
        checkpoint = manifest['source']['checkpoint']
        if before_source != manifest['source']['sha256']:
            errors.append({'kind': 'source_hash_mismatch'})
        certificates = {ref: json.loads(raw) for ref, raw in idx.execute('SELECT ref,data FROM certificates')}
        checked_refs = 0
        for ref, certificate in certificates.items():
            observations = []
            for request in certificate['support']['requests']:
                a, b, c = map(Fraction, (request['left'], request['right'], request['result']))
                op = request['op']
                actual = {'+': lambda: a+b, '-': lambda: a-b, '*': lambda: a*b, '/': lambda: a/b}[op]()
                if actual != c:
                    errors.append({'kind': 'arithmetic', 'certificate': ref, 'request': request})
                signature = (str(a), op, str(b), str(c))
                if signature not in observed:
                    ids = []
                    for value in (a, b, c):
                        if value not in keys:
                            row = src.execute('SELECT node_id FROM nodes WHERE p=? AND q=?',
                                              (value.numerator, value.denominator)).fetchone()
                            keys[value] = row[0] if row else None
                        ids.append(keys[value])
                    rows = src.execute('''SELECT edge_id,stage FROM edges
                        WHERE left_node_id=? AND op=? AND right_node_id=?
                          AND result_node_id=? AND stage<=? ORDER BY stage,edge_id''',
                        (ids[0], op, ids[1], ids[2], checkpoint)).fetchall() if all(x is not None for x in ids) else []
                    for edge_id, stage in rows:
                        if not (a.denominator == b.denominator == 1 and 1 <= a <= stage and 1 <= b <= stage):
                            errors.append({'kind': 'operand_eligibility', 'request': signature, 'edge_id': edge_id, 'stage': stage})
                    observed[signature] = rows
                rows = observed[signature]
                if bool(rows) != request['witnessed']:
                    errors.append({'kind': 'witness_status', 'certificate': ref, 'request': signature})
                actual_stage = rows[0][1] if rows else None
                if actual_stage != request['first_stage']:
                    errors.append({'kind': 'request_stage', 'certificate': ref, 'request': signature,
                                   'observed': actual_stage, 'reported': request['first_stage']})
                for edge in request['edge_refs']:
                    checked_refs += 1
                    if (edge['edge_id'], edge['stage']) not in rows:
                        errors.append({'kind': 'reference', 'certificate': ref, 'request': signature, 'edge': edge})
                observations.append(actual_stage)
            local[ref] = observations
        resolved, active = {}, set()

        def calculate(ref):
            if ref in resolved:
                return resolved[ref]
            if ref in active:
                raise ValueError('Saved certificate cycle: ' + ref)
            active.add(ref)
            dependencies = [calculate(d['ref']) for d in certificates[ref]['support']['dependencies']]
            stages = local[ref] + [d['stage'] for d in dependencies]
            complete = bool(stages) and all(stage is not None for stage in stages)
            partial = any(stage is not None for stage in local[ref]) or any(d['status'] != 'unwitnessed' for d in dependencies)
            result = {'stage': max(stages) if complete else None,
                      'status': 'witnessed' if complete else 'partial' if partial else 'unwitnessed'}
            resolved[ref] = result
            active.remove(ref)
            return result

        for ref, certificate in certificates.items():
            expected = calculate(ref)
            support = certificate['support']
            if expected['status'] != support['status'] or expected['stage'] != support['first_supported_stage']:
                errors.append({'kind': 'certificate_support', 'certificate': ref, 'observed': expected,
                               'reported_status': support['status'], 'reported_stage': support['first_supported_stage']})
        association_count, participant_count = 0, 0
        for aid, support_text in idx.execute('SELECT id,support FROM associations'):
            association_count += 1
            support = json.loads(support_text)
            members = [calculate(ref) for ref, c in certificates.items() if c['association_id'] == aid]
            stage = min((m['stage'] for m in members if m['stage'] is not None), default=None)
            status = 'witnessed' if stage is not None else 'partial' if any(m['status'] == 'partial' for m in members) else 'unwitnessed'
            if stage != support['first_supported_stage'] or status != support['status']:
                errors.append({'kind': 'association_support', 'association': aid, 'observed_stage': stage, 'observed_status': status})
            if stage is not None:
                for role, value in idx.execute('SELECT role,value FROM participants WHERE association_id=?', (aid,)):
                    f = Fraction(value)
                    node = src.execute('SELECT first_stage FROM nodes WHERE p=? AND q=?', (f.numerator, f.denominator)).fetchone()
                    participant_count += 1
                    if node is None or node[0] > stage:
                        errors.append({'kind': 'participant_not_observed', 'association': aid, 'role': role, 'value': value, 'certificate_stage': stage})
    after_source, after_index = digest(source_path), digest(index_path)
    if after_source != before_source or after_index != before_index:
        errors.append({'kind': 'input_changed_during_review'})
    return {
        'review_method': 'Independent direct SQL and exact rational arithmetic; no production evidence helpers or tests imported.',
        'scope_limit': 'Checks recorded requests, eligibility, references, dependency support and completion stages, not the mathematical sufficiency of arbitrary certificate schemas.',
        'source_path': str(Path(source_path).resolve()), 'source_sha256': before_source,
        'index_path': str(Path(index_path).resolve()), 'index_sha256': before_index,
        'auditor_sha256': digest(__file__), 'checkpoint': checkpoint,
        'association_count': association_count, 'certificates_checked': len(certificates),
        'distinct_directed_requests_checked': len(observed),
        'observed_directed_requests': sum(bool(rows) for rows in observed.values()),
        'materialized_references_checked': checked_refs,
        'witnessed_association_participant_rows_checked': participant_count,
        'inputs_unchanged': before_source == after_source and before_index == after_index,
        'errors': errors,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--index', type=Path, required=True)
    parser.add_argument('--write', type=Path, required=True)
    args = parser.parse_args()
    if args.write.exists():
        parser.error('Refusing to overwrite review artifact: ' + str(args.write))
    result = audit(args.source, args.index)
    with args.write.open('x') as output:
        json.dump(result, output, indent=2, sort_keys=True)
        output.write('\n')
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
