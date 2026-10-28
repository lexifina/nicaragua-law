"""Builds the Nicaragua git-for-law repository: the Constitución Política, 2014 to today, from Normas Jurídicas de
Nicaragua (legislacion.asamblea.gob.ni, Asamblea Nacional).

    python -I -X utf8 build.py --repo DIR --today YYYY-MM-DD [--offline] [--wip] [--verify-rebuild]

One commit per law per in-force day, authored by the law, at noon in Managua. The versions are made by versions.py
(official whole texts, and reform laws replayed between them). The history is written with one `git fast-import`;
every commit message is passed as bytes (no CRs). The documentation commit is dated by the data's retrieval day.
Standard library only.
"""
import argparse
import datetime as dt
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import parse as P  # noqa: E402
import source as S  # noqa: E402
import versions as V  # noqa: E402

FOLDER = 'constitucion'
COMMITTER = ('Lexifina', 'nicaragua-law@lexifina.com')
PUBLISHER = 'Asamblea Nacional de Nicaragua (Normas Jurídicas de Nicaragua)'


# ---- dates -------------------------------------------------------------------------------------------------------------
def offset(day: dt.date) -> str:
    """Nicaragua: UTC-6, with summer time (UTC-5) only in 2005 (10 April - 2 October) and 2006 (30 April - 1 October),
    from 2 a.m.; the commit time is noon, so the change days are on the new offset (start <= day < end)."""
    dst = {2005: (dt.date(2005, 4, 10), dt.date(2005, 10, 2)), 2006: (dt.date(2006, 4, 30), dt.date(2006, 10, 1))}
    if day.year in dst and dst[day.year][0] <= day < dst[day.year][1]:
        return '-0500'
    return '-0600'


def stamp(day: str, sec: int = 0) -> str:
    """Git raw date for noon local time on `day`, `sec` seconds after."""
    d = dt.date.fromisoformat(day)
    off = offset(d)
    sign = -1 if off[0] == '-' else 1
    hours = int(off[1:3])
    local = dt.datetime(d.year, d.month, d.day, 12, 0, sec, tzinfo=dt.timezone(dt.timedelta(hours=sign * hours)))
    return f'{int(local.timestamp())} {off}'


# ---- files -------------------------------------------------------------------------------------------------------------
def fname(key: str) -> str:
    """'37' -> 'articulo-037.md'; '46-ter' -> 'articulo-046-ter.md'"""
    n, _, suf = key.partition('-')
    return f'articulo-{int(n):03d}' + (f'-{suf}' if suf else '') + '.md'


def files_of(v: dict) -> dict:
    d = {'preambulo.md': '\n'.join(v['preamble']) + '\n',
         'cierre.md': '\n'.join(v['closing']) + '\n',
         'estructura.md': ''.join(f'{h} [artículo {k}]\n' for h, k in v['structure'])}
    for key, printed, body in v['articles']:
        d[fname(key)] = f'# Artículo {printed}\n\n' + '\n'.join(body) + '\n'
    return d


# ---- messages ----------------------------------------------------------------------------------------------------------
def law_name(law: dict) -> str:
    return f'Ley N° {law["number"]}'


def author(law: dict) -> tuple:
    if law['kind'] == 'baseline':
        return law['author'], law['email']
    return law_name(law), f'ley-{law["number"]}@asamblea-ni.invalid'


def law_title(law: dict) -> str:
    ls = P.lines(S.norm(law['unid']))
    return ls[0]


def words(s: str) -> list:
    return re.findall(r'[^\W_]+', s.casefold())


def changed_files(prev: dict | None, cur: dict) -> list:
    a = files_of(prev) if prev else {}
    b = files_of(cur)
    return sorted(k for k in set(a) | set(b) if a.get(k) != b.get(k))


def message(law: dict, v: dict, prev: dict | None, changed: list) -> str:
    title = law_title(law) if law['kind'] != 'baseline' else law['title']
    files = changed_files(prev, v)
    src = S.norm_url(law['unid'])
    gaz = S.gazette_link(S.norm(law['unid']))
    if law['kind'] == 'baseline':
        lines = ['Constitución: texto con reformas incorporadas (2014)', '',
                 f'{law["title"]}, published in La Gaceta, Diario Oficial N° {law["gazette"][0]} of '
                 f'{law["gazette"][1]}.', '',
                 'The first version in this record: the whole Constitution of 1987 with the reforms of Leyes N° 192 '
                 '(1995), 330 (2000), 490 (2004), 520, 521 and 527 (2005) and 854 (2014) incorporated, as ordered by '
                 'Ley N° 854 art. 50. Its words are older than 2014 in part, but every line is credited here to this '
                 'official text: read blame on this commit as "in force on 10 February 2014 at the latest".', '',
                 f'{len(v["articles"])} articles.', '', 'Kind: baseline', f'Consolidated: {law["gazette"][1]}']
    elif law['kind'] == 'amendment':
        what = ', '.join('el preámbulo' if c == 'preambulo' else f'artículo {c}' for c in changed)
        lines = [f'Constitución: {what} ({law_name(law)})'[:72], '', title + '.', '',
                 'REPLAYED: the previous version with the words this law quotes put in place ('
                 + {'1188': 'it repeals literal d) of numeral 9) of article 138; the official consolidation of 2024 '
                            'prints a repealed literal as "d) Derogado.", and so does this replay',
                    '1269': 'it replaces articles 159 and 160 and repeals literal b) of numeral 8) of article 132, '
                            'printed "b) Derogado." as the Digesto prints repealed literals',
                    '1270': 'it replaces numeral 10) of article 125; the law quotes only that numeral',
                    '1271': 'it replaces the first paragraph of article 118; the law quotes only that paragraph',
                    }.get(law['number'], 'whole articles replaced by the quoted text') + '). '
                 + ('The next official text (the Digesto consolidation of 2024, Ley N° 1196) checks this replay.'
                    if law['in_force'] < '2024-08-30' and law['in_force'] > '2022-09-28' else
                    'The next official text (the Digesto consolidation of 2022, Ley N° 1091) checks this replay.'
                    if law['in_force'] < '2022-09-28' else
                    'No official consolidation after it has been published yet (checked on the retrieval day), so '
                    'this version is checked only against the words of the law.'), '']
        if law.get('reading_rule'):
            lines += ['Not applied to the text: ' + law['reading_rule'], '']
        if law['number'] == '1186':
            lines += ['Normaweb\'s copy of this law has lost the closing quote after "le asignen las leyes." and moved '
                      'it to the next article\'s heading; the Gaceta (N° 10, 2024-01-19, p. 1276) prints the quote '
                      'there, so the quoted text ends at that line.', '']
        lines += ['Kind: amendment', 'Replayed: yes']
    elif law['kind'] == 'consolidation':
        a, b = files_of(prev), files_of(v)
        wd = [f for f in files if words(a.get(f, '')) != words(b.get(f, ''))]
        lines = [f'Constitución: texto consolidado del Digesto ({law_name(law)})', '', title + '.', '',
                 f'The official consolidated text of the Constitution, published with this law in La Gaceta N° '
                 f'{law["gazette"][0]} of {law["gazette"][1]} (Digesto Jurídico Nicaragüense; approved '
                 f'{law["approved"]}). It replaces the replayed text. The law gives the Digesto texts legal force, so '
                 f'every difference between the replay and this text is credited to it: {len(files)} files differ, '
                 f'{len(wd)} of them in their letters or digits (the rest in punctuation, quotation marks or '
                 'paragraph breaks only). These are the Digesto\'s own corrections and typography, not a reform: '
                 'compare with --word-diff.', '', 'Kind: consolidation', f'Words-changed: {len(wd)} files']
    else:  # reform with a whole official text
        lines = [f'Constitución: reforma parcial y texto íntegro ({law_name(law)})', '', title + '.', '',
                 'The law reforms most of the Constitution and orders a Texto Íntegro with the reforms incorporated and '
                 '"la respectiva renumeración de Títulos, Capítulos y Artículos"; both are printed in the same '
                 f'Gaceta (N° {law["gazette"][0]}, {law["gazette"][1]}). This version is that official Texto Íntegro, '
                 f'credited to the law: {len(prev["articles"])} articles become {len(v["articles"])}, so from this '
                 'commit on a file name holds the article of that number in the renumbered text; compare texts, not '
                 'paths, across it.', '', 'Kind: reform', 'Renumbered: yes']
    basis = V.SECOND_READING_BASIS if law.get('second_reading') else law['basis']
    lines += [f'Enacted: {law["approved"]}', f'Published: La Gaceta N° {law["gazette"][0]}, {law["gazette"][1]}',
              f'In-force: {law["in_force"]}', f'In-force-basis: {basis}']
    lines += [f'Affecting: {FOLDER}/{f}' for f in files]
    lines += [f'Source: {src}']
    if gaz:
        lines += [f'Gazette: {gaz}']
    return '\n'.join(lines) + '\n'


# ---- git ---------------------------------------------------------------------------------------------------------------
def git(repo, *args, inp: bytes | None = None) -> str:
    r = subprocess.run(['git', '-c', 'core.autocrlf=false', '-c', 'core.safecrlf=false', *args], cwd=repo, input=inp,
                       capture_output=True)
    if r.returncode:
        raise SystemExit(f'git {" ".join(args)}: {r.stderr.decode("utf-8", "replace")}')
    return r.stdout.decode('utf-8')


def rmtree(p):
    def fix(func, path, exc):
        os.chmod(path, stat.S_IWRITE)
        func(path)
    shutil.rmtree(p, onexc=fix)


def prepare(repo: Path):
    """Refuse a non-empty target that is not an earlier build of this repo or the placeholder clone. Keep origin."""
    origin = ''
    if repo.exists() and any(repo.iterdir()):
        if not (repo / '.git').exists():
            raise SystemExit(f'{repo} is not empty and not a git repository')
        log = subprocess.run(['git', 'log', '--all', '--format=%ce|%s', '-500'], cwd=repo, capture_output=True,
                             text=True, encoding='utf-8').stdout.splitlines()
        ours = all(l.split('|')[0] in (COMMITTER[1], 'world-law@lexifina.com') for l in log if l)
        if not ours:
            raise SystemExit(f'{repo} holds commits that are not from this builder; refusing to overwrite')
        origin = subprocess.run(['git', 'remote', 'get-url', 'origin'], cwd=repo, capture_output=True,
                                text=True).stdout.strip()
        for p in repo.iterdir():
            rmtree(p) if p.is_dir() else p.unlink()
    repo.mkdir(parents=True, exist_ok=True)
    git(repo, 'init', '-q', '-b', 'main')
    if origin:
        git(repo, 'remote', 'add', 'origin', origin)


class Writer:
    """One `git fast-import` stream. Each commit replaces the whole tree (deleteall + every file)."""

    def __init__(self, repo: Path):
        self.p = subprocess.Popen(['git', 'fast-import', '--quiet', '--done'], cwd=repo, stdin=subprocess.PIPE)
        self.mark = 0

    def w(self, b: bytes):
        self.p.stdin.write(b)

    def data(self, b: bytes):
        self.w(b'data %d\n' % len(b) + b + b'\n')

    def commit(self, name, email, when, cname, cemail, cwhen, msg: str, files: dict, ref='refs/heads/main'):
        self.mark += 1
        self.w(f'commit {ref}\nmark :{self.mark}\n'.encode())
        self.w(f'author {name} <{email}> {when}\n'.encode('utf-8'))
        self.w(f'committer {cname} <{cemail}> {cwhen}\n'.encode('utf-8'))
        self.data(msg.encode('utf-8'))
        if self.mark > 1:
            self.w(f'from :{self.mark - 1}\n'.encode())
        self.w(b'deleteall\n')
        for path in sorted(files):
            self.w(f'M 100644 inline {path}\n'.encode('utf-8'))
            self.data(files[path])
        self.w(b'\n')
        return self.mark

    def tag(self, name, mark):
        self.w(f'reset refs/tags/{name}\nfrom :{mark}\n\n'.encode('utf-8'))

    def finish(self):
        self.w(b'done\n')
        self.p.stdin.close()
        if self.p.wait():
            raise SystemExit('git fast-import failed')


def tree_bytes(v: dict) -> dict:
    return {f'{FOLDER}/{k}': t.encode('utf-8') for k, t in files_of(v).items()}


def build(repo: Path, today: str, offline: bool, wip: bool = False):
    S.OFFLINE = offline
    vs = V.build_versions()
    if any(l['in_force'] > today for l, _, _ in vs):
        raise SystemExit('a law takes effect after --today: a future branch is needed; not implemented')
    day = S.retrieved()
    if day > today:
        raise SystemExit(f'data retrieved {day} is after --today {today}')
    prepare(repo)
    wr = Writer(repo)
    prev = None
    sec = {}
    marks = []
    for law, v, changed in vs:
        n = sec.get(law['in_force'], 0)
        sec[law['in_force']] = n + 1
        when = stamp(law['in_force'], n)
        name, email = author(law)
        msg = message(law, v, prev, changed or [])
        m = wr.commit(name, email, when, COMMITTER[0], COMMITTER[1], when, msg, tree_bytes(v))
        marks.append(m)
        wr.tag(law['tag'] if 'tag' in law else f'ley/{law["number"]}', m)
        if law['kind'] != 'baseline' and 'tag' in law:
            wr.tag(f'ley/{law["number"]}', m)
        prev = v
    import reproduce
    docs = reproduce.docs(vs, day, today, HERE, wip)
    files = tree_bytes(prev)
    files.update({k: (t if isinstance(t, bytes) else t.encode('utf-8')) for k, t in docs.items()})
    when = stamp(day)
    msg = ('Documentation, tools and REPRODUCE.md\n\nNo law text changes: README, LICENSE, SOURCES.md, REPRODUCE.md, '
           'corpus.json, laws.csv and the tools.\n\nKind: documentation\nIn-force: ' + day + '\n')
    wr.commit(COMMITTER[0], COMMITTER[1], when, COMMITTER[0], COMMITTER[1], when, msg, files)
    wr.finish()
    git(repo, 'reset', '-q', '--hard', 'main')
    return git(repo, 'rev-parse', 'HEAD').strip(), vs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--repo', required=True)
    ap.add_argument('--today', required=True, help='the build day (YYYY-MM-DD); laws in force after it would go to '
                                                   'a future branch')
    ap.add_argument('--offline', action='store_true')
    ap.add_argument('--wip', action='store_true', help='README says "building" (for the wip branch only)')
    ap.add_argument('--verify-rebuild', action='store_true',
                    help='build again in a temporary folder from the cache and compare HEAD with --repo')
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding='utf-8')
    dt.date.fromisoformat(args.today)
    if args.verify_rebuild:
        want = git(Path(args.repo), 'rev-parse', 'HEAD').strip()
        with tempfile.TemporaryDirectory() as td:
            got, _ = build(Path(td) / 'r', args.today, True, args.wip)
        print('rebuild', got, 'repo', want, 'IDENTICAL' if got == want else 'DIFFERENT')
        raise SystemExit(0 if got == want else 1)
    head, vs = build(Path(args.repo), args.today, args.offline, args.wip)
    for law, v, _ in vs:
        print(law['key'], law['in_force'], len(v['articles']), 'articles')
    print('main', head)


if __name__ == '__main__':
    main()
