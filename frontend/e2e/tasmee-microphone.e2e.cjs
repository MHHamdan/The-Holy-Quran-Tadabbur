/**
 * Tasmee microphone behaviour (the same code runs in the Android/iOS WebView):
 * permission denied, recording, OS interruption, app backgrounded, connection
 * lost mid-recording, and speech recognition unavailable (HF quota).
 *
 * Needs the web build served with /api proxied to a running backend:
 *   npx vite build && npx vite preview --port 4173   (backend on the proxy target)
 *   node e2e/tasmee-microphone.e2e.cjs
 * Env: E2E_BASE_URL, E2E_SHOTS (screenshot dir), PLAYWRIGHT_MODULE.
 * Not part of CI: it needs a live backend with a seeded Qur'an table.
 */
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const B = process.env.E2E_BASE_URL || 'http://localhost:4173';
const init = (ctx) => ctx.addInitScript(() => {
  localStorage.setItem('tadabbur-persona', JSON.stringify({ state: { persona: null, hasChosen: true }, version: 0 }));
  localStorage.setItem('tadabbur-language', JSON.stringify({ state: { language: 'en', direction: 'ltr' }, version: 0 }));
  // Expose the stream so the test can simulate OS-level interruptions.
  const orig = navigator.mediaDevices && navigator.mediaDevices.getUserMedia.bind(navigator.mediaDevices);
  if (orig) navigator.mediaDevices.getUserMedia = async (c) => { const s = await orig(c); window.__stream = s; return s; };
});
async function openSession(page) {
  await page.goto(B + '/tasmee', { waitUntil: 'networkidle' });
  await page.getByRole('button', { name: /Start Session/i }).click();
  await page.getByRole('button', { name: 'Start recording' }).waitFor({ timeout: 15000 });
  await page.waitForFunction(() => !document.querySelector('button[aria-label="Start recording"]').disabled, null, { timeout: 15000 });
}
const banner = (page) => page.evaluate(() => document.body.innerText);
const result = {};
(async () => {
  // 1. Permission denied
  { const b = await chromium.launch({ args: ['--use-fake-device-for-media-stream'] });
    const ctx = await b.newContext(); await init(ctx);
    // What Chrome, Android WebView and WKWebView raise when the user taps "Don't allow".
    await ctx.addInitScript(() => { navigator.mediaDevices.getUserMedia = () => Promise.reject(new DOMException('Permission denied', 'NotAllowedError')); });
    const p = await ctx.newPage();
    await openSession(p); await p.getByRole('button', { name: 'Start recording' }).click(); await p.waitForTimeout(1500);
    const t = await banner(p);
    result.permission_denied = { title: /Microphone permission denied/.test(t), guidance: /lock icon|Settings/.test(t), notStreaming: await p.getByRole('button', { name: 'Start recording' }).isVisible() };
    await p.screenshot({ path: (process.env.E2E_SHOTS || '/tmp') + '/mic-denied.png' }); await b.close(); }

  const b = await chromium.launch({ args: ['--use-fake-device-for-media-stream', '--use-fake-ui-for-media-stream'] });
  // 2. Granted: streaming works and audio frames reach the backend
  { const ctx = await b.newContext(); await init(ctx); await ctx.grantPermissions(['microphone']); const p = await ctx.newPage();
    let frames = 0; p.on('websocket', ws => ws.on('framesent', f => { if (typeof f.payload !== 'string') frames++; }));
    // Real server session, but audio is not forwarded: with HF credits exhausted the
    // server would (correctly) end the session with stt_unavailable mid-test.
    await p.routeWebSocket(/\/api\/v1\/tasmee\/ws\//, ws => { const server = ws.connectToServer(); ws.onMessage(m => { if (typeof m === "string") server.send(m); else frames++; }); });
    await openSession(p); await p.getByRole('button', { name: 'Start recording' }).click(); await p.waitForTimeout(3000);
    result.recording = { stopVisible: await p.getByRole('button', { name: 'Stop recording' }).isVisible(), audioFramesSent: frames };
    // 3. Interruption: the OS ends the track (call / other app / permission revoked)
    await p.evaluate(() => window.__stream.getAudioTracks()[0].dispatchEvent(new Event('ended')));
    await p.waitForTimeout(800);
    let t = await banner(p);
    result.interrupted = { title: /Recording interrupted/.test(t), micReleased: await p.evaluate(() => window.__stream.getAudioTracks()[0].readyState === 'ended'), recordButtonBack: await p.getByRole('button', { name: 'Start recording' }).isVisible() };
    await p.screenshot({ path: (process.env.E2E_SHOTS || '/tmp') + '/mic-interrupted.png' });
    // 4. Try again, then the app goes to the background
    await p.getByRole('button', { name: 'Try Again' }).click(); await p.waitForTimeout(1500);
    const resumed = await p.getByRole('button', { name: 'Stop recording' }).isVisible();
    await p.evaluate(() => { Object.defineProperty(document, 'hidden', { configurable: true, get: () => true }); document.dispatchEvent(new Event('visibilitychange')); });
    await p.waitForTimeout(800); t = await banner(p);
    result.background = { resumedAfterTryAgain: resumed, paused: /went to the background/.test(t), micReleased: await p.evaluate(() => window.__stream.getAudioTracks()[0].readyState === 'ended') };
    await ctx.close(); }

  // 5. Backend error mid-recording: the server drops the WebSocket
  { const ctx = await b.newContext(); await init(ctx); await ctx.grantPermissions(['microphone']); const p = await ctx.newPage();
    let client;
    await p.routeWebSocket(/\/api\/v1\/tasmee\/ws\//, ws => { client = ws; ws.connectToServer(); });
    await openSession(p); await p.getByRole('button', { name: 'Start recording' }).click(); await p.waitForTimeout(1500);
    // As seen by the app: the server side drops the socket with an internal error.
    await client.close({ code: 1011, reason: 'internal error' }); await p.waitForTimeout(1000);
    const t = await banner(p);
    result.connection_lost = { title: /Connection lost/.test(t), micReleased: await p.evaluate(() => window.__stream.getAudioTracks()[0].readyState === 'ended'), notStreaming: !(await p.getByRole('button', { name: 'Stop recording' }).isVisible()) };
    await p.screenshot({ path: (process.env.E2E_SHOTS || '/tmp') + '/mic-connection-lost.png' }); await ctx.close(); }

  // 6. Speech recognition unavailable (HF quota): server reports stt_unavailable, then closes 4003
  { const ctx = await b.newContext(); await init(ctx); await ctx.grantPermissions(['microphone']); const p = await ctx.newPage();
    let server, client;
    await p.routeWebSocket(/\/api\/v1\/tasmee\/ws\//, ws => { client = ws; server = ws.connectToServer(); });
    await openSession(p); await p.getByRole('button', { name: 'Start recording' }).click(); await p.waitForTimeout(1500);
    client.send(JSON.stringify({ type: 'stt_unavailable', reason: 'ai_quota_exceeded' })); await p.waitForTimeout(500);
    const t1 = await banner(p);
    await client.close({ code: 4003, reason: 'stt_unavailable' }); await p.waitForTimeout(800);
    const t2 = await banner(p);
    result.stt_unavailable = { quotaNotice: /Speech recognition limit reached/.test(t1), stillShownAfterClose: /Speech recognition limit reached/.test(t2), micReleased: await p.evaluate(() => window.__stream.getAudioTracks()[0].readyState === 'ended') };
    await p.screenshot({ path: (process.env.E2E_SHOTS || '/tmp') + '/mic-stt-unavailable.png' }); await ctx.close(); }
  await b.close();
  console.log(JSON.stringify(result, null, 1));
})().catch(e => { console.error('FAILED', e.message); console.log(JSON.stringify(result, null, 1)); process.exit(1); });
