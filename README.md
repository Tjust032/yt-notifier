# yt-notifier

A GitHub Action that checks every 10 minutes whether [@Zwag](https://www.youtube.com/@Zwag) is live on YouTube and sends a push notification to your phone through [ntfy.sh](https://ntfy.sh). You get one notification per stream.

## Setup

1. Install the ntfy app ([iOS](https://apps.apple.com/app/ntfy/id1625396347) / [Android](https://play.google.com/store/apps/details?id=io.heckel.ntfy)).
2. In the app, subscribe to a hard-to-guess topic, e.g. `zwag-live-8f3k2q9x`. ntfy topics are public: anyone who knows the name can read or post to it.
3. Add that topic name as a repo secret named `NTFY_TOPIC` under **Settings → Secrets and variables → Actions**.
4. Test it: **Actions → "Check if Zwag is live" → Run workflow**. You only get a notification if Zwag is live at that moment.

## How it works

- `check_live.py` fetches `https://www.youtube.com/@Zwag/live`. When the channel is live, that URL resolves to the stream's watch page, and the script reads the video ID from the page's canonical link.
- Scheduled and upcoming streams also resolve to a watch page, so the script ignores them unless the page says the stream is live now.
- After notifying, the workflow saves a cache entry keyed by the video ID (`notified-<id>`). Later runs see that entry and skip the notification, so each stream notifies once.
- No YouTube API key is needed.

## Caveats

- GitHub can delay scheduled runs, sometimes by a lot when its runners are busy, so a notification may arrive well after the stream starts.
- GitHub turns off scheduled workflows after 60 days with no repo activity. Re-enable it from the Actions tab, or push a commit now and then.
- The check reads YouTube's page HTML, so it may break if YouTube changes that HTML.
