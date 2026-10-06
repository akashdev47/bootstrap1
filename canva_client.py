"""
Canva Connect API Client
------------------------
Provides methods to authenticate with Canva, inspect designs, and export designs as MP4 videos.
Credentials are automatically read from the local protected .env file.
"""

import os
import time
import json
import base64
import hashlib
import secrets
import urllib.parse
from typing import Optional, Dict, Any, List
from pathlib import Path
import requests
from dotenv import load_dotenv

load_dotenv()

TOKEN_CACHE_FILE = Path(".canva_tokens.json")


class CanvaClient:
    """Client for Canva Connect REST API."""

    AUTH_URL = "https://www.canva.com/api/oauth/authorize"
    TOKEN_URL = "https://api.canva.com/rest/v1/oauth/token"
    API_BASE = "https://api.canva.com/rest/v1"

    DEFAULT_SCOPES = [
        "design:content:read",
        "design:meta:read",
        "profile:read",
    ]

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        redirect_uri: Optional[str] = None,
    ):
        self.client_id = client_id or os.getenv("CANVA_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("CANVA_CLIENT_SECRET")
        self.redirect_uri = (
            redirect_uri
            or os.getenv("CANVA_REDIRECT_URI")
            or "http://127.0.0.1:8080/oauth/callback"
        )

        env_scopes = os.getenv("CANVA_SCOPES")
        if env_scopes:
            self.scopes = [s.strip() for s in env_scopes.split(",") if s.strip()]
        else:
            self.scopes = self.DEFAULT_SCOPES

        self.session = requests.Session()
        self.session.verify = False
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        if not self.client_id or not self.client_secret:
            raise ValueError(
                "Canva credentials missing. Please define CANVA_CLIENT_ID and "
                "CANVA_CLIENT_SECRET in your .env file."
            )

        self._tokens: Optional[Dict[str, Any]] = self._load_cached_tokens()

    # -------------------------------------------------------------------------
    # Authentication & PKCE Flow
    # -------------------------------------------------------------------------

    @staticmethod
    def _generate_pkce_pair():
        verifier = secrets.token_urlsafe(64)
        digest = hashlib.sha256(verifier.encode("utf-8")).digest()
        challenge = base64.urlsafe_b64encode(digest).decode("utf-8").replace("=", "")
        return verifier, challenge

    def get_authorization_url(self, scopes: Optional[List[str]] = None) -> tuple[str, str, str]:
        """
        Generate the Canva authorization URL with PKCE.
        
        Returns:
            (auth_url, code_verifier, state)
        """
        code_verifier, code_challenge = self._generate_pkce_pair()
        state = secrets.token_urlsafe(16)
        scope_str = " ".join(scopes or self.scopes)

        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": scope_str,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
            "state": state,
        }
        url = f"{self.AUTH_URL}?{urllib.parse.urlencode(params)}"
        return url, code_verifier, state

    def exchange_code_for_token(self, code: str, code_verifier: str) -> Dict[str, Any]:
        """Exchange the authorization code for an OAuth access and refresh token."""
        credentials = f"{self.client_id}:{self.client_secret}"
        encoded_creds = base64.b64encode(credentials.encode()).decode()

        headers = {
            "Authorization": f"Basic {encoded_creds}",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        payload = {
            "grant_type": "authorization_code",
            "code_verifier": code_verifier,
            "code": code,
            "redirect_uri": self.redirect_uri,
        }

        response = self.session.post(self.TOKEN_URL, headers=headers, data=payload)
        if not response.ok:
            raise RuntimeError(f"Token exchange failed ({response.status_code}): {response.text}")

        token_data = response.json()
        token_data["created_at"] = time.time()
        self._save_tokens(token_data)
        self._tokens = token_data
        return token_data

    def refresh_access_token(self) -> Dict[str, Any]:
        """Refresh an expired access token using the stored refresh token."""
        if not self._tokens or "refresh_token" not in self._tokens:
            raise RuntimeError("No refresh token available. Re-authorization required.")

        credentials = f"{self.client_id}:{self.client_secret}"
        encoded_creds = base64.b64encode(credentials.encode()).decode()

        headers = {
            "Authorization": f"Basic {encoded_creds}",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        payload = {
            "grant_type": "refresh_token",
            "refresh_token": self._tokens["refresh_token"],
        }

        response = self.session.post(self.TOKEN_URL, headers=headers, data=payload)
        if not response.ok:
            raise RuntimeError(f"Token refresh failed ({response.status_code}): {response.text}")

        token_data = response.json()
        token_data["created_at"] = time.time()
        self._save_tokens(token_data)
        self._tokens = token_data
        return token_data

    def get_valid_access_token(self) -> str:
        """Return a valid access token, refreshing if necessary."""
        if not self._tokens:
            raise RuntimeError("Not authenticated with Canva. Run authentication flow first.")

        created_at = self._tokens.get("created_at", 0)
        expires_in = self._tokens.get("expires_in", 3600)
        # If expiring in less than 60 seconds, refresh
        if (time.time() - created_at) > (expires_in - 60):
            self.refresh_access_token()

        return self._tokens["access_token"]

    def _get_auth_headers(self) -> Dict[str, str]:
        token = self.get_valid_access_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    # -------------------------------------------------------------------------
    # Token Cache Storage
    # -------------------------------------------------------------------------

    def _save_tokens(self, tokens: Dict[str, Any]) -> None:
        with open(TOKEN_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(tokens, f, indent=2)

    def _load_cached_tokens(self) -> Optional[Dict[str, Any]]:
        if TOKEN_CACHE_FILE.exists():
            try:
                with open(TOKEN_CACHE_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return None
        return None

    # -------------------------------------------------------------------------
    # Canva API Actions (Designs & Video Export)
    # -------------------------------------------------------------------------

    def get_user_profile(self) -> Dict[str, Any]:
        """Retrieve current user profile."""
        response = self.session.get(f"{self.API_BASE}/users/me", headers=self._get_auth_headers())
        response.raise_for_status()
        return response.json()

    def create_video_export_job(self, design_id: str, quality: str = "regular") -> str:
        """
        Request Canva to export a design as an MP4 video.
        
        Args:
            design_id: The ID of the Canva design.
            quality: 'regular' or 'high'
            
        Returns:
            The export job ID.
        """
        payload = {
            "design_id": design_id,
            "format": {
                "type": "mp4",
                "quality": quality,
            },
        }
        response = self.session.post(
            f"{self.API_BASE}/exports",
            headers=self._get_auth_headers(),
            json=payload,
        )
        if not response.ok:
            raise RuntimeError(f"Export creation failed ({response.status_code}): {response.text}")

        data = response.json()
        return data["job"]["id"]

    def get_export_job_status(self, job_id: str) -> Dict[str, Any]:
        """Check status of a running export job."""
        response = self.session.get(
            f"{self.API_BASE}/exports/{job_id}",
            headers=self._get_auth_headers(),
        )
        response.raise_for_status()
        return response.json()["job"]

    def export_video_and_download(
        self,
        design_id: str,
        output_path: str = "canva_video.mp4",
        poll_interval: int = 5,
        verbose: bool = True,
    ) -> str:
        """
        Export a Canva design to MP4, poll until complete, and download the video.

        Returns:
            The path of the downloaded MP4 file.
        """
        if verbose:
            print(f"[Canva] Requesting MP4 export for design {design_id}...")

        job_id = self.create_video_export_job(design_id)
        if verbose:
            print(f"[Canva] Export job initiated (ID: {job_id}). Rendering video...")

        while True:
            time.sleep(poll_interval)
            job = self.get_export_job_status(job_id)
            status = job.get("status")

            if status == "success":
                urls = job.get("urls", [])
                if not urls:
                    raise RuntimeError("Export completed but no download URLs were provided.")

                download_url = urls[0]
                if verbose:
                    print(f"[Canva] Render complete! Downloading video...")

                res = self.session.get(download_url, stream=True)
                res.raise_for_status()

                out_file = Path(output_path).resolve()
                out_file.parent.mkdir(parents=True, exist_ok=True)
                with open(out_file, "wb") as f:
                    for chunk in res.iter_content(chunk_size=8192):
                        f.write(chunk)

                if verbose:
                    print(f"[Canva] Video successfully saved to: {out_file}")
                return str(out_file)

            elif status == "failed":
                error_info = job.get("error", "Unknown error")
                raise RuntimeError(f"Export job failed: {error_info}")

            if verbose:
                print(f"[Canva] Status: {status}... rendering")
