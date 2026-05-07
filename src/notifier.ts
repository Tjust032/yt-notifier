import axios from 'axios';
import nodemailer from 'nodemailer';
import fs from 'fs/promises';

const STATE_FILE = './state.json';

interface LiveCheckResult {
  isLive: boolean;
  videoId?: string;
  title?: string;
  channelTitle?: string;
  thumbnail?: string;
}

interface State {
  notified: Record<string, string>;
}

async function loadState(): Promise<State> {
  try {
    const raw = await fs.readFile(STATE_FILE, 'utf-8');
    return JSON.parse(raw);
  } catch {
    return { notified: {} };
  }
}

async function saveState(state: State): Promise<void> {
  await fs.writeFile(STATE_FILE, JSON.stringify(state, null, 2));
}

async function checkChannelLive(channelId: string, apiKey: string): Promise<LiveCheckResult> {
  const { data } = await axios.get('https://www.googleapis.com/youtube/v3/search', {
    params: {
      part: 'snippet',
      channelId,
      eventType: 'live',
      type: 'video',
      key: apiKey,
    },
  });

  if (data.items && data.items.length > 0) {
    const item = data.items[0];
    return {
      isLive: true,
      videoId: item.id.videoId,
      title: item.snippet.title,
      channelTitle: item.snippet.channelTitle,
      thumbnail: item.snippet.thumbnails.high.url,
    };
  }
  return { isLive: false };
}

async function sendEmail(result: LiveCheckResult): Promise<void> {
  const transporter = nodemailer.createTransport({
    service: 'gmail',
    auth: {
      user: process.env.GMAIL_USER!,
      pass: process.env.GMAIL_APP_PASSWORD!,
    },
  });

  const videoUrl = `https://www.youtube.com/watch?v=${result.videoId}`;
  await transporter.sendMail({
    from: process.env.GMAIL_USER,
    to: process.env.NOTIFY_EMAIL,
    subject: `[LIVE] ${result.channelTitle}: ${result.title}`,
    html: `
      <h2>${result.channelTitle} just went live!</h2>
      <p><strong>${result.title}</strong></p>
      <a href="${videoUrl}">
        <img src="${result.thumbnail}" alt="thumbnail" style="max-width:480px;" />
      </a>
      <p><a href="${videoUrl}">Watch now</a></p>
    `,
  });
  console.log(`Sent notification for ${result.channelTitle} — ${result.videoId}`);
}

async function main(): Promise<void> {
  const apiKey = process.env.YOUTUBE_API_KEY;
  const channelIdsRaw = process.env.CHANNEL_IDS;

  if (!apiKey || !channelIdsRaw) {
    console.error('Missing required env vars: YOUTUBE_API_KEY and CHANNEL_IDS');
    process.exit(1);
  }

  const channelIds = channelIdsRaw.split(',').map(s => s.trim()).filter(Boolean);
  const state = await loadState();
  let stateChanged = false;

  for (const channelId of channelIds) {
    try {
      const result = await checkChannelLive(channelId, apiKey);
      const lastNotified = state.notified[channelId];

      if (result.isLive && result.videoId !== lastNotified) {
        await sendEmail(result);
        state.notified[channelId] = result.videoId!;
        stateChanged = true;
      } else if (!result.isLive && lastNotified) {
        delete state.notified[channelId];
        stateChanged = true;
      } else {
        console.log(`${channelId}: ${result.isLive ? 'live (already notified)' : 'not live'}`);
      }
    } catch (err: unknown) {
      const msg = axios.isAxiosError(err) ? JSON.stringify(err.response?.data) : String(err);
      console.error(`Error checking ${channelId}: ${msg}`);
    }
  }

  if (stateChanged) {
    await saveState(state);
    console.log('State saved.');
  }
}

main().catch(err => {
  console.error('Fatal:', err);
  process.exit(1);
});
