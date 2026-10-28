"""Checks the built Nicaragua repository against its sources. Standard library only.

    python -I -X utf8 check_repo.py --repo DIR [--record]

1. Byte check: every law commit's tree equals, file by file, the version versions.py makes from the cached source.
2. Independent word check (official versions): the letters and digits of the repository text, read in reading order,
   equal a contiguous run of the letters and digits of the raw page's text span (every text node, tags removed, no line
   or article logic); what is left before it is the database's title lines and what is left after it is only the
   database's "Observación" note.
3. Replay checks: each replayed file's letters and digits are a contiguous run of the reform law's raw page; every file
   a replay did not touch is byte-identical to the version before; every article a replay wrote is, word for word, the
   same article in the next official text (unless a later law in between rewrote it).
4. History: no merges, in-force dates never go backwards and are never after the build day, no CRs in messages, every
   commit has In-force and its trailers parse with `git interpret-trailers --parse`.
With --record the summary is written to verification.json (read by reproduce.py).
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build as B  # noqa: E402
import parse as P  # noqa: E402
import source as S  # noqa: E402
import versions as V  # noqa: E402

W = re.compile(r'[^\W_]+')


def words(s: str) -> list:
    return W.findall(s.casefold())


def git(repo, *a) -> str:
    return subprocess.run(['git', *a], cwd=repo, capture_output=True, text=True, encoding='utf-8', check=True).stdout


def read_tree(repo, commit) -> dict:
    names = [n for n in git(repo, 'ls-tree', '-r', '--name-only', commit, B.FOLDER + '/').split('\n') if n]
    p = subprocess.Popen(['git', 'cat-file', '--batch'], cwd=repo, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    out = {}
    for n in names:
        p.stdin.write(f'{commit}:{n}\n'.encode())
        p.stdin.flush()
        size = int(p.stdout.readline().split()[2])
        out[n] = p.stdout.read(size)
        p.stdout.read(1)
    p.stdin.close()
    p.wait()
    return out


def reading_order(files: dict) -> list:
    """Words of a version in reading order: preamble, (headings, article) ..., closing."""
    f = {k.split('/', 1)[1]: v.decode('utf-8') for k, v in files.items()}
    heads = {}
    for line in f.get('estructura.md', '').splitlines():
        m = re.fullmatch(r'(.*) \[artículo ([0-9]+(?:-[a-z]+)?)\]', line)
        heads.setdefault(B.fname(m.group(2)), []).append(m.group(1))
    order = {None: 0, 'bis': 1, 'ter': 2, 'quater': 3}

    def akey(n):
        m = re.fullmatch(r'articulo-(\d+)(?:-([a-z]+))?\.md', n)
        return int(m.group(1)), order[m.group(2)]
    out = words(f['preambulo.md'])
    for n in sorted((n for n in f if n.startswith('articulo-')), key=akey):
        for h in heads.get(n, []):
            out += words(h)
        out += words(f[n])
    return out + words(f['cierre.md'])


# Differences between a replayed article and the next Digesto text that are the Digesto's own wording, checked by eye
# against the law's Gaceta text; any other difference fails.
DIGESTO_EDITS = {
    # Ley 1186 (Gaceta 10, 2024-01-19, p. 1276) prints "Médicos Forenses y Secretarios de Actuaciones" in numerals 5)
    # and 6); the Digesto text of 2024 prints "Médicos Forenses, Secretarios de Actuaciones" in both.
    ('ley-1186', '165'): [('delete', 'y', ''), ('delete', 'y', '')],
}


def find_run(hay: list, needle: list) -> int:
    n = len(needle)
    first = needle[:12]
    m = len(first)
    for i in range(len(hay) - n + 1):
        if hay[i:i + m] == first and hay[i:i + n] == needle:
            return i
    return -1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--repo', required=True)
    ap.add_argument('--record', action='store_true')
    ap.add_argument('--today', default=None)
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding='utf-8')
    repo = Path(args.repo)
    S.OFFLINE = True
    vs = V.build_versions()
    log = git(repo, 'log', '--reverse', '--format=%H%x1f%an%x1f%(trailers:key=In-force,valueonly,separator=)',
              'main').strip().split('\n')
    commits = [l.split('\x1f') for l in log]
    law_commits = commits[:len(vs)]
    fails = []
    n_files = 0
    expected_trees = []
    # 1. byte check
    for (law, v, _), (h, an, inf) in zip(vs, law_commits):
        want = B.tree_bytes(v)
        got = read_tree(repo, h)
        expected_trees.append(want)
        n_files += len(want)
        if an != B.author(law)[0] or inf.strip() != law['in_force']:
            fails.append(f'{law["key"]}: author/in-force {an}/{inf} not as built')
        if got != want:
            bad = sorted(k for k in set(got) | set(want) if got.get(k) != want.get(k))
            fails.append(f'{law["key"]}: {len(bad)} files differ, e.g. {bad[:3]}')
    print(f'byte check: {len(vs)} versions, {n_files} files, {len(fails)} failures')
    # 2. independent word check of the official versions
    n_official = 0
    for (law, v, _), tree in zip(vs, expected_trees):
        if law['kind'] not in ('baseline', 'consolidation', 'reform'):
            continue
        n_official += 1
        unid = V.OFFICIAL[law['official']]
        raw = P.raw_words(S.norm(unid))
        mine = reading_order(tree)
        pos = find_run(raw, mine)
        if pos < 0:
            k = next((i for i in range(min(len(raw), len(mine))) if raw[i] != mine[i]), None)
            fails.append(f'{law["key"]}: official words not found as one run in the page')
            continue
        head = raw[:pos]
        tail = raw[pos + len(mine):]
        header = [w for l in v['header'] for w in words(l)]
        if head != header:
            fails.append(f'{law["key"]}: words before the text are not only the header: {head[:20]}')
        if tail and tail[0] != 'observación':
            fails.append(f'{law["key"]}: words after the text: {tail[:20]}')
        print(f'word check {law["key"]}: {len(mine)} words = page run at {pos}; left out {len(head)} header words, '
              f'{len(tail)} note words')
    # 3. replay checks
    n_replay = 0
    for i, (law, v, changed) in enumerate(vs):
        if law['kind'] != 'amendment':
            continue
        prev = expected_trees[i - 1]
        cur = expected_trees[i]
        raw = P.raw_words(S.norm(law['unid']))
        diff = sorted(k for k in set(prev) | set(cur) if prev.get(k) != cur.get(k))
        for k in diff:
            n_replay += 1
            body = cur[k].decode('utf-8')
            if k.endswith('preambulo.md'):
                ws = words('\n'.join(l for l in body.splitlines()[body.splitlines().index('Preámbulo'):]
                                     if not l.startswith(('Promulgamos', 'CONSTITUCIÓN POLÍTICA DE LA REP'))))
            else:
                # the new lines only (the heading and unchanged lines come from the previous version)
                old = set(prev[k].decode('utf-8').splitlines())
                new = [l for l in body.splitlines()[2:] if l not in old]
                rep = [l for l in new if re.fullmatch(r'[a-z]\) Derogado\.', l)]
                for l in rep:
                    if find_run(raw, ['se', 'deroga', 'el', 'literal', l[0]]) < 0:
                        fails.append(f'{law["key"]}: {k}: "{l}" but the law does not repeal literal {l[0]})')
                for l in new:
                    if l not in rep and find_run(raw, words(l)) < 0:
                        fails.append(f'{law["key"]}: {k}: new line not a run of the law\'s page: {l[:60]}')
                continue
            if ws and find_run(raw, ws) < 0:
                fails.append(f'{law["key"]}: {k}: new words not a run of the law\'s page')
        # the next official text
        nxt = next((j for j in range(i + 1, len(vs)) if vs[j][0]['kind'] in ('consolidation', 'reform')), None)
        if nxt is not None and vs[nxt][0]['kind'] == 'consolidation':
            later = [vs[j][2] or [] for j in range(i + 1, nxt)]
            for k in changed:
                if k == 'preambulo' or any(k in c for c in later):
                    continue
                a = [x for x in v['articles'] if x[0] == k][0][2]
                b = [x for x in vs[nxt][1]['articles'] if x[0] == k][0][2]
                wa, wb = words('\n'.join(a)), words('\n'.join(b))
                if wa != wb:
                    import difflib
                    ops = [(t, ' '.join(wa[i1:i2]), ' '.join(wb[j1:j2])) for t, i1, i2, j1, j2 in
                           difflib.SequenceMatcher(None, wa, wb, autojunk=False).get_opcodes() if t != 'equal']
                    if (law['key'], k) in DIGESTO_EDITS and ops == DIGESTO_EDITS[(law['key'], k)]:
                        print(f'replay {law["key"]} article {k} = {vs[nxt][0]["key"]} except the Digesto\'s known '
                              f'edit {ops}')
                    else:
                        fails.append(f'{law["key"]}: article {k} differs in words from {vs[nxt][0]["key"]}: {ops}')
                else:
                    print(f'replay {law["key"]} article {k} = {vs[nxt][0]["key"]} word for word')
            if 'preambulo' in changed:
                import difflib
                a = words('\n'.join(v['preamble']))
                b = words('\n'.join(vs[nxt][1]['preamble']))
                ops = [(t, ' '.join(a[i1:i2]), ' '.join(b[j1:j2])) for t, i1, i2, j1, j2 in
                       difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes() if t != 'equal']
                print(f'replay {law["key"]} preamble vs {vs[nxt][0]["key"]}: word differences {ops}')
                if len(ops) > 5:
                    fails.append(f'{law["key"]}: preamble differs from {vs[nxt][0]["key"]} in {len(ops)} places')
    # 4. history
    merges = git(repo, 'rev-list', '--merges', '--count', 'main').strip()
    days = [c[2].strip() for c in commits]
    back = [d for a, d in zip(days, days[1:]) if d < a]
    today = args.today or days[-1]
    future = [d for d in days if d > today]
    crs = git(repo, 'log', '--format=%B', 'main').count('\r')
    noinf = [c[0][:7] for c in commits if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', c[2].strip())]
    badtr = []
    for c in commits:
        msg = git(repo, 'log', '-1', '--format=%B', c[0])
        parsed = subprocess.run(['git', 'interpret-trailers', '--parse'], cwd=repo, input=msg, capture_output=True,
                                text=True, encoding='utf-8').stdout
        if not re.search(r'^In-force: ', parsed, re.M):
            badtr.append(c[0][:7])
    for name, bad in [('merges', merges != '0'), ('backwards dates', back), ('future dates', future), ('CRs', crs),
                      ('missing In-force', noinf), ('unparsed trailers', badtr)]:
        if bad:
            fails.append(f'history: {name}: {bad}')
    print(f'history: {len(commits)} commits, merges {merges}, backwards {len(back)}, future {len(future)}, CRs {crs}, '
          f'unparsed trailers {len(badtr)}')
    summary = (f'{len(vs)} versions, {n_files} files byte-equal; {n_official} official versions equal their pages as '
               f'letters and digits; {n_replay} replayed files are runs of their laws; '
               f'{len(fails)} failures')
    print('SUMMARY', summary)
    for f in fails:
        print('FAIL', f)
    if args.record:
        vp = HERE / 'verification.json'
        rec = json.loads(vp.read_text(encoding='utf-8')) if vp.exists() else {}
        rec['check'] = {'summary': summary, 'failures': fails}
        vp.write_text(json.dumps(rec, indent=2, ensure_ascii=False) + '\n', encoding='utf-8', newline='\n')
    sys.exit(1 if fails else 0)


if __name__ == '__main__':
    main()
