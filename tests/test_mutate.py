import unittest

from eval import mutate
from hinttutor import assignment, runner


class MutateTests(unittest.TestCase):
    def test_every_assignment_yields_failing_mutants_with_aligned_lines(self):
        for name in assignment.list_assignments():
            asg = assignment.load(name)
            mutants = mutate.generate(asg)
            self.assertGreaterEqual(len(mutants), 3, name)
            for m in mutants:
                rep = runner.run_tests(m["code"], asg.function, asg.tests, 2)
                self.assertFalse(rep.all_passed)
                self.assertLessEqual(m["line"], len(m["code"].splitlines()))


if __name__ == "__main__":
    unittest.main()
