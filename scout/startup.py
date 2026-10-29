"""Bind a local server without sharing an occupied Windows port."""
import errno
import os
import socket
from http.server import ThreadingHTTPServer


class LocalServer(ThreadingHTTPServer):
    allow_reuse_address = os.name != 'nt'
    allow_reuse_port = False

    def server_bind(self):
        if os.name == 'nt':
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        super().server_bind()


def bind_server(handler, port, auto_port=False):
    if not 1 <= port <= 65535:
        raise ValueError('Port must be between 1 and 65535.')
    last = min(port + 20, 65535) if auto_port else port
    for candidate in range(port, last + 1):
        try:
            return LocalServer(('127.0.0.1', candidate), handler)
        except OSError as exc:
            occupied = exc.errno in (errno.EADDRINUSE, errno.EACCES) or getattr(exc, 'winerror', None) in (10048, 10013)
            if not occupied:
                raise
            if candidate == last:
                raise OSError(f'Cannot use ports {port}–{last}. Choose another --port.') from exc
            print(f'Port {candidate} is unavailable; trying {candidate + 1}...', flush=True)
