import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import crypto from 'node:crypto';
import { createRequire } from 'node:module';
import { execFileSync } from 'node:child_process';

// Extract and render the original scene; never generate or repair drawing elements.
const argv = process.argv.slice(2);
if (!argv.length || argv.includes('--help')) {
  console.log('Usage: node prepare-evidence.mjs input.excalidraw [--output NEW_DIR] [--runtime CACHE_DIR]');
  process.exit(argv.length ? 0 : 1);
}
const source = path.resolve(argv.shift());
const flags = {};
while (argv.length) {
  const flag = argv.shift();
  if (!['--output', '--runtime'].includes(flag) || !argv.length) throw new Error(`Invalid option: ${flag}`);
  flags[flag] = path.resolve(argv.shift());
}
const raw = fs.readFileSync(source);
const digest = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const sha256 = digest(raw);
const data = JSON.parse(raw.toString('utf8').replace(/^\uFEFF/, ''));
if (data.type !== 'excalidraw' || !Array.isArray(data.elements)) throw new Error('Expected an Excalidraw scene with an elements array.');
const active = data.elements.filter(e => !e.isDeleted);
if (!active.length) throw new Error('No active elements to render.');
const out = flags['--output'] || fs.mkdtempSync(path.join(os.tmpdir(), 'excalidraw-evaluation-'));
if (fs.existsSync(out) && fs.readdirSync(out).length) throw new Error('Output directory must be new or empty.');
fs.mkdirSync(out, { recursive: true });
const write = (name, value) => fs.writeFileSync(path.join(out, name), JSON.stringify(value, null, 2), 'utf8');
const byId = new Map(active.map(e => [e.id, e]));
const texts = active.filter(e => e.type === 'text');
const label = id => {
  if (!id) return null;
  const element = byId.get(id);
  if (!element) return null;
  if (element.type === 'text') return element.text;
  const boundIds = new Set((element.boundElements || []).filter(b => b.type === 'text').map(b => b.id));
  return texts.filter(t => t.containerId === id || boundIds.has(t.id)).map(t => t.text).join(' / ') || null;
};
const arrows = active.filter(e => e.type === 'arrow').map(e => ({
  id: e.id,
  start: { binding: e.startBinding ?? null, label: label(e.startBinding?.elementId), arrowhead: e.startArrowhead ?? null },
  end: { binding: e.endBinding ?? null, label: label(e.endBinding?.elementId), arrowhead: e.endArrowhead ?? null },
  points: e.points, x: e.x, y: e.y, angle: e.angle,
  freeEndpoint: !e.startBinding || !e.endBinding,
  sameElementBinding: Boolean(e.startBinding && e.endBinding && e.startBinding.elementId === e.endBinding.elementId),
  missingTargets: [e.startBinding, e.endBinding].filter(b => b && !byId.has(b.elementId)).map(b => b.elementId),
}));
write('evidence.json', {
  source, sha256, sourceVersion: data.version,
  counts: { active: active.length, deleted: data.elements.length - active.length, texts: texts.length, arrows: arrows.length },
  texts: texts.map(t => ({ id: t.id, text: t.text, originalText: t.originalText, x: t.x, y: t.y, width: t.width, height: t.height, opacity: t.opacity, containerId: t.containerId, groupIds: t.groupIds, frameId: t.frameId })),
  arrows, elements: active, deletedElements: data.elements.filter(e => e.isDeleted), appState: data.appState,
  files: Object.fromEntries(Object.entries(data.files || {}).map(([id, file]) => [id, { ...file, dataURL: file.dataURL ? `[embedded data omitted here; ${file.dataURL.length} characters; original passed intact to renderer]` : undefined }])),
});
write('render-manifest.json', { source, sha256, status: 'incomplete' });
console.log(`Evidence directory: ${out}`);

const runtime = flags['--runtime'] || path.join(os.tmpdir(), 'codex-excalidraw-evaluator-0.18.1-1.63.0');
fs.mkdirSync(runtime, { recursive: true });
const require = createRequire(path.join(runtime, 'package.json'));
const versions = { '@excalidraw/excalidraw': '0.18.1', esbuild: '0.28.2', playwright: '1.63.0', react: '18.3.1', 'react-dom': '18.3.1' };
let ready = true;
for (const [pkg, version] of Object.entries(versions)) {
  try { if (JSON.parse(fs.readFileSync(path.join(runtime, 'node_modules', pkg, 'package.json'), 'utf8')).version !== version) ready = false; }
  catch { ready = false; }
}
if (!ready) {
  let npmCli = process.env.npm_execpath;
  if (!npmCli || !fs.existsSync(npmCli)) {
    const dirs = [path.dirname(process.execPath), ...(process.env.PATH || '').split(path.delimiter)];
    npmCli = dirs.map(d => path.join(d.replace(/^"|"$/g, ''), 'node_modules/npm/bin/npm-cli.js')).find(p => fs.existsSync(p));
  }
  if (!npmCli) throw new Error('npm not found. Install pinned packages in a cache with npm, then pass --runtime CACHE_DIR.');
  execFileSync(process.execPath, [npmCli, 'install', '--prefix', runtime, '--no-audit', '--no-fund', ...Object.entries(versions).map(([pkg, v]) => `${pkg}@${v}`)], { stdio: 'inherit' });
}
const esbuild = require('esbuild');
const { chromium } = require('playwright');
const bundleEntry = "import {exportToSvg} from '@excalidraw/excalidraw';window.exportToSvg=exportToSvg;";
const bundleKey = digest(Buffer.from(JSON.stringify(versions) + bundleEntry + 'minified-iife-production-v1'));
const bundlePath = path.join(runtime, `excalidraw-export-${bundleKey}.js`);
const bundle = fs.existsSync(bundlePath) ? fs.readFileSync(bundlePath, 'utf8') : esbuild.buildSync({
  stdin: { contents: bundleEntry, resolveDir: runtime },
  bundle: true, minify: true, format: 'iife', write: false, define: { 'process.env.NODE_ENV': JSON.stringify('production') },
}).outputFiles[0].text;
if (!fs.existsSync(bundlePath)) fs.writeFileSync(bundlePath, bundle);
let browser;
try {
  try { browser = await chromium.launch({ headless: true }); }
  catch (error) {
    if (!String(error).includes("Executable doesn't exist")) throw error;
    execFileSync(process.execPath, [require.resolve('playwright/cli'), 'install', 'chromium'], { stdio: 'inherit' });
    browser = await chromium.launch({ headless: true });
  }
  const page = await browser.newPage({ viewport: { width: 1600, height: 1200 } });
  const failures = [];
  page.on('requestfailed', r => failures.push({ url: r.url(), error: r.failure()?.errorText }));
  page.on('response', r => { if (r.status() >= 400) failures.push({ url: r.url(), status: r.status() }); });
  await page.setContent('<html><body style="margin:0;background:white"><div id="root"></div></body></html>');
  await page.addScriptTag({ content: bundle });
  const dimensions = await page.evaluate(async scene => {
    const svg = await window.exportToSvg({ elements: scene.elements, appState: { ...scene.appState, exportBackground: true, exportWithDarkMode: false }, files: scene.files || {} });
    document.querySelector('#root').append(svg);
    await document.fonts.ready;
    const rect = svg.getBoundingClientRect();
    return { width: Math.ceil(rect.width), height: Math.ceil(rect.height) };
  }, data);
  if (!dimensions.width || !dimensions.height) throw new Error('Empty rendered bounds.');
  const overviewScale = Math.min(1, 12000 / dimensions.width, 12000 / dimensions.height);
  await page.evaluate(scale => { const svg = document.querySelector('#root svg'); svg.style.width = `${parseFloat(svg.getAttribute('width')) * scale}px`; svg.style.height = `${parseFloat(svg.getAttribute('height')) * scale}px`; }, overviewScale);
  const overview = await page.locator('#root svg').screenshot({ path: path.join(out, 'overview.png'), timeout: 60000 });
  await page.evaluate(() => { const svg = document.querySelector('#root svg'); svg.style.width = ''; svg.style.height = ''; });
  const tiles = [];
  const tileW = 2200, tileH = 1600, overlap = 100;
  let n = 0;
  for (let y = 0; y < dimensions.height; y += tileH - overlap) {
    for (let x = 0; x < dimensions.width; x += tileW - overlap) {
      const width = Math.min(tileW, dimensions.width - x), height = Math.min(tileH, dimensions.height - y);
      const name = `tile-${String(++n).padStart(3, '0')}.png`;
      tiles.push({ file: name, x, y, width, height });
    }
  }
  if (overviewScale === 1) {
    // Crop the captured PNG, keeping the exact rendered pixels without more browser screenshots.
    const crops = await page.evaluate(async ({ png, tiles }) => {
      const image = new Image();
      image.src = `data:image/png;base64,${png}`;
      await image.decode();
      const canvas = document.createElement('canvas');
      return tiles.map(({ x, y, width, height }) => {
        canvas.width = width;
        canvas.height = height;
        canvas.getContext('2d').drawImage(image, x, y, width, height, 0, 0, width, height);
        return canvas.toDataURL('image/png').split(',')[1];
      });
    }, { png: overview.toString('base64'), tiles });
    for (let i = 0; i < tiles.length; i++) fs.writeFileSync(path.join(out, tiles[i].file), Buffer.from(crops[i], 'base64'));
  } else {
    // Large scenes use full-resolution captures; never crop detail from a scaled overview.
    for (const { file, x, y, width, height } of tiles) {
      await page.evaluate(({x, y}) => { const root = document.querySelector('#root'); root.style.position = 'absolute'; root.style.left = `${-x}px`; root.style.top = `${-y}px`; }, {x, y});
      await page.setViewportSize({ width, height });
      await page.screenshot({ path: path.join(out, file), timeout: 60000 });
    }
  }
  if (digest(fs.readFileSync(source)) !== sha256) throw new Error('Source changed during rendering; rerun against a stable snapshot.');
  write('render-manifest.json', { source, sha256, status: 'complete', dimensions, overviewScale, versions, networkFailures: failures, tiles });
  console.log(`Rendered overview and ${tiles.length} tiles. Inspect all images before evaluating. Network failures: ${failures.length}`);
} finally {
  if (browser) await browser.close();
}
