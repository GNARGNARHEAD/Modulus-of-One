from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

from moo.constructionist_math import Graph, SpeculativeOperandError, eval_moo


class ExpressionConfirmationTests(unittest.TestCase):
    def test_first_fan_does_not_confirm_two(self) -> None:
        graph, two = eval_moo("1+1")
        self.assertEqual(graph.numeric_value(two), (2, 1))
        self.assertEqual(two.status, "S")
        self.assertEqual(sorted(graph.nodes_by_int), [1])

    def test_all_integer_results_wait_for_recurrence(self) -> None:
        for expression, value in (("(1+1)+(1+1)", 4),
                                  ("(1+1)*(1+1)", 4),
                                  ("1-1", 0)):
            with self.subTest(expression=expression):
                graph = Graph()
                graph.advance_frontier_max_to(2)
                _, result = eval_moo(expression, graph=graph)
                self.assertEqual(graph.numeric_value(result), (value, 1))
                self.assertEqual(result.status, "S")
                self.assertEqual(sorted(graph.nodes_by_int), [1, 2])

    def test_unconfirmed_integer_cannot_be_reused(self) -> None:
        graph = Graph()
        graph.advance_frontier_max_to(2)
        with self.assertRaises(SpeculativeOperandError):
            eval_moo("((1+1)*(1+1))+1", graph=graph)
        self.assertEqual(sorted(graph.nodes_by_int), [1, 2])
        self.assertEqual(graph.nodes_by_value[(4, 1)].status, "S")
        self.assertNotIn((5, 1), graph.nodes_by_value)

    def test_explicit_recurrence_preserves_the_earlier_product_witness(self) -> None:
        graph = Graph()
        graph.advance_frontier_max_to(2)
        _, four = eval_moo("(1+1)*(1+1)", graph=graph)
        product = graph.edges[-1]
        graph.advance_frontier_max_to(4)
        self.assertIs(graph.get_or_create_ref(4), four)
        self.assertIs(product.output, four)
        self.assertIn(product, graph.edges)
        self.assertEqual(product.metadata["result"], "speculative")
        _, five = eval_moo("((1+1)*(1+1))+1", graph=graph)
        self.assertEqual(five.status, "S")
        self.assertEqual(sorted(graph.nodes_by_int), [1, 2, 3, 4])

    def test_promotion_cannot_skip_recurrence(self) -> None:
        graph = Graph()
        with self.assertRaises(ValueError):
            graph.promote_core_iteration(4)
        self.assertEqual(sorted(graph.nodes_by_int), [1])

    def test_fraction_stays_speculative_even_after_further_recurrence(self) -> None:
        graph = Graph()
        graph.advance_frontier_max_to(4)
        _, half = eval_moo("1/(1+1)", graph=graph)
        self.assertEqual(graph.numeric_value(half), (1, 2))
        self.assertEqual(half.status, "S")
        with self.assertRaises(SpeculativeOperandError):
            eval_moo("(1/(1+1))+1", graph=graph)

    def test_exploratory_operand_option_does_not_confer_confirmation(self) -> None:
        graph, five = eval_moo("((1+1)*(1+1))+1", allow_speculative_operands=True)
        self.assertEqual(graph.numeric_value(five), (5, 1))
        self.assertEqual(five.status, "S")
        self.assertEqual(sorted(graph.nodes_by_int), [1])

    def test_cli_requires_explicit_confirmation_for_nested_expression(self) -> None:
        denied = subprocess.run([sys.executable, "-m", "moo.constructionist_math", "1/(1+1)"],
                                capture_output=True, text=True)
        self.assertNotEqual(denied.returncode, 0)
        self.assertIn("speculative", denied.stderr)
        allowed = subprocess.run(
            [sys.executable, "-m", "moo.constructionist_math", "--confirm-through", "2", "1/(1+1)"],
            capture_output=True, text=True,
        )
        self.assertEqual(allowed.returncode, 0, allowed.stderr)
        self.assertIn("# RESULT\nS(1/2)", allowed.stdout)


if __name__ == "__main__":
    unittest.main()
