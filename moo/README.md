# Python Tools

Run commands from the repository root with `python3 -m moo.<module>`.
No package installation is required for the standard-library runtime and
tests. See the [development guide](../docs/software/DEVELOPMENT.md).

| Purpose | Entry points or shared code |
| --- | --- |
| Selected expressions and in-memory graph | [constructionist_math.py](constructionist_math.py) |
| Full positive-spine field | [strict_stage_moo.py](strict_stage_moo.py), [graph_corpus.py](graph_corpus.py) |
| Read-only graph inspection | [graph_query.py](graph_query.py), [graph_evidence.py](graph_evidence.py), [core_alignment_check.py](core_alignment_check.py) |
| Node associations and certificates | [node_profiles.py](node_profiles.py), [association_families.py](association_families.py), [profile_certificates.py](profile_certificates.py) |
| Shared measurements and report support | [graph_invariants.py](graph_invariants.py), [rational_baselines.py](rational_baselines.py), [research_utils.py](research_utils.py) |
| Geometry, arithmetic, route and convergence probes | The [research program cards](../research/README.md) identify each instrument, tests and evidence. |
| Earlier closure and ledger instruments | [legacy/](legacy/README.md) |

The [runtime reference](../docs/software/RUNTIME.md) and
[corpus contract](../docs/software/GRAPH_CORPUS.md) describe the two construction
interfaces. Maintained research scripts with a single domain owner stay beside
their program under `research/`; the reusable instruments live here.

Historical reports keep their original tool/schema names and source hashes.
A module move changes source identity; it does not relabel an old run as a new
reproduction. The [layout record](../archive/reorganizations/20261107/README.md)
maps former paths to their current homes.
