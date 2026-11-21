// Renders a batch of HTML stickers to transparent PNGs in one Chromium session.
// usage: node render_stickers.js items.json FONTS_DIR
// items.json: [{"out": "/path/a.png", "html": "<div ...>...</div>"}, ...]
const fs = require('fs');
const { chromium } = require('playwright');

(async () => {
  const [, , itemsPath, fontsDir] = process.argv;
  const items = JSON.parse(fs.readFileSync(itemsPath, 'utf8'));
  const faces = [
    ['Anton', 'Anton-Regular.ttf'], ['Bangers', 'Bangers-Regular.ttf'],
    ['Luckiest Guy', 'LuckiestGuy-Regular.ttf'], ['Permanent Marker', 'PermanentMarker-Regular.ttf'],
  ].map(([n, f]) => `@font-face { font-family: '${n}'; src: url(file://${fontsDir}/${f}); }`).join('\n');
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1400, height: 2000 } });
  for (const it of items) {
    await page.setContent(`<!doctype html><meta charset="utf-8"><style>${faces}
      html, body { margin: 0; background: transparent; }
      #wrap { display: inline-block; padding: 28px; }
      .o { position: relative; display: inline-block; }
      .o .b { position: absolute; left: 0; top: 0; color: transparent; }
      .o .f { position: relative; }
    </style><div id="wrap">${it.html}</div>`);
    await page.evaluate(() => document.fonts.ready);
    await (await page.$('#wrap')).screenshot({ path: it.out, omitBackground: true });
  }
  await browser.close();
})();
