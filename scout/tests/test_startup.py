import socket
import sys
import unittest
from http.server import BaseHTTPRequestHandler
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from startup import bind_server


class StartupTests(unittest.TestCase):
    def test_occupied_port_fails_or_falls_back(self):
        with socket.socket() as occupied:
            occupied.bind(('127.0.0.1', 0))
            occupied.listen()
            port = occupied.getsockname()[1]
            with self.assertRaises(OSError):
                bind_server(BaseHTTPRequestHandler, port)
            with bind_server(BaseHTTPRequestHandler, port, auto_port=True) as server:
                self.assertGreater(server.server_port, port)
                self.assertLessEqual(server.server_port, port + 20)
                self.assertEqual(server.server_address[0], '127.0.0.1')

    def test_invalid_port(self):
        for port in (-1, 0, 65536):
            with self.assertRaises(ValueError):
                bind_server(BaseHTTPRequestHandler, port)


if __name__ == '__main__':
    unittest.main()
