// usage: node render_html.js page.html out.png width height
const { chromium } = require('playwright');
(async () => {
  const [, , page, out, w, h] = process.argv;
  const browser = await chromium.launch();
  const p = await browser.newPage({ viewport: { width: +w, height: +h } });
  await p.goto('file://' + page);
  await p.evaluate(() => document.fonts.ready);
  // omitBackground keeps transparent pages transparent (cards drawn over footage)
  await p.screenshot({ path: out, clip: { x: 0, y: 0, width: +w, height: +h }, omitBackground: true });
  await browser.close();
})();
