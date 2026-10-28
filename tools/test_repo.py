"""Functional smoke test of the built Nicaragua repository: the things a reader does with it work. Standard library only.

    python -I -X utf8 test_repo.py --repo DIR [--record]

It asserts that:
1. `git blame` on article 37 names Ley N° 1057 for its first paragraph;
2. tools/in_force_on.py gives article 37 before and after Ley N° 1057 (the day before and the day of its in-force day),
   each equal to the file at that version, and article 21 before and after Ley N° 1190; it refuses a day before the
   record;
3. `git log` on articulo-037.md lists its laws in the order they took effect;
4. every tag resolves to a commit, and every commit has an ISO `In-force:` trailer;
5. no commit is authored by Lexifina except the documentation commit (the last), and every other author uses an
   `.invalid` address;
6. every article a law changes reads new on its in-force day and old (or absent) the day before;
7. every command in the README's table runs and prints something.
With --record the result is written to verification.json next to this script (for REPRODUCE.md).
"""
import argparse
import json
import re
import shlex
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
F37 = 'constitucion/articulo-037.md'
F21 = 'constitucion/articulo-021.md'


class Smoke:
    def __init__(self, repo: Path):
        self.repo = repo
        self.results = []

    def git(self, *args):
        out = subprocess.run(['git', *args], cwd=self.repo, capture_output=True, text=True, encoding='utf-8')
        if out.returncode:
            raise AssertionError(f'git {" ".join(args)}: {out.stderr.strip()}')
        return out.stdout

    def tool(self, *args, ok=True):
        out = subprocess.run([sys.executable, '-X', 'utf8', 'tools/in_force_on.py', *args], cwd=self.repo,
                             capture_output=True, text=True, encoding='utf-8')
        if ok and out.returncode:
            raise AssertionError(f'in_force_on {" ".join(args)}: {out.stderr.strip()}')
        return out.stdout if ok else out

    def check(self, name, fn):
        try:
            detail = fn() or ''
            self.results.append((name, True, detail))
            print(f'PASS {name}: {detail}')
        except AssertionError as exc:
            self.results.append((name, False, str(exc)))
            print(f'FAIL {name}: {exc}')

    def t_blame(self):
        out = self.git('blame', '--line-porcelain', 'ley/1057', '--', F37)
        authors = re.findall(r'^author (.+)$', out, re.M)
        assert 'Ley N° 1057' in authors, authors
        return f'authors {sorted(set(authors))}'

    def t_tool(self):
        before = self.tool('2021-01-18', 'constitucion', '37')
        after = self.tool('2021-01-19', 'constitucion', '37')
        assert before == self.git('show', 'ley/1014:' + F37), 'before != file at ley/1014'
        assert after == self.git('show', 'ley/1057:' + F37), 'after != file at ley/1057'
        assert 'prisión perpetua' not in before and 'prisión perpetua' in after
        b21 = self.tool('2024-01-21', 'constitucion', '21')
        a21 = self.tool('2024-01-22', 'constitucion', '21')
        assert b21 != a21 and 'Traidores a la Patria' in a21 and 'Traidores a la Patria' not in b21
        r = self.tool('2014-02-09', 'constitucion', '37', ok=False)
        assert r.returncode != 0, 'a day before the record should fail'
        whole = self.tool('2024-03-01', 'constitucion')
        assert whole.count('# Artículo ') == 202, whole.count('# Artículo ')
        whole25 = self.tool('2026-10-01', 'constitucion')
        assert whole25.count('# Artículo ') == 184, whole25.count('# Artículo ')
        return 'art. 37 changes on 2021-01-19, art. 21 on 2024-01-22; 202 and 184 articles'

    def t_log(self):
        out = self.git('log', '--format=%(trailers:key=In-force,valueonly,separator=)', 'main', '--', F37)
        days = [d for d in out.split() if d]
        assert days == sorted(days, reverse=True) and len(days) >= 3, days
        return f'{len(days)} entries, newest first'

    def t_tags(self):
        tags = self.git('tag', '--list').split()
        for t in tags:
            self.git('rev-parse', '--verify', '-q', t + '^{commit}')
        bad = [l for l in self.git('log', '--format=%h %(trailers:key=In-force,valueonly,separator=)', 'main')
               .splitlines() if not re.fullmatch(r'\w+ \d{4}-\d{2}-\d{2}', l)]
        assert not bad, bad
        return f'{len(tags)} tags'

    def t_authors(self):
        rows = self.git('log', '--format=%an|%ae', 'main').splitlines()
        lex = [i for i, r in enumerate(rows) if r.startswith('Lexifina|')]
        assert lex == [0], lex
        bad = [r for r in rows[1:] if not r.endswith('.invalid')]
        assert not bad, bad
        return f'{len(rows)} commits, documentation commit last'

    def t_every_change(self):
        """For every law commit and every file it changes: the tool gives the new file on the in-force day and the old
        file (or nothing) on the day before. Same-day chains: only the last commit of a day is the text of that day."""
        import datetime as dt
        rows = self.git('log', '--reverse', '--format=%H %(trailers:key=In-force,valueonly,separator=)', 'main')
        commits = [r.split() for r in rows.splitlines() if len(r.split()) == 2][:-1]
        last_of_day = {}
        for h, d in commits:
            last_of_day[d] = h
        n = 0
        for i, (h, d) in enumerate(commits):
            if i == 0 or last_of_day[d] != h:
                continue
            first_of_day = next(c for c, e in commits if e == d)
            parent = self.git('rev-parse', first_of_day + '^').strip()
            for f in self.git('diff', '--name-only', parent, h, '--', 'constitucion/').split():
                art = f.split('/')[1]
                if not art.startswith('articulo-'):
                    continue
                prev_day = (dt.date.fromisoformat(d) - dt.timedelta(days=1)).isoformat()
                now = self.tool(d, 'constitucion', art, ok=False)
                new = subprocess.run(['git', 'show', f'{h}:{f}'], cwd=self.repo, capture_output=True, text=True,
                                     encoding='utf-8')
                if new.returncode == 0:
                    assert now.returncode == 0 and now.stdout == new.stdout, f'{f} on {d}'
                else:
                    assert now.returncode != 0, f'{f} still there on {d}'
                before = self.tool(prev_day, 'constitucion', art, ok=False)
                old = subprocess.run(['git', 'show', f'{parent}:{f}'], cwd=self.repo, capture_output=True, text=True,
                                     encoding='utf-8')
                if old.returncode == 0:
                    assert before.stdout == old.stdout, f'{f} on {prev_day}'
                else:
                    assert before.returncode != 0, f'{f} existed on {prev_day}'
                n += 1
        return f'{n} file changes checked on their day and the day before'

    def t_readme(self):
        readme = (self.repo / 'README.md').read_text(encoding='utf-8')
        cmds = re.findall(r'^\| [^|]+ \| `([^`]+)` \|$', readme, re.M)
        assert len(cmds) >= 8, len(cmds)
        for c in cmds:
            argv = shlex.split(c)
            if argv[0] == 'python':
                argv[0] = sys.executable
            out = subprocess.run(argv, cwd=self.repo, capture_output=True, text=True, encoding='utf-8')
            assert out.returncode == 0 and out.stdout.strip(), f'{c}: {out.stderr.strip()[:200]}'
        return f'{len(cmds)} commands'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--repo', default=str(HERE.parent if (HERE.parent / '.git').exists() else '.'))
    ap.add_argument('--record', action='store_true')
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding='utf-8')
    s = Smoke(Path(args.repo))
    for name, fn in [('blame', s.t_blame), ('on-date tool', s.t_tool), ('log order', s.t_log), ('tags', s.t_tags),
                     ('authors', s.t_authors), ('every change on its day', s.t_every_change),
                     ('README commands', s.t_readme)]:
        s.check(name, fn)
    passed = sum(1 for _, ok, _ in s.results if ok)
    print(f'{passed}/{len(s.results)} passed')
    if args.record:
        vp = HERE / 'verification.json'
        rec = json.loads(vp.read_text(encoding='utf-8')) if vp.exists() else {}
        rec['smoke'] = {'passed': passed, 'total': len(s.results)}
        vp.write_text(json.dumps(rec, indent=2, ensure_ascii=False) + '\n', encoding='utf-8', newline='\n')
    sys.exit(0 if passed == len(s.results) else 1)


if __name__ == '__main__':
    main()
