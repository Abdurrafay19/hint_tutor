import json
import unittest
from unittest import mock

from hinttutor import assignment, pipeline
from hinttutor.llm import LLMError, LLMResult

ASG = assignment.load("sum_to_n")
BUGGY = ASG.buggy_example
DIAG = json.dumps({"line": 3, "bug_type": "off_by_one", "reason": "loop stops one short"})


def reply(text):
    return LLMResult(text=text, seconds=0.01, model="fake")


class PipelineTests(unittest.TestCase):
    def test_passing_code_makes_no_model_call(self):
        with mock.patch("hinttutor.llm.chat") as chat:
            res = pipeline.run(ASG, ASG.reference_code)
        self.assertEqual(res.status, "passed")
        chat.assert_not_called()

    def test_syntax_error_makes_no_model_call(self):
        with mock.patch("hinttutor.llm.chat") as chat:
            res = pipeline.run(ASG, "def sum_to_n(n)\n    return n\n")
        self.assertEqual(res.status, "syntax_error")
        self.assertIn("line 1", res.message)
        chat.assert_not_called()

    def test_first_attempt_accepted(self):
        with mock.patch("hinttutor.llm.chat", side_effect=[reply(DIAG), reply("Check line 3. Does the loop reach n?")]):
            res = pipeline.run(ASG, BUGGY)
        self.assertEqual(res.status, "hint")
        self.assertFalse(res.hint.used_fallback)
        self.assertEqual(len(res.hint.attempts), 1)
        self.assertEqual(res.diagnosis.line, 3)

    def test_guard_rejects_then_accepts(self):
        bad, good = reply("Use range(1, n + 1)."), reply("Look at line 3. What is the last value of i?")
        with mock.patch("hinttutor.llm.chat", side_effect=[reply(DIAG), bad, good]) as chat:
            res = pipeline.run(ASG, BUGGY)
        self.assertEqual([a.ok for a in res.hint.attempts], [False, True])
        self.assertEqual(res.message, "Look at line 3. What is the last value of i?")
        retry_prompt = chat.call_args_list[2].args[1]
        self.assertIn("rejected", retry_prompt)
        self.assertNotIn("n + 1", retry_prompt.split("rejected")[1])  # retry prompt must not leak the fix

    def test_three_rejections_use_fallback(self):
        bad = reply("Change it to n + 1.")
        with mock.patch("hinttutor.llm.chat", side_effect=[reply(DIAG), bad, bad, bad]):
            res = pipeline.run(ASG, BUGGY)
        self.assertTrue(res.hint.used_fallback)
        self.assertEqual(len(res.hint.attempts), 3)
        self.assertIn("Look at line 3", res.message)

    def test_invalid_diagnosis_line_retried_then_fallback(self):
        bad = reply(json.dumps({"line": 99, "bug_type": "other", "reason": "x"}))
        with mock.patch("hinttutor.llm.chat", side_effect=[bad, bad]):
            res = pipeline.run(ASG, BUGGY)
        self.assertIsNone(res.diagnosis)
        self.assertTrue(res.hint.used_fallback)

    def test_ollama_down_reports_llm_error(self):
        with mock.patch("hinttutor.llm.chat", side_effect=LLMError("connection refused")):
            res = pipeline.run(ASG, BUGGY)
        self.assertEqual(res.status, "llm_error")


if __name__ == "__main__":
    unittest.main()
