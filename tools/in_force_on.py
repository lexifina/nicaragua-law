"""Prints the Constitution of Nicaragua, or one article of it, as it stood on a given day, from this repository.

    python tools/in_force_on.py 2021-06-01 constitucion 37     # article 37 on 1 June 2021
    python tools/in_force_on.py 2021-06-01 constitucion        # the whole text on 1 June 2021, in reading order

Each commit carries the day its text took effect in an `In-force:` trailer. The text in force on a day is the last commit
on or before it, read by that trailer (not by commit time, so the reader's time zone does not matter). Article numbers
are those of the text in force that day: Ley N° 1234 renumbered the articles on 18 February 2025. All files are read
through one `git cat-file --batch`. Standard library only.
"""
import datetime as dt
import re
import subprocess
import sys


def git(*args: str) -> str:
    return subprocess.run(['git', *args], capture_output=True, text=True, encoding='utf-8', check=True).stdout


def commit_on(day: str, folder: str) -> str:
    out = git('log', '--no-merges', '--format=%H%x09%(trailers:key=In-force,valueonly,separator=)', 'main', '--', folder)
    for line in out.splitlines():
        h, _, d = line.partition('\t')
        if d.strip() and d.strip() <= day:
            return h
    return ''


def fname(key: str) -> str:
    m = re.fullmatch(r'(\d+)(?:[- ]?(bis|ter|quater))?', key)
    if not m:
        return key if key.endswith('.md') else key + '.md'
    return f'articulo-{int(m.group(1)):03d}' + (f'-{m.group(2)}' if m.group(2) else '') + '.md'


def akey(name: str) -> tuple:
    m = re.fullmatch(r'articulo-(\d+)(?:-(bis|ter|quater))?\.md', name)
    order = {None: 0, 'bis': 1, 'ter': 2, 'quater': 3}
    return (int(m.group(1)), order[m.group(2)]) if m else (10 ** 6, 0)


def read_many(commit: str, paths: list) -> dict:
    p = subprocess.Popen(['git', 'cat-file', '--batch'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    out = {}
    for path in paths:
        p.stdin.write(f'{commit}:{path}\n'.encode('utf-8'))
        p.stdin.flush()
        head = p.stdout.readline().decode()
        if head.endswith('missing\n'):
            out[path] = None
            continue
        size = int(head.split()[2])
        out[path] = p.stdout.read(size).decode('utf-8')
        p.stdout.read(1)
    p.stdin.close()
    p.wait()
    return out


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    day, folder = sys.argv[1], sys.argv[2].rstrip('/')
    dt.date.fromisoformat(day)
    c = commit_on(day, folder)
    if not c:
        first = git('log', '--reverse', '--format=%(trailers:key=In-force,valueonly,separator=)', 'main', '--',
                    folder).split()
        sys.exit(f'{folder} is not in the record on {day} (the record starts on {first[0] if first else "?"}).')
    if len(sys.argv) > 3:
        name = fname(sys.argv[3])
        got = read_many(c, [f'{folder}/{name}'])[f'{folder}/{name}']
        if got is None:
            sys.exit(f'{folder}/{name} was not in the text on {day}.')
        sys.stdout.write(got)
        return
    names = [n.split('/', 1)[1] for n in git('ls-tree', '-r', '--name-only', c, folder + '/').split('\n') if n]
    arts = sorted((n for n in names if n.startswith('articulo-')), key=akey)
    texts = read_many(c, [f'{folder}/{n}' for n in ['preambulo.md', 'estructura.md', 'cierre.md'] + arts])
    heads = {}
    for line in (texts[f'{folder}/estructura.md'] or '').splitlines():
        m = re.fullmatch(r'(.*) \[artículo ([0-9]+(?:-[a-z]+)?)\]', line)
        if m:
            heads.setdefault(fname(m.group(2)), []).append(m.group(1))
    sys.stdout.write(texts[f'{folder}/preambulo.md'] + '\n')
    for n in arts:
        for h in heads.get(n, []):
            sys.stdout.write(h + '\n')
        if n in heads:
            sys.stdout.write('\n')
        sys.stdout.write(texts[f'{folder}/{n}'] + '\n')
    sys.stdout.write(texts[f'{folder}/cierre.md'])


if __name__ == '__main__':
    main()
