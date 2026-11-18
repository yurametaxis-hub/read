// Renders the title plaque to a transparent PNG with Chromium,
// which takes care of emoji and font fallback.
// usage: node render_title.js out.png '{"html": "Speed found <b>KFC</b> 🍗", "size": 52}'
const { chromium } = require('playwright');

(async () => {
  const [, , outPath, raw] = process.argv;
  const o = JSON.parse(raw);
  const page_html = `<!doctype html><meta charset="utf-8"><style>
    html, body { margin: 0; background: transparent; }
    #wrap { display: inline-block; padding: 24px; }
    #p {
      display: inline-block; box-sizing: border-box; max-width: ${o.maxWidth || 900}px;
      padding: ${o.padY || 16}px ${o.padX || 30}px; border-radius: ${o.radius || 22}px;
      background: ${o.bg || '#ffffff'}; color: ${o.color || '#000000'};
      font-family: '${o.font || 'Montserrat'}', 'Noto Color Emoji', sans-serif;
      font-weight: ${o.weight || 800}; font-size: ${o.size || 50}px; line-height: 1.18;
      text-align: center; box-shadow: 0 6px 20px rgba(0, 0, 0, .35);
    }
    #p b { color: ${o.accent || '#e0262f'}; font-weight: inherit; }
  </style><div id="wrap"><div id="p">${o.html}</div></div>`;
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1080, height: 800 } });
  await page.setContent(page_html);
  await page.evaluate(() => document.fonts.ready);
  await (await page.$('#wrap')).screenshot({ path: outPath, omitBackground: true });
  await browser.close();
})();
