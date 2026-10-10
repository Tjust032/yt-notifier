"""Check whether a YouTube channel is live right now.

Prints the live video ID to stdout and exits 0 when live; exits 1 when not live.
"""
import re
import sys
import urllib.request

CHANNEL = sys.argv[1] if len(sys.argv) > 1 else "@Zwag"


def fetch(url: str) -> str:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/126.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
            # Skip the EU cookie consent interstitial.
            "Cookie": "CONSENT=YES+1; SOCS=CAI",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


def live_video_id(html: str) -> str | None:
    # When a channel is live (or has a scheduled stream), /live redirects to a watch page.
    m = re.search(r'<link rel="canonical" href="https://www\.youtube\.com/watch\?v=([\w-]{11})"', html)
    if not m:
        canon = re.search(r'<link rel="canonical" href="([^"]+)"', html)
        log(f"No watch-page canonical link (canonical: {canon.group(1) if canon else 'none'}).")
        return None
    # Exclude scheduled/upcoming streams: only count it if it's actually live now.
    if '"isLiveNow":true' not in html and '"isLive":true' not in html:
        log(f"Watch page {m.group(1)} found, but it isn't marked live now (likely scheduled).")
        return None
    return m.group(1)


def log(msg: str) -> None:
    # stderr, so it shows in the Actions log without polluting the video ID on stdout.
    print(msg, file=sys.stderr)


if __name__ == "__main__":
    html = fetch(f"https://www.youtube.com/{CHANNEL}/live")
    title = re.search(r"<title>(.*?)</title>", html, re.S)
    log(f"Fetched {len(html)} bytes; page title: {title.group(1).strip() if title else 'none'!r}")
    vid = live_video_id(html)
    if vid:
        print(vid)
        sys.exit(0)
    sys.exit(1)
