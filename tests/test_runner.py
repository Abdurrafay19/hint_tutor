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

    def test_student_print_does_not_break_output(self):
        rep = runner.run_tests("def sq(n):\n    print('debug')\n    return n * n\n", "sq", TESTS)
        self.assertTrue(rep.all_passed)


if __name__ == "__main__":
    unittest.main()
