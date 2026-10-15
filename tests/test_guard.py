import unittest

from hinttutor import guard

REF = "def sum_to_n(n):\n    total = 0\n    for i in range(1, n + 1):\n        total += i\n    return total\n"
BUG = REF.replace("n + 1", "n")


class GuardTests(unittest.TestCase):
    def setUp(self):
        self.fix = guard.compute_fix(BUG, REF)

    def test_clean_hint_passes(self):
        v = guard.check("Look at line 3. Does your loop ever reach n itself? Try n = 2 by hand.", self.fix)
        self.assertTrue(v.ok, v)

    def test_code_block_rejected(self):
        v = guard.check("Try this:\n```python\nfor i in range(1, n):\n```", self.fix)
        self.assertIn("code_block", v.reasons)

    def test_fix_line_rejected(self):
        v = guard.check("Your line should read: for i in range(1, n + 1):", self.fix)
        self.assertFalse(v.ok)
        self.assertIn("fix_line", v.reasons)

    def test_fix_expression_rejected_with_spacing_variants(self):
        for text in ("Change the bound to n + 1.", "Use n+1 instead.", "Add +1 to the upper bound."):
            v = guard.check(text, self.fix)
            self.assertIn("fix_expression", v.reasons, text)

    def test_reasons_do_not_contain_fix_text(self):
        v = guard.check("Use n + 1 here.", self.fix)
        self.assertNotIn("+", " ".join(v.reasons))
        self.assertTrue(v.detail)  # fix text lives only in detail

    def test_empty_rejected(self):
        self.assertFalse(guard.check("   ", self.fix).ok)

    def test_operator_swap_candidates(self):
        ref = "def f(x):\n    if x >= 0:\n        return 1\n    return 0\n"
        bug = ref.replace(">=", ">")
        fix = guard.compute_fix(bug, ref)
        self.assertIn("fix_expression", guard.check("Should it be >= instead?", fix).reasons)
        self.assertTrue(guard.check("Check the comparison on line 2 against x = 0.", fix).ok)

    def test_broad_diff_uses_relaxed_rules(self):
        ref = "def f(x):\n" + "".join("    a%d = x + %d\n" % (i, i) for i in range(8)) + "    return a0\n"
        student = "def f(x):\n    return x\n"
        fix = guard.compute_fix(student, ref)
        self.assertTrue(fix.broad)
        self.assertEqual(fix.candidates, [])
        self.assertTrue(guard.check("Use x + 3 somewhere.", fix).ok)           # token rule off
        self.assertFalse(guard.check("Write a0 = x + 0 first.", fix).ok)        # exact reference line
        self.assertFalse(guard.check("```\ncode\n```", fix).ok)                 # fence rule still on

    def test_identical_code_only_fence_rule(self):
        fix = guard.compute_fix(REF, REF)
        self.assertTrue(guard.check("Trace it by hand.", fix).ok)


if __name__ == "__main__":
    unittest.main()
