import json
import tempfile
import unittest
from pathlib import Path

from evlop.cli import main
from evlop.feynman import generate_feynman_blueprint


class TestFeynmanFirstPrinciplesEngine(unittest.TestCase):
    def test_feynman_blueprint_deconstructs_three_unseen_domains(self):
        bp_expr = generate_feynman_blueprint("Build expression evaluator with operator precedence and short-circuit boolean logic")
        self.assertIn("right-associative", bp_expr.first_principles_invariant)
        self.assertEqual(len(bp_expr.minimal_counter_examples), 3)

        bp_ring = generate_feynman_blueprint("Implement consistent hash ring with virtual nodes and replica placement")
        self.assertIn("DISTINCT physical", bp_ring.first_principles_invariant)

        bp_stream = generate_feynman_blueprint("Implement stateful TCP byte-stream frame decoder across fragmented chunks")
        self.assertIn("arbitrary", bp_stream.first_principles_invariant)

    def test_cli_feynman_command_and_gene_distillation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            main(["init"], root_dir=root)
            rc = main(
                [
                    "feynman",
                    "Implement consistent hash ring with virtual nodes and replica placement",
                    "--distill-gene",
                ],
                root_dir=root,
            )
            self.assertEqual(rc, 0)
            genes = json.loads((root / ".evlop" / "genes.json").read_text(encoding="utf-8"))
            self.assertTrue(any("Feynman Mental Model" in g["title"] for g in genes))


if __name__ == "__main__":
    unittest.main()
