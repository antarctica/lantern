# Preview local site with CORS support

import csv
import ssl
from base64 import b64encode
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import cast
from urllib.parse import urlparse

import trustme

BASIC_AUTH_PATH = "/-/items/"
BASIC_AUTH_CREDENTIAL = "guest"
REDIRECTS = {}
MEDIA_TYPES = {
    "/static/json/api-catalog.json": "application/linkset+json",
    "/static/json/health.json": "application/health+json",
}


class RequestHandler(SimpleHTTPRequestHandler):
    """
    Request handler for development server.

    Includes:
    - permissive CORS support (JS HTTP clients)
    - blocking unsupported HTTP methods (OpenAPI schema validation)
    - returning redirects
    - overriding media types
    - requiring basic auth for protected paths
    """

    def __init__(self, *args, **kwargs) -> None:  # noqa: ANN002, ANN003
        """Initialise basic server with support for basic auth."""
        username = kwargs.pop("username", BASIC_AUTH_CREDENTIAL)
        password = kwargs.pop("password", BASIC_AUTH_CREDENTIAL)
        self._auth = b64encode(f"{username}:{password}".encode()).decode()
        super().__init__(*args, **kwargs)

    def end_headers(self) -> None:
        """Include permissive CORS."""
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS, PATCH")
        self.send_header(
            "Access-Control-Allow-Headers", "Origin, X-Requested-With, Content-Type, Accept, Authorization"
        )
        super().end_headers()

    def _unsupported_method(self) -> None:
        """
        Return 405 Method Not Allowed for unsupported methods.

        As expected by schemathesis.
        """
        self.send_response(405, "Method Not Allowed")
        self.send_header("Allow", "HEAD, GET, OPTIONS")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _redirect(self) -> bool:
        """
        Handle redirects.

        Returns True if redirect was sent.

        Content-Type header set to comply with OpenAPI spec as redirects return fallback HTML for meta redirects.
        """
        if self.path not in REDIRECTS:
            return False

        target = REDIRECTS[self.path]
        # Convert relative URLs to absolute URLs to match OpenAPI spec requirements
        if target.startswith("/"):
            # Use Host header from request, fallback to server address if not present
            host = self.headers.get("Host")
            if not host:
                addr = cast("tuple[str, int]", self.server.server_address)
                host = f"{addr[0]}:{addr[1]}"
            target = f"https://{host}{target}"

        self.send_response(301, "Moved Permanently")
        self.send_header("Location", target)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", "0")
        self.end_headers()
        return True

    def _basic_auth(self) -> bool:
        """
        Handle basic auth.

        Returns True if the request does not need authentication.
        """
        if BASIC_AUTH_PATH not in self.path:
            return True

        if self.headers.get("Authorization") is None:
            self.do_HEAD_unauthorised()
            self.wfile.write(b"No auth header - unauthorised.")
            return False
        if self.headers.get("Authorization") == "Basic " + self._auth:
            return True

        self.do_HEAD_forbidden()
        self.wfile.write(b"Invalid credentials - forbidden.")
        return False

    def send_header(self, keyword: str, value: str) -> None:
        """Override Content-Type header for specific paths."""
        if keyword.lower() == "content-type" and self.path in MEDIA_TYPES:
            value = MEDIA_TYPES[self.path]
        super().send_header(keyword, value)

    def do_TRACE(self) -> None:
        """Return 405 Method Not Allowed for TRACE requests."""
        self._unsupported_method()

    def do_QUERY(self) -> None:
        """Return 405 Method Not Allowed for QUERY requests."""
        self._unsupported_method()

    def do_PUT(self) -> None:
        """Return 405 Method Not Allowed for PUT requests."""
        self._unsupported_method()

    def do_POST(self) -> None:
        """Return 405 Method Not Allowed for POST requests."""
        self._unsupported_method()

    def do_PATCH(self) -> None:
        """Return 405 Method Not Allowed for PATCH requests."""
        self._unsupported_method()

    def do_DELETE(self) -> None:
        """Return 405 Method Not Allowed for DELETE requests."""
        self._unsupported_method()

    def do_GET(self) -> None:
        """Handle GET requests with redirect and media type override support."""
        if not self._basic_auth():
            return
        if not self._redirect():
            super().do_GET()

    def do_HEAD(self) -> None:
        """Handle HEAD requests with redirect and media type override support."""
        if not self._basic_auth():
            return
        if not self._redirect():
            super().do_HEAD()

    def do_HEAD_unauthorised(self) -> None:
        """Send 401 unauthorised response."""
        self.send_response(401)
        self.send_header("WWW-Authenticate", 'Basic realm="Test"')
        self.send_header("Content-type", "text/html")
        self.end_headers()

    def do_HEAD_forbidden(self) -> None:
        """Send 403 forbidden response."""
        self.send_response(403)
        self.send_header("Content-type", "text/html")
        self.end_headers()

    def do_OPTIONS(self) -> None:
        """Handle preflight requests."""
        self.send_response(200, "OK")
        self.end_headers()


def _load_redirects(base_path: Path) -> None:
    """Populate REDIRECTS from RedirectsOutput CSV."""
    redirects_path = base_path / "-" / "redirects.csv"
    if not redirects_path.exists():
        return

    REDIRECTS.clear()
    with redirects_path.open() as f:
        redirects = csv.DictReader(f)
        for r in redirects:
            source = f"/{r['source']}"
            REDIRECTS[source] = urlparse(r["target"]).path


def run(
    host: str = "127.0.0.1",
    port: int = 9000,
    raw_path: str = "./export",
    username: str = BASIC_AUTH_CREDENTIAL,
    password: str = BASIC_AUTH_CREDENTIAL,
) -> None:
    """
    Run development server with HTTPS support.

    Note: Where host is `127.0.0.1`, `localhost` is used for compatibility with Font Awesome icon kits.
    """
    host_display = "localhost" if host == "127.0.0.1" else host
    path = Path(raw_path)
    handler = partial(RequestHandler, directory=path, username=username, password=password)
    _load_redirects(base_path=path)

    # Create self-signed certificate using trustme
    ca = trustme.CA()
    server_cert = ca.issue_cert(host_display)

    # Create SSL context
    ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    server_cert.configure_cert(ssl_context)

    with ThreadingHTTPServer((host, port), handler) as httpd:
        httpd.socket = ssl_context.wrap_socket(httpd.socket, server_side=True)
        print(f"- serving {path.resolve()} at https://{host_display}:{port}")
        print(f"- loaded {len(REDIRECTS)} redirects")
        print(f"- using {len(MEDIA_TYPES)} extra content-type mappings")
        print(
            f"- use username '{username}' and password '{password}' to access restricted content under '{BASIC_AUTH_PATH}'"
        )
        print("- ⚠️ using self-signed certificate which will see security warnings in clients")
        if not path.joinpath("-/items").is_dir():
            print(
                f"\n**Note:** Run `ln -s ../../export-trusted/items items` or similar from `{path.resolve()}/-` to simulate reverse proxy."
            )

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("Keyboard interrupt received, exiting.")


if __name__ == "__main__":
    run()
