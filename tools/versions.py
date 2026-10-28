"""The versions of the Constitution of Nicaragua, 2014 to today, from Normas Jurídicas de Nicaragua.

Official whole texts (each published in La Gaceta, Diario Oficial, and kept by the Asamblea Nacional in Normaweb):
  2014-02-18  Texto ... con sus Reformas Incorporadas (Gaceta 32/2014), ordered by Ley 854 art. 50
  2022-09-28  Texto Consolidado, Digesto (Ley 1091, Gaceta 181/2022), consolidated to 2021-10-27
  2024-08-30  Texto Consolidado, Digesto (Ley 1196, Gaceta 161/2024), consolidated to 2024-03-13
  2025-02-18  Texto Íntegro (Gaceta 32/2025), ordered by Ley 1234 art. 15 (renumbered)
Between them each reform law is REPLAYED from the words it quotes; the next official text then checks the replay.

Every operation names the exact lines it takes from the amending law and stops the build if they are not there.
"""
import copy
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import parse as P  # noqa: E402
import source as S  # noqa: E402

START = r'^[“"]?El Presidente de la Rep'
STOP = r'^Dado en la Sala de Sesiones de la Asamblea Nacional, en la ciudad de Managua, a los diez y nueve'
SITE_NOTE = 'Observación:'
QUOTES = '“”"'

OFFICIAL = {
    '2014': 'C93CBD0FF408D07306257C8C004F6953',
    '2022': '799683A327E172CD062589E300549408',
    '2024': '51A99B32B259856106258B8C00742382',
    '2025': '76AEDE617857465D06258C360052B2E4',
}

# The laws, in the order they took effect. 'ops' rewrite the previous version; 'official' replaces it with a whole
# official text. in_force: every one of these laws enters into force on its publication in La Gaceta (its own last
# article, quoted in 'basis').
LAWS = [
    {'key': 'texto-2014', 'unid': OFFICIAL['2014'], 'kind': 'baseline', 'official': '2014',
     'author': 'Asamblea Nacional: texto con reformas incorporadas (2014)', 'email': 'texto-2014@asamblea-ni.invalid',
     'in_force': '2014-02-10', 'gazette': ('32', '2014-02-18'), 'approved': '2014-02-10',
     'basis': ('Ley N° 854 (Gaceta 26, 2014-02-10), art. 51: "entrará en vigencia a partir del día de su publicación en '
               'La Gaceta"; its art. 50 ordered this text with the reforms incorporated, published 2014-02-18. The text '
               'in force from 2014-02-10 is this one (the publication also replaced "Arto." by "Artículo", as art. 50 '
               'ordered).'),
     'title': 'Texto de la Constitución Política de la República de Nicaragua con sus Reformas Incorporadas',
     'tag': 'texto/2014'},
    {'key': 'ley-1014', 'unid': '5EDEF87CC36977F906258722004F1211', 'kind': 'amendment', 'number': '1014',
     'in_force': '2020-02-04', 'gazette': ('22', '2020-02-04'), 'approved': '2020-01-28',
     'ops': [('preamble',)],
     'basis': 'art. tercero: "entrará en vigencia a partir del día de su publicación en La Gaceta, Diario Oficial".'},
    {'key': 'ley-1057', 'unid': '259E2FCBC244949106258662007A06E6', 'kind': 'amendment', 'number': '1057',
     'in_force': '2021-01-19', 'gazette': ('12', '2021-01-19'), 'approved': '2021-01-18',
     'ops': [('articles', ['37'])],
     'basis': 'art. tercero: "entrará en vigencia a partir del día de su publicación en La Gaceta, Diario Oficial".'},
    {'key': 'ley-1091', 'unid': '2BA40AEED64D0549062588CC00768418', 'kind': 'consolidation', 'number': '1091',
     'official': '2022', 'in_force': '2022-09-28', 'gazette': ('181', '2022-09-28'), 'approved': '2021-10-27',
     'basis': 'art. 10: "La presente Ley entrará en vigencia a partir de su publicación en La Gaceta, Diario Oficial".',
     'tag': 'digesto/2022'},
    {'key': 'ley-1185', 'unid': '6F652D291FEBC77006258AB40069B6C5', 'kind': 'amendment', 'number': '1185',
     'in_force': '2024-01-19', 'gazette': ('10', '2024-01-19'), 'approved': '2024-01-16',
     'ops': [('articles', ['97'])],
     'basis': 'art. segundo: "entrará en vigencia a partir de la fecha de su publicación en La Gaceta, Diario Oficial".'},
    {'key': 'ley-1186', 'unid': '8E897220BA33496406258AA9006FC1D8', 'kind': 'amendment', 'number': '1186',
     'in_force': '2024-01-19', 'gazette': ('10', '2024-01-19'), 'approved': '2024-01-16',
     'ops': [('articles', ['165'])], 'second_reading': True},
    {'key': 'ley-1187', 'unid': '5D94AB00AF6773AC06258AAC004B32D7', 'kind': 'amendment', 'number': '1187',
     'in_force': '2024-01-22', 'gazette': ('11', '2024-01-22'), 'approved': '2024-01-17',
     'ops': [('articles', ['159'])], 'second_reading': True},
    {'key': 'ley-1188', 'unid': '7A49A016CD1ABCA906258AAC004D31F6', 'kind': 'amendment', 'number': '1188',
     'in_force': '2024-01-22', 'gazette': ('11', '2024-01-22'), 'approved': '2024-01-17',
     'ops': [('repeal_item', '138', '9)', 'd)')], 'second_reading': True},
    {'key': 'ley-1190', 'unid': 'B7DBCF55D795103406258AAC004E2D4E', 'kind': 'amendment', 'number': '1190',
     'in_force': '2024-01-22', 'gazette': ('11', '2024-01-22'), 'approved': '2024-01-18',
     'ops': [('articles', ['21'])], 'second_reading': True},
    {'key': 'ley-1196', 'unid': '7BAB8534B193AA9606258B89005E93F0', 'kind': 'consolidation', 'number': '1196',
     'official': '2024', 'in_force': '2024-08-30', 'gazette': ('161', '2024-08-30'), 'approved': '2024-03-13',
     'basis': 'art. 11: "La presente Ley entrará en vigencia a partir de su publicación en La Gaceta, Diario Oficial".',
     'tag': 'digesto/2024'},
    {'key': 'ley-1234', 'unid': '2798FEE6DACD52B506258C360051E856', 'kind': 'reform', 'number': '1234',
     'official': '2025', 'in_force': '2025-02-18', 'gazette': ('32', '2025-02-18'), 'approved': '2025-01-30',
     'basis': ('art. decimoquinto: "entrará en vigencia una vez sea publicada en La Gaceta, Diario Oficial"; the same '
               'issue (Gaceta 32, 2025-02-18) prints the Texto Íntegro it ordered, "con las reformas incorporadas y la '
               'respectiva renumeración de Títulos, Capítulos y Artículos".'),
     'tag': 'texto/2025'},
    {'key': 'ley-1268', 'unid': '0A8606CDF5AC451F06258D5C005CBEE8', 'kind': 'amendment', 'number': '1268',
     'in_force': '2026-01-16', 'gazette': ('09', '2026-01-16'), 'approved': '2026-01-14',
     'ops': [('articles', ['23', '25'])],
     'basis': 'art. segundo: "entrará en vigencia a partir de la fecha de su publicación en La Gaceta, Diario Oficial".'},
    {'key': 'ley-1269', 'unid': '1C542C6C8834FF1206258D5C007918C4', 'kind': 'amendment', 'number': '1269',
     'in_force': '2026-01-16', 'gazette': ('09', '2026-01-16'), 'approved': '2026-01-14',
     'ops': [('articles', ['159', '160']), ('repeal_item', '132', '8)', 'b)')],
     'basis': 'art. cuarto: "entrará en vigencia a partir de la fecha de su publicación en La Gaceta, Diario Oficial".',
     'reading_rule': ('art. tercero: "En todo el ordenamiento jurídico del país, donde se lea Procuraduría General de '
                      'la República, deberá leerse Procuraduría General de Justicia." A rule of reading, not a textual '
                      'amendment: the other articles keep their printed words here.')},
    {'key': 'ley-1270', 'unid': 'F3E19EB1F057532B06258D5C005C0CE6', 'kind': 'amendment', 'number': '1270',
     'in_force': '2026-01-19', 'gazette': ('10', '2026-01-19'), 'approved': '2026-01-15',
     'ops': [('item', '125', '10)')],
     'basis': 'art. segundo: "entrará en vigencia a partir de la fecha de su publicación en La Gaceta, Diario Oficial".'},
    {'key': 'ley-1271', 'unid': '2070D3F189509FC106258D5C005C3CB6', 'kind': 'amendment', 'number': '1271',
     'in_force': '2026-01-19', 'gazette': ('10', '2026-01-19'), 'approved': '2026-01-15',
     'ops': [('first_paragraph', '118')],
     'basis': 'art. segundo: "entrará en vigencia a partir de la fecha de su publicación en La Gaceta, Diario Oficial".'},
]

SECOND_READING_BASIS = ('art. segundo: "Se mandata la publicación de la primera aprobación en primera legislatura en La '
                        'Gaceta, Diario Oficial. Una vez sea aprobada en segunda legislatura, la presente Ley ... '
                        'entrará en vigencia a partir de la fecha de su publicación en La Gaceta, Diario Oficial." The '
                        'clause was carried over from the first-reading bill: this publication is the promulgated law '
                        '("Téngase como Ley de la República"), and the Digesto consolidation of 2024 (Ley 1196) '
                        'incorporates it as "publicada en La Gaceta" on this day. In force on this publication.')


# ---- official texts ----------------------------------------------------------------------------------------------------
def official(unid: str) -> dict:
    ls = P.lines(S.norm(unid))
    v = P.constitution(ls, START, STOP)
    i0 = next(i for i, l in enumerate(ls) if re.search(START, l))
    i1 = next(i for i, l in enumerate(ls) if i > i0 and re.search(STOP, l))
    closing = [l for l in ls[i1:] if not l.startswith(SITE_NOTE)]
    v['header'] = ls[:i0]
    v['closing'] = closing
    return v


# ---- replay ------------------------------------------------------------------------------------------------------------
def unquote_block(ls: list) -> list:
    """Strip the opening quote of the first line and the closing quote of the last, as printed: ...". -> ... ."""
    out = list(ls)
    if not out[0] or out[0][0] not in QUOTES:
        raise SystemExit(f'quoted block does not open with a quote: {out[0][:60]}')
    out[0] = out[0][1:]
    last = out[-1]
    m = re.search(r'[”"](\.?)\s*$', last)
    if not m:
        raise SystemExit(f'quoted block does not close with a quote: {last[-60:]}')
    out[-1] = last[:m.start()] + m.group(1)
    return out


def quoted_block(law_lines: list, first: str) -> list:
    """The lines of the law from the one starting with a quote then `first`, to the first line ending in a quote."""
    i = next((i for i, l in enumerate(law_lines) if re.match('[' + QUOTES + ']' + first, l)), None)
    if i is None:
        raise SystemExit(f'no quoted block starting {first!r}')
    own = re.compile(r'^[“"]?Artículo (segundo|tercero|cuarto|quinto)\b', re.I)
    for j in range(i, len(law_lines)):
        if re.search(r'[”"]\.?\s*$', law_lines[j]):
            return unquote_block(law_lines[i:j + 1])
        if j + 1 < len(law_lines) and own.match(law_lines[j + 1]):
            # Normaweb lost the closing quote (Ley 1186: the Gaceta prints 'leyes."' and Normaweb moves the quote to
            # the next article's heading). The law's own next article ends the quoted text.
            block = list(law_lines[i:j + 1])
            block[-1] = block[-1] + '"'
            UNCLOSED.append((first, law_lines[j + 1][:40]))
            return unquote_block(block)
    raise SystemExit(f'quoted block starting {first!r} never closes')


UNCLOSED = []


def split_articles(block: list) -> dict:
    """{'37': [paragraphs]} from a quoted block of whole articles ("Artículo 37 ..." / "Articulo 23 ...")."""
    out, cur = {}, None
    for l in block:
        m = re.match(r'^Art[ií]culo\s+(\d+)(?:\s*(bis|ter|quater))?\s*\.?-?\s*(.*)$', l)
        if m:
            cur = P.key_of(m.group(1), m.group(2))
            out[cur] = [m.group(3)] if m.group(3) else []
        elif cur is None:
            raise SystemExit(f'text before the first article in a quoted block: {l[:60]}')
        else:
            out[cur].append(l)
    return out


def art(v: dict, key: str) -> list:
    hit = [a for a in v['articles'] if a[0] == key]
    if len(hit) != 1:
        raise SystemExit(f'article {key} not found once')
    return hit[0]


def apply(law: dict, prev: dict) -> tuple:
    v = copy.deepcopy(prev)
    ls = P.lines(S.norm(law['unid']))
    changed = []
    for op in law['ops']:
        if op[0] == 'preamble':
            new = quoted_block(ls, 'Preámbulo')
            pre = v['preamble']
            i = pre.index('Preámbulo')
            # the law quotes the preamble from "Preámbulo" to "POR LA PATRIA, ... POR LA PAZ"; the promulgation
            # lines after it ("Promulgamos la siguiente", the title) are not part of the reform and stay.
            j = next(j for j in range(i, len(pre)) if pre[j].startswith('POR LA PATRIA, POR LA REVOLUCIÓN'))
            if not new[-1].startswith('POR LA PATRIA, POR LA REVOLUCIÓN'):
                raise SystemExit('Ley 1014: quoted preamble does not end with "POR LA PATRIA ..."')
            v['preamble'] = pre[:i] + new + pre[j + 1:]
            changed.append('preambulo')
        elif op[0] == 'articles':
            first = op[1][0]
            block = quoted_block(ls, rf'Art[ií]culo {first}\b')
            arts = split_articles(block)
            if sorted(arts) != sorted(op[1]):
                raise SystemExit(f'{law["key"]}: quoted articles {sorted(arts)} != {op[1]}')
            for k in op[1]:
                art(v, k)[2][:] = arts[k]
                changed.append(k)
        elif op[0] == 'repeal_item':
            _, key, num, lit = op
            body = art(v, key)[2]
            i = body.index(next(l for l in body if l.startswith(num + ' ')))
            j = next(j for j in range(i + 1, len(body)) if body[j].startswith(lit + ' '))
            body[j] = lit + ' Derogado.'
            changed.append(key)
        elif op[0] == 'item':
            _, key, num = op
            block = [l for l in quoted_block(ls, rf'Art[ií]culo {key}\b')]
            new = [l for l in block if l.startswith(num + ' ')]
            if len(new) != 1:
                raise SystemExit(f'{law["key"]}: item {num} not quoted once')
            body = art(v, key)[2]
            i = body.index(next(l for l in body if l.startswith(num + ' ')))
            body[i] = new[0]
            changed.append(key)
        elif op[0] == 'first_paragraph':
            _, key = op
            i = next(i for i, l in enumerate(ls) if re.match(rf'[{QUOTES}]Art[ií]culo {key}\b', l))
            m = re.match(rf'[{QUOTES}]Art[ií]culo {key}\s+(.*)$', ls[i])
            if not re.match(r'^[….]{1,3}/?\s*[”"]?$', ls[i + 1]):
                raise SystemExit(f'{law["key"]}: first paragraph of {key} not followed by an ellipsis line')
            art(v, key)[2][0] = m.group(1)
            changed.append(key)
        else:
            raise SystemExit(f'unknown op {op}')
    return v, changed


def build_versions() -> list:
    """[(law, version, changed)] in order. version: preamble, articles, structure, header, closing."""
    out = []
    prev = None
    for law in LAWS:
        if 'official' in law:
            v = official(law['unid'] if law['kind'] == 'baseline' else OFFICIAL[law['official']])
            changed = None
        else:
            v, changed = apply(law, prev)
        out.append((law, v, changed))
        prev = v
    return out


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    vs = build_versions()
    for law, v, ch in vs:
        print(law['key'], law['in_force'], len(v['articles']), 'articles', ch)
