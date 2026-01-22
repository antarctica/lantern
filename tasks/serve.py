from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


class CORSRequestHandler(SimpleHTTPRequestHandler):
    """SimpleHTTPRequestHandler that injects CORS headers for development."""

    def end_headers(self) -> None:
        """Configure CORS permissively."""
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS, PATCH")
        self.send_header(
            "Access-Control-Allow-Headers", "Origin, X-Requested-With, Content-Type, Accept, Authorization"
        )
        super().end_headers()

    def do_OPTIONS(self) -> None:
        """Handle preflight requests."""
        self.send_response(200, "OK")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS, PATCH")
        self.send_header(
            "Access-Control-Allow-Headers", "Origin, X-Requested-With, Content-Type, Accept, Authorization"
        )
        self.send_header("Content-Length", "0")
        self.end_headers()


def run(host: str = "127.0.0.1", port: int = 9000, directory: str = "./export") -> None:
    """Run simple development server."""
    handler = partial(CORSRequestHandler, directory=directory)
    with ThreadingHTTPServer((host, port), handler) as httpd:
        dir_path = Path(directory)
        print(f"Serving directory {dir_path.resolve()} at http://{host}:{port}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("Keyboard interrupt received, exiting.")


if __name__ == "__main__":
    run()
