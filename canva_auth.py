"""
Canva OAuth Helper CLI
----------------------
Guides you through authorizing your Canva account with your registered Client ID.
Runs a local callback listener or allows manual code pasting.
"""

import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
from canva_client import CanvaClient

callback_data = {"code": None, "state": None, "error": None}


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        query = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(query)

        if "code" in params:
            callback_data["code"] = params["code"][0]
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(b"<h1>Canva Authorization Successful!</h1><p>You can close this tab and return to your terminal.</p>")
        elif "error" in params:
            callback_data["error"] = params.get("error_description", params["error"])[0]
            self.send_response(400)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(b"<h1>Authorization Failed</h1><p>Check terminal for details.</p>")
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        # Suppress server request logging
        pass


def main():
    print("=" * 60)
    print(" Canva OAuth 2.0 Authorization Setup")
    print("=" * 60)

    client = CanvaClient()
    auth_url, code_verifier, state = client.get_authorization_url()

    print(f"\n1. In your Canva Developer Portal, make sure your Redirect URI is set to:")
    print(f"   http://127.0.0.1:8080/oauth/callback\n")
    print(f"2. Opening Canva authorization page in your browser...")
    print(f"   (If it doesn't open automatically, copy and paste this URL into your browser):\n")
    print(auth_url)
    print("\n" + "-" * 60)

    webbrowser.open(auth_url)

    # Attempt to start temporary local callback server
    try:
        server = HTTPServer(("127.0.0.1", 8080), OAuthCallbackHandler)
        print("Waiting for callback on http://127.0.0.1:8080/oauth/callback ...")
        # Handle single request
        server.handle_request()
        server.server_close()
    except Exception as e:
        print(f"Local server note: {e}")

    code = callback_data.get("code")
    if not code:
        print("\nIf the callback did not redirect automatically, please paste the full redirect URL or the 'code' parameter here:")
        user_input = input("Code or URL: ").strip()
        if "code=" in user_input:
            code = urllib.parse.parse_qs(urllib.parse.urlparse(user_input).query).get("code", [None])[0]
        else:
            code = user_input

    if not code:
        print("[Error] No authorization code received.")
        return

    print("\nExchanging authorization code for access tokens...")
    try:
        tokens = client.exchange_code_for_token(code=code, code_verifier=code_verifier)
        print("\n[Success] Canva authentication complete!")
        print(f"Tokens securely cached in: .canva_tokens.json (git-ignored)")
    except Exception as e:
        print(f"\n[Error] Token exchange failed: {e}")


if __name__ == "__main__":
    main()
