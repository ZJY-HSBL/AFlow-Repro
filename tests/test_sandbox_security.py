"""Safe execution policy tests: do not require Docker daemon."""
import unittest

from tools.sandbox_mbpp import docker_command


class SecurityContractTests(unittest.TestCase):
    def test_sandbox_has_network_and_privilege_restrictions(self):
        command = docker_command()
        self.assertIn("--network=none", command)
        self.assertIn("--read-only", command)
        self.assertIn("--cap-drop=ALL", command)
        self.assertIn("--security-opt=no-new-privileges", command)
        self.assertIn("--pids-limit=32", command)
        self.assertIn("--user=65534:65534", command)
        self.assertEqual(command[-3:-1], ["-S", "-c"])


if __name__ == "__main__":
    unittest.main()
