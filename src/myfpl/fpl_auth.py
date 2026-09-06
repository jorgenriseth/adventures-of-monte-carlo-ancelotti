import getpass
import os
import re
import shutil
import subprocess
import webbrowser

import requests

from fpl_api_models.manager import MyTeam
from myfpl.team_state import TeamState

# users.premierleague.com (the old email+password login endpoint) no longer resolves;
# Premier League has migrated to a different auth backend we haven't reverse-engineered.
LOGIN_URL = "https://users.premierleague.com/accounts/login/"
LOGIN_PAGE_URL = "https://fantasy.premierleague.com/"
MY_TEAM_URL = "https://fantasy.premierleague.com/api/my-team/{manager_id}/"

_USER_AGENT = "Mozilla/5.0 (compatible; myfpl/1.0)"


def login_with_credentials(email: str, password: str) -> requests.Session:
    """Authenticates against the FPL accounts service and returns a session with the auth cookies set."""
    raise RuntimeError(
        "Direct email/password login is broken: users.premierleague.com no longer resolves "
        "(Premier League migrated their login backend). Use --login-method browser instead."
    )


def login_interactively() -> requests.Session:
    """Prompts for email + password on the terminal (password hidden) instead of reading env vars."""
    email = input("FPL email: ").strip()
    password = getpass.getpass("FPL password (hidden): ")
    return login_with_credentials(email, password)


def login_with_cookie_header(cookie_header: str) -> requests.Session:
    """Builds a session from a raw browser 'cookie' request header only (legacy fallback)."""
    cookie_header = cookie_header.strip()
    if cookie_header.lower().startswith("cookie:"):
        cookie_header = cookie_header.split(":", 1)[1].strip()
    session = requests.Session()
    session.headers.update({"User-Agent": _USER_AGENT})
    for part in cookie_header.split(";"):
        if "=" not in part:
            continue
        name, _, value = part.strip().partition("=")
        session.cookies.set(name, value, domain=".premierleague.com")
    if not session.cookies:
        raise RuntimeError(
            "No cookies parsed from the pasted value. Make sure you copied the 'cookie' "
            "request header (not a response header) after logging in."
        )
    return session


_CURL_HEADER_RE = re.compile(r"-H\s+'([^:']+):\s*([^']*)'")


def parse_curl_headers(curl_text: str) -> dict[str, str]:
    """Extracts header name/value pairs from a browser 'Copy as cURL' command."""
    return {
        name.strip(): value.strip()
        for name, value in _CURL_HEADER_RE.findall(curl_text)
    }


def login_with_curl_command(curl_text: str) -> requests.Session:
    """Builds a session by replaying every header from a 'Copy as cURL' capture.

    Replays cookies AND any other auth-related headers (e.g. a Bearer token), since
    the real auth mechanism behind the my-team endpoint is unverified.
    """
    headers = parse_curl_headers(curl_text)
    if not headers:
        raise RuntimeError(
            "Could not find any '-H' headers in the pasted text. Make sure you used "
            "DevTools 'Copy as cURL', not just the cookie value."
        )
    session = requests.Session()
    session.headers.update({"User-Agent": _USER_AGENT})
    for name, value in headers.items():
        if name.lower() == "cookie":
            for part in value.split(";"):
                if "=" not in part:
                    continue
                cname, _, cvalue = part.strip().partition("=")
                session.cookies.set(cname, cvalue, domain=".premierleague.com")
        elif name.lower() != "user-agent":
            session.headers[name] = value
    return session


def _read_clipboard() -> str | None:
    """Reads the macOS clipboard via pbpaste, bypassing the terminal's line-length limit entirely."""
    if shutil.which("pbpaste") is None:
        return None
    result = subprocess.run(["pbpaste"], capture_output=True, text=True, check=False)
    return result.stdout if result.returncode == 0 else None


def login_via_browser() -> requests.Session:
    """Opens the real FPL login page, then replays every header from a 'Copy as cURL' capture."""
    print(f"Opening {LOGIN_PAGE_URL} in your browser...")
    webbrowser.open(LOGIN_PAGE_URL)
    print(
        "Log in there, then open DevTools > Network, click the '/api/my-team/...' "
        "request (or any fantasy.premierleague.com/api/ request), right-click it, and "
        "choose 'Copy > Copy as cURL'. Copy the whole thing to your clipboard."
    )
    input("Press Enter once you've copied it to your clipboard...")
    curl_text = _read_clipboard()
    if not curl_text:
        # Pasting long captures into input() can silently truncate at the terminal's
        # canonical line-buffer limit, so this is a last resort.
        curl_text = input(
            "Could not read the clipboard; paste the 'Copy as cURL' text here: "
        )
    if "-H" in curl_text:
        return login_with_curl_command(curl_text)
    return login_with_cookie_header(curl_text)


def fetch_my_team(manager_id: int, session: requests.Session) -> MyTeam:
    """Fetches the authenticated my-team payload for the manager who owns the given session."""
    response = session.get(MY_TEAM_URL.format(manager_id=manager_id))
    if response.status_code == 403:
        raise RuntimeError(
            f"Not authorised to view my-team for manager {manager_id}. "
            "manager_id must match the account that logged in."
        )
    response.raise_for_status()
    return MyTeam.model_validate(response.json())


def fetch_player_names() -> dict[int, str]:
    """Fetches player_id -> web_name from the public bootstrap-static endpoint (no auth needed)."""
    response = requests.get("https://fantasy.premierleague.com/api/bootstrap-static/")
    response.raise_for_status()
    return {element["id"]: element["web_name"] for element in response.json()["elements"]}


def fetch_team_state(
    manager_id: int,
    email: str | None = None,
    password: str | None = None,
    method: str = "interactive",
) -> TeamState:
    """Logs in and builds a TeamState for the given manager.

    method controls how login happens when email/password aren't passed explicitly:
      - "interactive": prompt for email + hidden password on the terminal (default)
      - "browser": open the FPL login page and prompt for a pasted session cookie
      - "env": read FPL_EMAIL / FPL_PASSWORD environment variables
    """
    email = email or os.environ.get("FPL_EMAIL")
    password = password or os.environ.get("FPL_PASSWORD")

    if email and password:
        session = login_with_credentials(email, password)
    elif method == "browser":
        session = login_via_browser()
    elif method == "interactive":
        session = login_interactively()
    elif method == "env":
        raise RuntimeError(
            "FPL_EMAIL and FPL_PASSWORD must be set as env vars for method='env'."
        )
    else:
        raise ValueError(
            f"Unknown login method: {method!r} (expected 'interactive', 'browser', or 'env')."
        )

    my_team = fetch_my_team(manager_id, session)
    player_names = fetch_player_names()
    return TeamState.from_my_team(manager_id, my_team, player_names)
