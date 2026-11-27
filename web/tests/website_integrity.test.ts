import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';

const WEBSITE_DIR = path.resolve(process.cwd(), 'website');
const html = fs.readFileSync(path.join(WEBSITE_DIR, 'index.html'), 'utf8');
const css = fs.readFileSync(path.join(WEBSITE_DIR, 'style.css'), 'utf8');
const js = fs.readFileSync(path.join(WEBSITE_DIR, 'script.js'), 'utf8');
const readme = fs.readFileSync(path.join(WEBSITE_DIR, 'README.md'), 'utf8');

test('all required static website files and local assets exist', () => {
  const requiredFiles = [
    'index.html',
    'style.css',
    'script.js',
    'sitemap.xml',
    'robots.txt',
    'README.md',
    'assets/icon.png',
    'assets/icon-64.png',
    'assets/preview_main_dark.png',
    'assets/preview_main_light.png',
    'assets/preview_markup_showcase.png',
    'assets/preview_adjust_color.png',
    'assets/preview_updater.png',
  ];

  for (const rel of requiredFiles) {
    const fullPath = path.join(WEBSITE_DIR, rel);
    assert.equal(fs.existsSync(fullPath), true, `Missing required file: ${rel}`);
    assert.ok(fs.statSync(fullPath).size > 0, `File is empty: ${rel}`);
  }
});

test('copy rule: zero em dashes anywhere in website files', () => {
  for (const [name, content] of [
    ['index.html', html],
    ['style.css', css],
    ['script.js', js],
    ['README.md', readme],
  ]) {
    assert.equal(content.includes('\u2014'), false, `Found em dash in ${name}`);
    assert.equal(content.includes('&mdash;'), false, `Found HTML em dash entity in ${name}`);
  }
});

test('all img tags specify alt, width, height, and valid local asset paths', () => {
  const imgTags = html.match(/<img\b[^>]*>/gi) ?? [];
  assert.ok(imgTags.length >= 8, 'Expected hero, icon, footer icon, gallery, and lightbox images');

  for (const tag of imgTags) {
    assert.match(tag, /\balt="[^"]+"/i, `Missing non-empty alt attribute: ${tag}`);
    assert.match(tag, /\bwidth="\d+"/i, `Missing numeric width attribute: ${tag}`);
    assert.match(tag, /\bheight="\d+"/i, `Missing numeric height attribute: ${tag}`);
    const srcMatch = tag.match(/\bsrc="([^"]+)"/i);
    assert.ok(srcMatch, `Missing src attribute: ${tag}`);
    const assetPath = path.join(WEBSITE_DIR, srcMatch[1]);
    assert.equal(fs.existsSync(assetPath), true, `Referenced image does not exist: ${srcMatch[1]}`);
  }

  const descMatch = html.match(/<meta\s+name="description"\s+content="([^"]+)"/i);
  assert.ok(descMatch, 'Missing meta description');
  assert.ok(descMatch[1].length >= 120 && descMatch[1].length <= 160, `Meta description length ${descMatch[1].length} outside 120-160`);
});

test('contains all required sections, shortcuts, FAQ questions, and trademark disclaimer', () => {
  const requiredFragments = [
    'macOS Preview, on Linux and Windows.',
    'preview-app_1.7.3_amd64.deb',
    'Preview-Setup-v1.7.3.exe',
    'Universal Document &amp; Image Engine',
    'Markup &amp; Annotation Suite',
    'Precision Productivity Tools',
    'Pro Image Adjustment Lab',
    'Sparkle-Style In-App Updater',
    'Eye of GNOME',
    'test_preview_features.py',
    'Is it free?',
    'Does it edit PDFs permanently?',
    'Does it work offline?',
    'Is redaction secure?',
    'Which Linux distros are supported?',
    'How do I update?',
    'How do I report a bug?',
    'Built by Shivam Prasad',
    'TriviLabs.in',
    'macOS and Preview are trademarks of Apple Inc. This project is independent and not affiliated with Apple.',
  ];

  for (const fragment of requiredFragments) {
    assert.equal(html.includes(fragment), true, `Missing required content fragment: ${fragment}`);
  }
});

test('contains zero external JS frameworks or tracking scripts', () => {
  assert.equal(/https?:\/\/.*(react|vue|angular|jquery|gtag|analytics|googletagmanager)/i.test(html), false);
});

test('scroll reveal uses IntersectionObserver with .reveal and .revealed classes and reduced-motion support', () => {
  const majorSectionIds = [
    'top',
    'install',
    'features',
    'gallery',
    'compare',
    'shortcuts',
    'architecture',
    'faq',
    'contributing',
  ];

  for (const id of majorSectionIds) {
    const sectionPattern = new RegExp(`<section\\b[^>]*class="[^"]*\\breveal\\b[^"]*"[^>]*id="${id}"`, 'i');
    assert.match(html, sectionPattern, `Expected <section id="${id}"> to have class "reveal"`);
  }
  assert.match(html, /<section\b[^>]*class="[^"]*\breveal\b[^"]*\brevealed\b[^"]*"[^>]*id="top"/i);

  assert.match(js, /new IntersectionObserver\(/);
  assert.match(js, /observer\.observe\(/);
  assert.match(js, /observer\.unobserve\(/);
  assert.match(js, /classList\.add\('revealed'\)/);
  assert.match(js, /--reveal-delay/);
  assert.match(js, /prefers-reduced-motion:\s*reduce/);
  assert.match(js, /hashchange/);
  assert.match(css, /\.reveal\s*\{[\s\S]*opacity:\s*0;[\s\S]*transform:\s*translateY\(20px\);[\s\S]*transition:/);
  assert.match(css, /\.reveal\.revealed,\s*\.revealed,\s*\.reveal \.reveal\.revealed\s*\{[\s\S]*opacity:\s*1;[\s\S]*transform:\s*translateY\(0\);/);
  assert.match(css, /@media\s*\(prefers-reduced-motion:\s*reduce\)/);
});
