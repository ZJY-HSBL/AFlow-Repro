"""Proof that upstream lax XML acceptance needs an additional structural gate."""
import unittest

from scripts.formatter import XmlFormatter
from scripts.optimizer import GraphOptimize
from tools.validate_workflow_proposal import validate_graph_proposal


class ProposalValidationTests(unittest.TestCase):
    def test_missing_optional_fields_accepted_by_upstream_xml_but_rejected_by_gate(self):
        valid, response = XmlFormatter.from_model(GraphOptimize).validate_response(
            "<graph>class Workflow:\n    pass</graph>"
        )
        self.assertTrue(valid)
        self.assertFalse(validate_graph_proposal(response)["accepted"])
        self.assertTrue(any("modification" in e for e in validate_graph_proposal(response)["reasons"]))

    def test_compiled_graph_without_valid_prompt_rejected(self):
        sample = {"modification": "fixture",
                  "graph": "class Workflow:\n    pass",
                  "prompt": "plain natural language without Python syntax!"}
        verdict = validate_graph_proposal(sample)
        self.assertFalse(verdict["accepted"])
        self.assertTrue(any("prompt Python" in x for x in verdict["reasons"]))

    def test_valid_structural_workflow(self):
        response = {"modification": "Add direct generation operator",
                    "graph": "class Workflow:\n    def __init__(self):\n        pass",
                    "prompt": "# Prompt module is a valid Python file\n"}
        result = validate_graph_proposal(response)
        self.assertTrue(result["accepted"])
        self.assertEqual(result["reasons"], [])

    def test_graph_without_workflow_fails(self):
        response = {"modification": "test", "graph": "class Other:\n    pass",
                    "prompt": "VALUE = 'valid'"}
        self.assertFalse(validate_graph_proposal(response)["accepted"])


if __name__ == "__main__":
    unittest.main()
