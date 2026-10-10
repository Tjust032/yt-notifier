# yt-notifier

A GitHub Action that checks every 10 minutes whether [@Zwag](https://www.youtube.com/@Zwag) is live on YouTube and sends a push notification to your phone through [ntfy.sh](https://ntfy.sh). You get one notification per stream.

## Setup

1. Install the ntfy app ([iOS](https://apps.apple.com/app/ntfy/id1625396347) / [Android](https://play.google.com/store/apps/details?id=io.heckel.ntfy)).
2. In the app, subscribe to a hard-to-guess topic, e.g. `zwag-live-8f3k2q9x`. ntfy topics are public: anyone who knows the name can read or post to it.
3. Get a YouTube Data API v3 key from [Google Cloud Console](https://console.cloud.google.com/apis/credentials) (enable "YouTube Data API v3" for the project).
4. Under **Settings → Secrets and variables → Actions**, add two repo secrets:
   - `NTFY_TOPIC`: the topic name only, without `ntfy.sh/`.
   - `YOUTUBE_API_KEY`: the API key.
5. Test it: **Actions → "Check if Zwag is live" → Run workflow**. You can enter any channel handle that's live right now (e.g. `@NBCNews`) to check the notification end to end.

## How it works

- `check_live.py` looks up the channel by handle, reads its 50 most recent uploads, and asks the API which of them is live right now. Live streams appear in the uploads list as soon as they're scheduled or started.
- Scheduled and upcoming streams are ignored until they actually go live.
- After notifying, the workflow saves a cache entry keyed by the video ID (`notified-<id>`). Later runs see that entry and skip the notification, so each stream notifies once.
- Each run costs 3 API quota units, about 430/day. The free quota is 10,000/day.
- A failed check (bad key, quota exhausted, API down) fails the run, so you'll see a red X in Actions instead of a silent "Not live."

Why not scrape `youtube.com/@channel/live` instead? YouTube serves GitHub's runners a "sign in to confirm you're not a bot" page, so scraping can't tell whether a channel is live.

## Caveats

- GitHub can delay scheduled runs, sometimes by a lot when its runners are busy, so a notification may arrive well after the stream starts.
- GitHub turns off scheduled workflows after 60 days with no repo activity. Re-enable it from the Actions tab, or push a commit now and then.
- A stream that was scheduled long ago, with 50+ newer uploads since, won't be found. That's unlikely for Zwag but possible for very busy channels.
