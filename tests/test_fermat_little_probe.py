from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from moo.fermat_little_probe import fermat_little_probe


class FermatLittleProbeTests(unittest.TestCase):
    def test_missing_corpus_is_not_created_by_probe(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "missing.sqlite"
            with self.assertRaises(SystemExit):
                fermat_little_probe(
                    db_path=db_path,
                    min_modulus=2,
                    max_modulus=2,
                    min_base=1,
                    max_base=1,
                    top_k=1,
                    edge_limit=1,
                )
            self.assertFalse(db_path.exists())


if __name__ == "__main__":
    unittest.main()
