"""Fetching from Normas Jurídicas de Nicaragua (legislacion.asamblea.gob.ni, Asamblea Nacional), with a disk cache.

Every response is cached under cache/ (self-gitignored), negative answers too. One request at a time, with curl
(Python's TLS fails on this machine and the host is plain http). A browser User-Agent and gzip are sent.

  view_docs()           every document row of the Normaweb default view (category, date, number, title, UNID)
  norm(unid)            the official text page (xpNorma.xsp) of one document
"""
import gzip
import hashlib
import json
import os
import re
import subprocess
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
CACHE = HERE / 'cache'
HOST = 'http://legislacion.asamblea.gob.ni'
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36'
LOG = CACHE / 'requests.jsonl'
OFFLINE = False


def _init():
    CACHE.mkdir(exist_ok=True)
    gi = CACHE / '.gitignore'
    if not gi.exists():
        gi.write_text('*\n', encoding='utf-8')
    top = HERE / '.gitignore'
    if not top.exists():
        top.write_text('cache/\n__pycache__/\nrepo-build/\n', encoding='utf-8')


def get(url: str) -> bytes:
    """GET with the cache. Returns the body (decompressed). Raises on a non-200 answer (cached as negative)."""
    _init()
    key = hashlib.sha256(url.encode()).hexdigest()[:24]
    body, meta = CACHE / f'{key}.gz', CACHE / f'{key}.json'
    if meta.exists():
        m = json.loads(meta.read_text(encoding='utf-8'))
        if m['status'] != 200:
            raise IOError(f'{url}: cached HTTP {m["status"]}')
        return gzip.decompress(body.read_bytes())
    if OFFLINE:
        raise IOError(f'offline and not cached: {url}')
    tmp = CACHE / f'{key}.part'
    for attempt in range(4):
        r = subprocess.run(['curl', '-s', '--compressed', '-m', '180', '-A', UA, '-o', str(tmp), '-w', '%{http_code}',
                            url], capture_output=True, text=True)
        status = int(r.stdout or 0)
        if status == 200 or status in (404, 410):
            break
        time.sleep(5 * (attempt + 1))
    data = tmp.read_bytes() if tmp.exists() else b''
    if tmp.exists():
        tmp.unlink()
    body.write_bytes(gzip.compress(data, mtime=0))
    m = {'url': url, 'status': status, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(),
         'retrieved': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}
    meta.write_text(json.dumps(m, ensure_ascii=False), encoding='utf-8')
    with open(LOG, 'a', encoding='utf-8') as f:
        f.write(json.dumps(m, ensure_ascii=False) + '\n')
    if status != 200:
        raise IOError(f'{url}: HTTP {status}')
    return data


def retrieved() -> str:
    """The last retrieval day in the cache (the documentation commit's date)."""
    days = []
    for p in CACHE.glob('*.json'):
        try:
            days.append(json.loads(p.read_text(encoding='utf-8'))['retrieved'][:10])
        except (KeyError, ValueError):
            pass
    return max(days)


def requests_made() -> int:
    return sum(1 for p in CACHE.glob('*.json') if p.name != 'requests.json')


def _entry_values(e):
    out = []
    for x in e['entrydata']:
        for k in ('text', 'number', 'datetime'):
            if k in x:
                out.append('|'.join(str(v) for v in x[k].values()))
                break
        else:
            out.append('')
    return out


def view_docs() -> list:
    """All documents of the default view, as dicts: category, date (YYYYMMDD), number, title, unid.
    Read in pages of the expanded view (ReadViewEntries JSON). Categories are top-level rows."""
    top = json.loads(get(f'{HOST}/Normaweb.nsf/$defaultview?ReadViewEntries&Count=100&CollapseView&outputformat=JSON')
                     .decode('utf-8'))
    cats = {}
    for e in top['viewentry']:
        v = _entry_values(e)
        if len(v) >= 2 and v[1]:
            cats[e['@position']] = (v[1], int(e.get('@descendants') or 0))
    docs = []
    for pos, (cat, n) in sorted(cats.items(), key=lambda kv: int(kv[0])):
        start = pos
        while True:
            url = (f'{HOST}/Normaweb.nsf/$defaultview?ReadViewEntries&Start={start}&Count=1000&ExpandView'
                   f'&outputformat=JSON')
            page = json.loads(get(url).decode('utf-8')).get('viewentry', [])
            last = None
            stop = False
            for e in page:
                p = e['@position']
                if p.split('.')[0] != pos:
                    stop = True
                    break
                last = p
                if e.get('@unid') and p.count('.') == 2:
                    v = _entry_values(e)
                    docs.append({'category': cat, 'date': v[1], 'number': v[4], 'title': v[5], 'unid': e['@unid'],
                                 'position': p})
            if stop or not page or last is None or len(page) < 1000:
                break
            # next page starts after the last row read
            a, b, c = (last.split('.') + ['0', '0'])[:3]
            start = f'{a}.{b}.{int(c) + 1}' if last.count('.') == 2 else f'{a}.{int(b) + 1}'
    return docs


def norm(unid: str) -> str:
    url = f'{HOST}/Normaweb.nsf/xpNorma.xsp?documentId={unid}&action=openDocument'
    return get(url).decode('utf-8')


def norm_url(unid: str) -> str:
    return f'{HOST}/Normaweb.nsf/xpNorma.xsp?documentId={unid}&action=openDocument'


def gazette_link(page: str) -> str:
    m = re.search(r'href="(http://legislacion\.asamblea\.gob\.ni/gacetas/[^"]+)"', page)
    return m.group(1) if m else ''
