"""Offline smoke checks for the CPU inference CLI; do not download models."""
import unittest

from tools.run_mbpp_cpu import DirectModelAgent


class StubAdapter:
    async def call_with_format(self, prompt, formatter):
        valid, answer = formatter.validate_response(
            "def square(x):\n    return x * x"
        )
        assert valid, answer
        return answer


class ModelAgentTest(unittest.IsolatedAsyncioTestCase):
    async def test_uses_original_code_generator_operator(self):
        # No HF dependencies; checks the actual AFlow CustomCodeGenerate interface.
        agent = DirectModelAgent(StubAdapter())
        # DirectModelAgent calls get_usage_summary only on the original adapter
        # when returning metadata; stub needs the same reporting protocol.
        agent.model.get_usage_summary = lambda: {"total_cost": 0.0}
        answer, cost = await agent("Write square(x)", "square")
        self.assertIn("def square", answer)
        self.assertEqual(cost, 0.0)


if __name__ == "__main__":
    unittest.main()
