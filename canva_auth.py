"""
Canva OAuth Helper CLI
----------------------
Guides you through authorizing your Canva account with your registered Client ID.
Runs a local callback listener to capture the OAuth redirect.
"""

import sys
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
from pathlib import Path
from canva_client import CanvaClient

callback_data = {"code": None, "state": None, "error": None}


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        query = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(query)

        if "code" in params:
            callback_data["code"] = params["code"][0]
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            html = """
            <html>
            <body style="font-family: sans-serif; text-align: center; padding: 50px;">
                <h1 style="color: #00c4cc;">Canva Authorization Successful!</h1>
                <p>You can close this tab and return to your IDE.</p>
            </body>
            </html>
            """
            self.wfile.write(html.encode("utf-8"))
        elif "error" in params:
            callback_data["error"] = params.get("error_description", params["error"])[0]
            self.send_response(400)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"<h1>Authorization Failed</h1><p>Check terminal for details.</p>")
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass


def main():
    print("=" * 60, flush=True)
    print(" Canva OAuth 2.0 Authorization Setup", flush=True)
    print("=" * 60, flush=True)

    client = CanvaClient()
    auth_url, code_verifier, state = client.get_authorization_url()

    print(f"\nAuthorization URL generated:", flush=True)
    print(auth_url, flush=True)
    print("-" * 60, flush=True)

    # Try opening browser
    try:
        webbrowser.open(auth_url)
    except Exception:
        pass

    parsed = urllib.parse.urlparse(client.redirect_uri)
    host = parsed.hostname or "127.0.0.1"
    port = parsed.port or 8080

    print(f"Listening for OAuth callback on {client.redirect_uri} ...", flush=True)

    bind_host = "0.0.0.0" if host in ("localhost", "127.0.0.1") else host
    server = HTTPServer((bind_host, port), OAuthCallbackHandler)
    server.timeout = 180  # Wait up to 3 minutes

    while not callback_data["code"] and not callback_data["error"]:
        server.handle_request()

    server.server_close()

    if callback_data["error"]:
        print(f"\n[Error] Authorization failed: {callback_data['error']}", flush=True)
        sys.exit(1)

    code = callback_data["code"]
    if not code:
        print("\n[Error] No authorization code received within timeout.", flush=True)
        sys.exit(1)

    print(f"\nAuthorization code captured! Exchanging for tokens...", flush=True)
    try:
        tokens = client.exchange_code_for_token(code=code, code_verifier=code_verifier)
        print("\n[Success] Canva authentication complete!", flush=True)
        print("Access and Refresh tokens have been securely cached in .canva_tokens.json", flush=True)
    except Exception as e:
        print(f"\n[Error] Token exchange failed: {e}", flush=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
