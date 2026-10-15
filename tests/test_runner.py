import unittest

from hinttutor import runner

TESTS = [{"args": [2], "expected": 4}, {"args": [3], "expected": 9}]


class RunnerTests(unittest.TestCase):
    def test_all_pass(self):
        rep = runner.run_tests("def sq(n):\n    return n * n\n", "sq", TESTS)
        self.assertTrue(rep.all_passed)

    def test_wrong_answer(self):
        rep = runner.run_tests("def sq(n):\n    return n + n\n", "sq", TESTS)
        self.assertFalse(rep.all_passed)
        self.assertEqual(rep.first_failure.kind, "wrong")
        self.assertEqual(rep.n_passed, 1)  # 2+2 == 2*2

    def test_exception_has_line(self):
        rep = runner.run_tests("def sq(n):\n    return n / 0\n", "sq", TESTS)
        f = rep.first_failure
        self.assertEqual(f.kind, "exception")
        self.assertEqual(f.error_line, 2)
        self.assertIn("ZeroDivisionError", f.error)

    def test_timeout(self):
        rep = runner.run_tests("def sq(n):\n    while True:\n        pass\n", "sq", TESTS, timeout=1)
        self.assertEqual(rep.first_failure.kind, "timeout")

    def test_syntax_error_skips_execution(self):
        rep = runner.run_tests("def sq(n)\n    return n\n", "sq", TESTS)
        self.assertIsNotNone(rep.syntax_error)
        self.assertEqual(rep.syntax_error.line, 1)
        self.assertEqual(rep.results, [])

    def test_missing_function(self):
        rep = runner.run_tests("def other(n):\n    return n\n", "sq", TESTS)
        self.assertIn("NameError", rep.first_failure.error)

    def test_tuple_return_preserved(self):
        tests = [{"args": [2], "expected": (2, 4)}]
        rep = runner.run_tests("def sq(n):\n    return (n, n * n)\n", "sq", tests)
        self.assertTrue(rep.all_passed)
        self.assertEqual(rep.results[0].actual, (2, 4))

    def test_describe_failure_none_handled_gracefully(self):
        desc = runner.describe_failure("f", None)
        self.assertIn("No test failure details available", desc)

    def test_timeout_aborts_subsequent_tests_quickly(self):
        tests = [{"args": [i], "expected": i} for i in range(5)]
        rep = runner.run_tests("def f(x):\n    while True:\n        pass\n", "f", tests, timeout=0.1)
        self.assertEqual(len(rep.results), 5)
        self.assertTrue(all(r.kind == "timeout" for r in rep.results))
        # Total time should be close to 0.1s, not 5 * 0.1s
        self.assertLess(sum(r.seconds for r in rep.results), 0.4)


if __name__ == "__main__":
    unittest.main()
