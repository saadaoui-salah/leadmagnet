"""
Standalone MITM Proxy Server — forwards all traffic through an upstream proxy.

Usage:
    python run_mitm.py

    # Or with custom upstream proxy:
    python run_mitm.py --upstream http://user:pass@host:port

    # Or with custom port:
    python run_mitm.py --port 8080

Upstream proxy format:
    http://username:password@host:port
"""

import socket
import select
import threading
import argparse
import base64
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


class ProxyHandler(BaseHTTPRequestHandler):
    """HTTP proxy handler that forwards through upstream proxy."""

    upstream_proxy = None

    def log_message(self, format, *args):
        logger.debug(format, *args)

    def do_CONNECT(self):
        """Handle HTTPS CONNECT tunneling."""
        try:
            host, port = self.path.split(":")
            port = int(port)
        except ValueError:
            self.send_error(400, "Bad CONNECT path")
            return

        upstream = self.upstream_proxy
        if upstream:
            # Connect through upstream proxy
            try:
                remote = socket.create_connection(
                    (upstream["host"], upstream["port"]), timeout=30
                )
                # Authenticate with upstream proxy
                auth = base64.b64encode(
                    f"{upstream['username']}:{upstream['password']}".encode()
                ).decode()
                connect_req = (
                    f"CONNECT {host}:{port} HTTP/1.1\r\n"
                    f"Host: {host}:{port}\r\n"
                    f"Proxy-Authorization: Basic {auth}\r\n"
                    f"\r\n"
                )
                remote.sendall(connect_req.encode())
                resp = remote.recv(4096)
                if b"200" not in resp.split(b"\r\n")[0]:
                    self.send_error(502, "Upstream CONNECT failed")
                    return
            except Exception as e:
                logger.error("Upstream connect failed: %s", e)
                self.send_error(502, f"Upstream connect failed: {e}")
                return
        else:
            # Direct connection
            try:
                remote = socket.create_connection((host, port), timeout=30)
            except Exception as e:
                self.send_error(502, f"Cannot connect to {host}:{port}")
                return

        # Send 200 to client
        self.send_response(200, "Connection Established")
        self.end_headers()

        # Tunnel data
        self._tunnel(self.connection, remote)

    def do_GET(self):
        self._forward("GET")

    def do_POST(self):
        self._forward("POST")

    def do_PUT(self):
        self._forward("PUT")

    def do_DELETE(self):
        self._forward("DELETE")

    def do_PATCH(self):
        self._forward("PATCH")

    def do_HEAD(self):
        self._forward("HEAD")

    def do_OPTIONS(self):
        self._forward("OPTIONS")

    def _forward(self, method):
        """Forward HTTP request through upstream proxy."""
        url = self.path
        if not url.startswith("http"):
            url = f"http://{self.headers.get('Host', 'localhost')}{self.path}"

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length else None

        try:
            import http.client

            parsed = urlparse(url)
            host = parsed.hostname
            port = parsed.port or 80

            upstream = self.upstream_proxy
            if upstream:
                conn = http.client.HTTPConnection(
                    upstream["host"], upstream["port"], timeout=30
                )
                conn.set_tunnel(host, port)
                auth = base64.b64encode(
                    f"{upstream['username']}:{upstream['password']}".encode()
                ).decode()
                headers = dict(self.headers)
                headers["Proxy-Authorization"] = f"Basic {auth}"
            else:
                conn = http.client.HTTPConnection(host, port, timeout=30)
                headers = dict(self.headers)

            path = parsed.path or "/"
            if parsed.query:
                path += f"?{parsed.query}"

            conn.request(method, path, body=body, headers=headers)
            resp = conn.getresponse()

            self.send_response(resp.status, resp.reason)
            for h, v in resp.getheaders():
                if h.lower() not in ("transfer-encoding", "connection"):
                    self.send_header(h, v)
            self.end_headers()
            self.wfile.write(resp.read())
            conn.close()

        except Exception as e:
            logger.error("Forward failed: %s", e)
            self.send_error(502, f"Forward failed: {e}")

    def _tunnel(self, client, remote):
        """Bidirectional data tunnel."""
        sockets = [client, remote]
        while True:
            readable, _, exceptional = select.select(sockets, [], sockets, 30)
            if exceptional or not readable:
                break
            for sock in readable:
                try:
                    data = sock.recv(8192)
                    if not data:
                        return
                    if sock is client:
                        remote.sendall(data)
                    else:
                        client.sendall(data)
                except Exception:
                    return
        remote.close()


def parse_proxy(proxy_str):
    """Parse proxy string: http://user:pass@host:port"""
    if not proxy_str:
        return None

    if not proxy_str.startswith("http"):
        proxy_str = f"http://{proxy_str}"

    parsed = urlparse(proxy_str)
    return {
        "username": parsed.username or "",
        "password": parsed.password or "",
        "host": parsed.hostname,
        "port": parsed.port or 80,
    }


def test_upstream(upstream):
    """Test connection to upstream proxy."""
    logger.info("Testing connection to %s:%d...", upstream["host"], upstream["port"])
    try:
        s = socket.create_connection((upstream["host"], upstream["port"]), timeout=10)
        logger.info("✓ TCP connection successful")

        # Try HTTP CONNECT
        auth = base64.b64encode(
            f"{upstream['username']}:{upstream['password']}".encode()
        ).decode()
        connect_req = (
            f"CONNECT httpbin.org:443 HTTP/1.1\r\n"
            f"Host: httpbin.org:443\r\n"
            f"Proxy-Authorization: Basic {auth}\r\n"
            f"\r\n"
        )
        s.sendall(connect_req.encode())
        resp = s.recv(4096)
        status_line = resp.split(b"\r\n")[0].decode()
        logger.info("✓ HTTP CONNECT response: %s", status_line)
        s.close()
        return "200" in status_line
    except Exception as e:
        logger.error("✗ Connection failed: %s", e)
        return False


def main():
    parser = argparse.ArgumentParser(description="MITM Proxy Server")
    parser.add_argument(
        "--port", type=int, default=8080, help="Local proxy port (default: 8080)"
    )
    parser.add_argument(
        "--upstream",
        type=str,
        default=None,
        help="Upstream proxy: http://user:pass@host:port",
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Test upstream proxy connection and exit",
    )
    args = parser.parse_args()

    upstream = parse_proxy(args.upstream)

    if args.test:
        if not upstream:
            logger.error("No upstream proxy specified")
            return
        test_upstream(upstream)
        return

    ProxyHandler.upstream_proxy = upstream
    server = HTTPServer(("127.0.0.1", args.port), ProxyHandler)

    logger.info("MITM proxy started on 127.0.0.1:%d", args.port)
    if upstream:
        logger.info("Upstream: %s@%s:%d", upstream["username"], upstream["host"], upstream["port"])
    else:
        logger.info("No upstream proxy (direct connection)")

    logger.info("Press Ctrl+C to stop")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()
        logger.info("MITM proxy stopped")


if __name__ == "__main__":
    main()
