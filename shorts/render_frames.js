// Renders an animated HTML page frame by frame into a silent mp4.
// The page must define window.render(t) that draws the scene at time t (seconds); nothing else animates.
// usage: node render_frames.js page.html out.mp4 fps duration width height
const fs = require('fs');
const { spawn } = require('child_process');
const { chromium } = require('playwright');

(async () => {
  const [, , page, out, fps, dur, w, h] = process.argv;
  const n = Math.round(+dur * +fps);
  const ff = spawn('ffmpeg', ['-v', 'error', '-y', '-f', 'image2pipe', '-c:v', 'mjpeg', '-framerate', fps, '-i', '-',
    '-c:v', 'libx264', '-preset', 'medium', '-crf', '17', '-pix_fmt', 'yuv420p', '-r', fps, out],
    { stdio: ['pipe', 'inherit', 'inherit'] });
  const browser = await chromium.launch();
  const p = await browser.newPage({ viewport: { width: +w, height: +h } });
  await p.goto('file://' + page);
  await p.evaluate(async () => {
    await document.fonts.ready;
    await Promise.all(Array.from(document.images).map((i) => i.decode().catch(() => {})));
  });
  for (let i = 0; i < n; i++) {
    await p.evaluate((t) => window.render(t), i / +fps);
    const buf = await p.screenshot({ type: 'jpeg', quality: 93 });
    if (!ff.stdin.write(buf)) await new Promise((r) => ff.stdin.once('drain', r));
    if (i % 150 === 0) process.stderr.write(`frame ${i}/${n}\n`);
  }
  ff.stdin.end();
  await new Promise((r) => ff.on('close', r));
  await browser.close();
})();
