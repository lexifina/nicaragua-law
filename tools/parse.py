"""Parsing Normaweb text pages (legislacion.asamblea.gob.ni) into lines and constitution versions.

lines(page)          the official text (the span view:_id1:computedField1) as a list of non-empty lines: one line per
                     <br>/<div>/<p>-separated run of text, tags removed, entities decoded, runs of white space made one
                     space, ends stripped. Nothing else is normalised.
constitution(lines)  {'preamble': [...], 'articles': [(key, printed, [paragraphs])], 'structure': [(heading, key)]}
"""
import html
import re

NBSP = ' '
BODY = re.compile(r'<span id="view:_id1:computedField1"[^>]*>(.*?)</span>(?:<div style="background-color:rgb\(0,64,128\)">'
                  r'|<table id="view:_id1:fileDownload1")', re.S)
BREAK = re.compile(r'<br\s*/?>|</?div[^>]*>|</?p[^>]*>|</?tr[^>]*>|</?table[^>]*>|</?li[^>]*>|</?ul[^>]*>', re.I)
TAG = re.compile(r'<[^>]+>')
WS = re.compile(r'[\s ​﻿]+')

# "Artículo 1", "Artículo 12 ", "Arto. 5", "Artículo 131 bis" at the start of a line, then the text.
ART = re.compile(r'^(?:Artículo|Arto\.)\s+(\d+)(?:\s*(bis|ter|quater))?\s*\.?-?\s*(.*)$')
HEAD = re.compile(r'^(TÍTULO|TITULO|CAPÍTULO|CAPITULO|SECCIÓN|SECCION)\b')


def body_html(page: str) -> str:
    m = BODY.search(page)
    if not m:
        raise ValueError('no computedField1 body')
    return m.group(1)


def lines(page: str) -> list:
    out = []
    for chunk in BREAK.split(body_html(page)):
        t = html.unescape(TAG.sub('', chunk))
        t = WS.sub(' ', t).strip()
        if t:
            out.append(t)
    return out


def raw_words(page: str) -> list:
    """Independent extractor for the word check: every text node of the body, letters and digits only, casefolded.
    No line logic, no article logic."""
    t = html.unescape(TAG.sub('', re.sub(r'<(?:br|/?div|/?p|/?tr|/?td|/?li)\b[^>]*>', ' ', body_html(page), flags=re.I)))
    return re.findall(r'[^\W_]+', t.casefold())


def key_of(num: str, suffix: str | None) -> str:
    return num + (('-' + suffix) if suffix else '')


def constitution(ls: list, start: str, stop: str) -> dict:
    """Split the lines between the line matching `start` and the line matching `stop` (exclusive) into the preamble,
    articles and headings. A heading line (TÍTULO/CAPÍTULO/SECCIÓN) and the title line after it belong to the structure,
    not to the article before."""
    i0 = next(i for i, l in enumerate(ls) if re.search(start, l))
    i1 = next(i for i, l in enumerate(ls) if i > i0 and re.search(stop, l))
    body = ls[i0:i1]
    preamble, articles, structure = [], [], []
    cur = None
    pending = []
    seen = set()
    for l in body:
        m = ART.match(l)
        if m:
            k = key_of(m.group(1), m.group(2))
            if k in seen:
                raise ValueError(f'article {k} twice')
            seen.add(k)
            for h in pending:
                structure.append((h, k))
            pending = []
            printed = m.group(1) + ((' ' + m.group(2)) if m.group(2) else '')
            cur = [k, printed, [m.group(3)] if m.group(3) else []]
            articles.append(cur)
            continue
        if cur is None:
            if HEAD.match(l) or (pending and l.isupper()):
                pending.append(l)
            else:
                preamble.extend(pending)
                pending = []
                preamble.append(l)
            continue
        if HEAD.match(l) or (pending and l.isupper()):
            pending.append(l)
            continue
        if pending:
            # a run of upper-case lines that was not a heading after all
            cur[2].extend(pending)
            pending = []
        cur[2].append(l)
    if pending:
        articles[-1][2].extend(pending)
    return {'preamble': preamble, 'articles': articles, 'structure': structure}
