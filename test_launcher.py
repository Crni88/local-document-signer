import socket
import unittest
from pathlib import Path
from unittest.mock import patch

from app import get_bundle_dir
from launcher import find_free_port, ServerThread


class LauncherTests(unittest.TestCase):
    def test_get_bundle_dir(self):
        bundle_dir = get_bundle_dir()
        self.assertIsInstance(bundle_dir, Path)
        self.assertTrue((bundle_dir / "templates").is_dir())
        self.assertTrue((bundle_dir / "static").is_dir())

    def test_find_free_port(self):
        port = find_free_port(start_port=5900)
        self.assertIsInstance(port, int)
        self.assertGreaterEqual(port, 5900)
        # Verify port can actually be bound
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("127.0.0.1", port))

    def test_server_thread_start_and_shutdown(self):
        port = find_free_port(start_port=5950)
        server_thread = ServerThread("127.0.0.1", port)
        server_thread.start()
        self.assertTrue(server_thread.is_alive())

        # Probe with socket to make sure it's listening
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(("127.0.0.1", port))

        # Shutdown cleanly
        server_thread.shutdown()
        server_thread.join(timeout=3)
        self.assertFalse(server_thread.is_alive())


if __name__ == "__main__":
    unittest.main()
