"""Check whether a YouTube channel is live right now, using the YouTube Data API.

Prints the live video ID to stdout and exits 0 when live; exits 1 when not live.
Exits 2 on errors (bad API key, unknown channel, network), so the workflow fails loudly.

Costs 3 quota units per run (channels.list + playlistItems.list + videos.list),
about 430/day at a 10-minute interval. The free quota is 10,000/day.
"""
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

CHANNEL = sys.argv[1] if len(sys.argv) > 1 else "@Zwag"
API = "https://www.googleapis.com/youtube/v3"


def log(msg: str) -> None:
    # stderr, so it shows in the Actions log without polluting the video ID on stdout.
    print(msg, file=sys.stderr)


def api(endpoint: str, **params: str) -> dict:
    params["key"] = os.environ["YOUTUBE_API_KEY"]
    url = f"{API}/{endpoint}?{urllib.parse.urlencode(params)}"
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as e:
        # Don't include the URL: it contains the API key.
        raise RuntimeError(f"{endpoint} failed: HTTP {e.code} {e.read().decode(errors='replace')}") from None


def live_video_id(handle: str) -> str | None:
    channels = api("channels", part="snippet,contentDetails", forHandle=handle).get("items", [])
    if not channels:
        raise RuntimeError(f"No channel found for {handle}")
    channel = channels[0]
    uploads = channel["contentDetails"]["relatedPlaylists"]["uploads"]
    log(f"Channel: {channel['snippet']['title']} ({channel['id']})")

    # Live streams show up in the uploads playlist once they're scheduled or started.
    items = api("playlistItems", part="contentDetails", playlistId=uploads, maxResults="50").get("items", [])
    ids = [i["contentDetails"]["videoId"] for i in items]
    if not ids:
        log("No uploads.")
        return None

    videos = api("videos", part="snippet", id=",".join(ids)).get("items", [])
    # liveBroadcastContent is "live" only while streaming; scheduled streams are "upcoming".
    live = [v["id"] for v in videos if v["snippet"].get("liveBroadcastContent") == "live"]
    upcoming = [v["id"] for v in videos if v["snippet"].get("liveBroadcastContent") == "upcoming"]
    log(f"Checked {len(ids)} recent videos: live={live} upcoming={upcoming}")
    return live[0] if live else None


if __name__ == "__main__":
    if not os.environ.get("YOUTUBE_API_KEY"):
        log("YOUTUBE_API_KEY is not set")
        sys.exit(2)
    try:
        vid = live_video_id(CHANNEL)
    except Exception as e:
        log(f"Error: {e}")
        sys.exit(2)
    if vid:
        print(vid)
        sys.exit(0)
    sys.exit(1)
