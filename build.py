"""Rebuilds index.html from engine.html, the timeline-built slides and the deck slides.
Works in either layout: everything in one folder (run: python3 build.py),
or the source/ and source/deck/slides/ folders (run: python3 source/build.py).
"""
import json, re, html, os, sys

BASE = os.path.dirname(os.path.abspath(__file__))
FLAT = os.path.exists(os.path.join(BASE, 'deck.json'))
DECK = BASE if FLAT else os.path.join(BASE, 'deck')
SLIDES = BASE if FLAT else os.path.join(DECK, 'slides')
ASSET = r'\1.svg' if FLAT else r'assets/\1.svg'

engine = open(os.path.join(BASE, 'engine.html')).read()
proto_src = open(os.path.join(BASE, 'american-century.proto.html')).read()
order = json.load(open(os.path.join(DECK, 'deck.json')))['order']


# ---------- deck stylesheet, scoped to carried-over slides ----------
def parse_css(s):
    i, n, out = 0, len(s), []
    while i < n:
        if s.startswith('/*', i):
            i = s.index('*/', i) + 2; continue
        if s[i].isspace():
            i += 1; continue
        j = s.index('{', i); sel = s[i:j].strip()
        depth, k = 1, j + 1
        while depth:
            if s[k] == '{': depth += 1
            elif s[k] == '}': depth -= 1
            k += 1
        out.append((sel, s[j + 1:k - 1])); i = k
    return out

css_out = []
for sel, body in parse_css(open(os.path.join(DECK, 'deck.css')).read()):
    if sel.startswith('@'):
        css_out.append(f'{sel} {{{body}}}'); continue
    if sel == ':root':
        continue
    keep = []
    for x in [t.strip() for t in sel.split(',')]:
        if x.startswith(('.paper', 'section', 'body')) or x.startswith('.fragment') or '.pg' in x:
            continue
        keep.append('.port ' + x)
    if keep:
        css_out.append(', '.join(keep) + ' {' + body + '}')
deck_css = '\n'.join(css_out)


# ---------- timeline-built slides from the prototype ----------
protos = {}
for m in re.finditer(r'<section class="scene" id="sc-([\w-]+)"[\s\S]*?</section>', proto_src):
    protos[m.group(1)] = m.group(0).replace('class="scene"', 'class="scene proto"', 1)
proto_map = {'cover': 'cover', 'roadmap': 'roadmap', 'y1898': 'y1898', 'act1': 'act1', 'powder-keg': 'powder', 'july-crisis': 'july'}

ROADMAP_NOTES = ('Here is the question that ties everything together: how did a young, mostly inward-looking republic become the most powerful nation on Earth, '
                 'and what did that rise cost? This is the whole road we will travel: a prologue that begins in 1898, the Great War in red, the twenty uneasy years '
                 'between the wars, World War II, and the long Cold War in blue, ending with Americans walking on the Moon in 1969. Each light standing on the timeline '
                 'is a moment we will visit.')

PROTO_CFG = {
    'cover': dict(year=1898, act='', stamp='', cam=[-1500, 1500, 4300], tgt=[1900, 250, -600], hud=False, quiet=[[0, 200, 1150, 840]]),
    'roadmap': dict(year=1898, act='Prologue', stamp='1898', cam=[4970, 3400, 6900], tgt=[4970, 380, -300], dur=3400, overview=True, quiet=[[0, 100, 1920, 360]]),
    'y1898': dict(year=1898, act='Prologue', stamp='1898', cam=[-60, 330, 1250], tgt=[-480, 20, 0], dur=3600, quiet=[[0, 100, 1100, 460], [100, 600, 1820, 920]]),
    'act1': dict(year=1914, act='Act I · The Great War', stamp='1914', cam=[1960, 150, 1380], tgt=[1790, 330, -300], dur=3400, monument='1914', letterbox=True, quiet=[[0, 330, 1350, 930]]),
    'powder-keg': dict(year=1914, act='Act I · The Great War', stamp='1914', cam=[2960, 620, 1580], tgt=[1880, 160, 0], dur=2600, beats=2, quiet=[[0, 100, 1300, 330], [100, 440, 1820, 940]]),
    'july-crisis': dict(year=1914, act='Act I · The Great War', stamp='1914', cam=[1560, 430, 940], tgt=[2080, 40, -260], dur=2600, beats=6, fuse=True, quiet=[[0, 100, 1500, 380], [100, 600, 1820, 930]]),
}

PAPER_INK = {'#1C1A17': '#F3EDE1', '#5A5145': '#A9A397', '#A1281F': '#E6685C', '#2F5F96': '#7FB0E6', '#A3621F': '#E89A45', '#E2D8C4': '#2C2925', '#D9CDB6': '#2C2925'}
JIT = [0, 150, -130, 250, -210, 90, -60, 190]


def aside_of(t):
    a = re.search(r'<aside>([\s\S]*?)</aside>', t)
    return html.unescape(a.group(1)).strip() if a else ''


TWEAKS = {
    'act4': [('style="--i:1;font-size:140px"', 'style="--i:1;font-size:104px"'), ('style="--i:8;margin:36px 0 0"', 'style="--i:8;margin:24px 0 0"')],
    'dday': [('style="--i:1;font-size:160px"', 'style="--i:1;font-size:128px"'), ('style="--i:7;margin:36px 0 0"', 'style="--i:7;margin:22px 0 0"'), ('class="col" style="gap:18px;margin:32px 0 0"', 'class="col" style="gap:10px;margin:22px 0 0"')],
    'why-ww1': [('class="col" style="flex:1;gap:30px"', 'class="col" style="flex:1;gap:20px"'), ('class="row" style="gap:64px;margin:44px 0 0"', 'class="row" style="gap:64px;margin:32px 0 0"'), ('class="lede" style="margin:4px 0 0"', 'class="lede" style="margin:4px 0 0;font-size:26px"')],
}


def port(sid, t):
    for a, b in TWEAKS.get(sid, []):
        assert a in t, (sid, a)
        t = t.replace(a, b)
    m = re.search(r'<section([^>]*)>([\s\S]*)</section>', t)
    attrs, inner = m.group(1), m.group(2)
    cm = re.search(r'class="([^"]*)"', attrs); cls = cm.group(1).split() if cm else []
    sm = re.search(r'style="([^"]*)"', attrs); style = sm.group(1) if sm else ''
    notes = aside_of(inner)
    inner = re.sub(r'\s*<aside>[\s\S]*?</aside>', '', inner)
    ym = re.search(r'<p class="tyear"[^>]*>(\d{4})</p>', inner)
    fm = re.search(r'<p class="foot">([^<]*)</p>', inner)
    stm = re.search(r'<p class="yearstamp"[^>]*>([^<]*)</p>', inner)
    for pat in [r'\s*<p class="yearstamp"[^>]*>[^<]*</p>', r'\s*<p class="foot">[^<]*</p>', r'\s*<div class="rail"></div>',
                r'\s*<div class="tfill"[^>]*></div>', r'\s*<div class="tdot"[^>]*></div>', r'\s*<p class="tyear"[^>]*>[^<]*</p>', r'\s*<p class="pg"></p>']:
        inner = re.sub(pat, '', inner)
    inner = re.sub(r'\s*<x-embed[\s\S]*?</x-embed>', '', inner)
    inner = inner.replace(' id="actyear"', '')
    inner = re.sub(r'/_blob/([0-9a-f]{32})', ASSET, inner)
    inner = re.sub(r'<img([^>]*?) src="((?:assets/)?[0-9a-f]{32}\.svg)"', r'<img\1 data-src="\2" decoding="async"', inner)
    if 'paper' in cls:
        for a, b in PAPER_INK.items():
            inner = re.sub(a, b, inner, flags=re.I)
    n = [0]
    def frag(mm):
        n[0] += 1
        return f'{mm.group(0)} data-beat="{n[0]}"'
    inner = re.sub(r'<\w+[^>]*?class="[^"]*\bfragment\b[^"]*"', frag, inner)
    for x in sorted(set(re.findall(r'\bid="([^"]+)"', inner)), key=len, reverse=True):
        y = f'{sid}-{x}'
        inner = inner.replace(f'id="{x}"', f'id="{y}"').replace(f'url(#{x})', f'url(#{y})').replace(f'href="#{x}"', f'href="#{y}"')
    content_cls = 'content' + (' blood' if 'blood' in cls else '')
    label = re.sub(r'<[^>]+>', ' ', (re.search(r'<h[12][^>]*>([\s\S]*?)</h[12]>', inner) or re.search(r'<p class="title[^"]*"[^>]*>([\s\S]*?)</p>', inner) or [None, sid])[1])
    label = html.escape(re.sub(r'\s+', ' ', html.unescape(label)).strip(), quote=True)
    section = f'<section class="scene port" id="sc-{sid}" aria-label="{label}">\n<div class="{content_cls}" style="{style}">{inner}\n</div>\n</section>'
    cfg = dict(year=int(ym.group(1)) if ym else 1969, act=html.unescape(fm.group(1)) if fm else '', stamp=stm.group(1) if stm else '',
               beats=1 + n[0], kind='port', veil=1, quiet=[[0, 0, 1250, 1080], [0, 0, 1920, 430]])
    if '<img' in inner: cfg['shot'] = 'map'
    elif 'black' in cls: cfg['shot'] = 'black'; cfg['tint'] = 'black'
    elif sid.startswith('act'): cfg['shot'] = 'act'
    else: cfg['shot'] = 'content'
    if 'blood' in cls: cfg['tint'] = 'blood'
    return section, cfg, notes


sections, configs = [], []
v, prev_year, run = 0, None, 0
for sid in order:
    t = open(os.path.join(SLIDES, f'{sid}.html')).read()
    if sid in proto_map:
        sec = protos[proto_map[sid]].replace(f'id="sc-{proto_map[sid]}"', f'id="sc-{sid}"', 1)
        cfg = dict(PROTO_CFG[sid]); cfg['kind'] = 'proto'; cfg['veil'] = 0
        notes = ROADMAP_NOTES if sid == 'roadmap' else aside_of(t)
    else:
        sec, cfg, notes = port(sid, t)
    cfg['id'] = sid; cfg['notes'] = notes
    run = run + 1 if cfg['year'] == prev_year else 0
    prev_year = cfg['year']
    cfg['jit'] = JIT[run % len(JIT)]
    if cfg.get('shot') == 'content':
        cfg['v'] = v; v += 1
    if sid == 'space':
        cfg['v'] = 1; cfg['noMoon'] = True
    if sid == 'earthrise':
        cfg['noMoon'] = True
    if sid == 'closing':
        cfg.update(shot='closing', hud=False, act='Epilogue', stamp='', quiet=[[0, 0, 1400, 1080]], dur=4200, tint=None, moonScale=2.4, veil=0)
    sections.append(sec); configs.append(cfg)

out = engine.replace('/*@DECKCSS@*/', deck_css)
out = out.replace('<!--@SCENES@-->', '\n'.join(sections))
out = out.replace('/*@CONFIG@*/', 'window.SCENES = ' + json.dumps(configs, ensure_ascii=False) + ';')
head, body = out.split('</style>', 1)
title_end = head.index('</title>') + len('</title>')
page = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
        '<meta name="description" content="A cinematic history in four acts: how a young republic became a superpower, 1898 to 1969.">\n'
        '<meta property="og:title" content="The American Century">\n'
        '<meta property="og:description" content="A cinematic history in four acts, 1898 to 1969.">\n'
        '<meta name="theme-color" content="#0D0F12">\n'
        '<link rel="icon" href="favicon.svg" type="image/svg+xml">\n'
        + head[:title_end] + head[title_end:] + '</style>\n</head>\n<body>' + body + '\n</body>\n</html>\n')
open(os.path.join(BASE, 'index.html') if FLAT else os.path.join(BASE, '..', 'index.html'), 'w').write(page)
print(len(configs), 'scenes;', len(out) // 1024, 'KB')
print([(c['id'], c.get('shot', 'proto'), c['year'], c['beats'] if 'beats' in c else 1) for c in configs])
