"""Writes the repository's documentation and tools: README.md, LICENSE, SOURCES.md, REPRODUCE.md, corpus.json, laws.csv,
.gitattributes and tools/. Called by build.py; deterministic (no clock, no network). verification.json (written by
check_repo.py and test_repo.py with --record) is read when it exists, so a rebuild carries the results of the checks."""
import hashlib
import json
import subprocess
from pathlib import Path

TOOLS = ('build.py', 'source.py', 'parse.py', 'versions.py', 'reproduce.py', 'check_repo.py', 'test_repo.py',
         'in_force_on.py')


def blob(p: Path) -> str:
    return subprocess.run(['git', 'hash-object', str(p)], capture_output=True, text=True).stdout.strip()


def docs(vs, day: str, today: str, here: Path, wip: bool = False) -> dict:
    import build as B
    import parse as P
    import source as S
    ver = {}
    vp = here / 'verification.json'
    if vp.exists():
        ver = json.loads(vp.read_text(encoding='utf-8'))
    laws = [l for l, _, _ in vs]
    first, last = laws[0]['in_force'], laws[-1]['in_force']
    out = {}
    corpus = {
        'corpus': 'ni/national/acts',
        'name': 'Nicaraguan law: the Constitución Política (text of 2014 to today)',
        'label': 'Nicaragua',
        'language': 'es',
        'acts': ['Constitución Política de la República de Nicaragua'],
        'history_from': first,
        'record_to': last,
        'checked_on': day,
        'record_note': (f'From the official text with the reforms incorporated (in force {first}) to Ley N° 1271 '
                        f'(in force {last}). Normas Jurídicas de Nicaragua lists no later constitutional reform on '
                        f'{day}, the day the data was retrieved and checked.'),
        'history': 'in-force',
        'in_force_trailer': 'In-force',
        'baseline_trailer': 'Consolidated',
        'has_future_branch': False,
        'built': day,
        'dates': {'commit': 'in-force', 'other_trailers': ['Enacted', 'Published', 'In-force-basis'],
                  'time': '12:00 America/Managua (UTC-6; summer time UTC-5 only in 2005 and 2006)'},
        'scope': {
            'trailer': 'Applies',
            'when_absent': 'this corpus records no scope notes (no commit carries Applies:); the absence is not a '
                           'statement that the change reaches every case',
            'default_reach': {
                'rule': 'the law has no retroactive effect, except in criminal matters when it favours the accused',
                'meaning': 'a change applies from its in-force day; a criminal provision that favours the accused also '
                           'reaches earlier acts',
                'authority': 'Constitución Política (texto de 2014), art. 38: "La ley no tiene efecto retroactivo, '
                             'excepto en materia penal cuando favorezca al reo."; texto íntegro de 2025, art. 27, '
                             'numeral 14)',
                'decided_here': False}},
        'replayed': ('partial: the 2014, 2022, 2024 and 2025 versions are whole official texts; the versions of the '
                     'reform laws between them are replayed from the words each law quotes, and the next official '
                     'text checks them (the 2026 reforms have no official text after them yet)'),
        'verification': ('every replayed article equals the next official consolidation word for word; the '
                         'consolidations differ from the replay only in the Digesto\'s own corrections and typography, '
                         'credited to the Digesto law in a labelled commit'),
        'tool': 'tools/in_force_on.py',
        'citation': {'file': '(constitucion)/articulo-0*([0-9]+)(-[a-z]+)?\\.md',
                     'cites': '([Aa]rt[ií]culo|[Aa]rto\\.|[Aa]rt\\.) ?{n}([^0-9]|$)'},
    }
    out['corpus.json'] = json.dumps(corpus, indent=2, ensure_ascii=False) + '\n'

    rows = ['tag,author,kind,approved,gazette,in_force,articles_after,normaweb_document,in_force_basis']
    for law, v, _ in vs:
        name, _ = B.author(law)
        tag = law.get('tag', f'ley/{law.get("number", "")}')
        basis = (__import__('versions').SECOND_READING_BASIS if law.get('second_reading') else law['basis'])
        rows.append(','.join('"' + str(x).replace('"', '""') + '"' for x in [
            tag, name, law['kind'], law['approved'], f'La Gaceta N° {law["gazette"][0]}, {law["gazette"][1]}',
            law['in_force'], len(v['articles']), law['unid'], basis]))
    out['laws.csv'] = '\n'.join(rows) + '\n'

    out['LICENSE'] = (
        'Source of the legal texts: Normas Jurídicas de Nicaragua, the legislation database of the Asamblea Nacional\n'
        'de la República de Nicaragua: http://legislacion.asamblea.gob.ni/Normaweb.nsf/\n\n'
        'Copyright: the texts are laws of Nicaragua. Ley N° 312, Ley de Derecho de Autor y Derechos Conexos (1999),\n'
        'art. 16: "No son objeto de protección las leyes, las disposiciones gubernativas, proyectos de ley, actas,\n'
        'acuerdos, deliberaciones y dictámenes de los órganos y organismos públicos y traducciones oficiales de los\n'
        'textos anteriores."\n\n'
        f'Terms of use: the database publishes none (checked {day}); legislacion.asamblea.gob.ni and www.asamblea.gob.ni\n'
        'have no robots.txt (HTTP 404). Only La Gaceta, Diario Oficial is authoritative. The versions between the\n'
        'official texts are derived (replayed) from the reform laws by the method in REPRODUCE.md; the Asamblea did\n'
        'not publish them as whole texts.\n\n'
        'Attribution for the legal texts: "Textos: Normas Jurídicas de Nicaragua, Asamblea Nacional,\n'
        'http://legislacion.asamblea.gob.ni/".\n\n'
        'The history (commits and commit messages), the tables and the tools are dedicated to the public domain under\n'
        'CC0 1.0 Universal: https://creativecommons.org/publicdomain/zero/1.0/legalcode\n')

    srcs = '\n'.join(f'| `{l.get("tag", "ley/" + l.get("number", ""))}` | {B.law_title(l) if l["kind"] != "baseline" else l["title"]} | '
                     f'[Normaweb]({S.norm_url(l["unid"])}) | [Gaceta N° {l["gazette"][0]}, {l["gazette"][1]}]'
                     f'({S.gazette_link(S.norm(l["unid"]))}) |' for l in laws)
    out['SOURCES.md'] = f'''# Sources

All texts come from **Normas Jurídicas de Nicaragua** (http://legislacion.asamblea.gob.ni/Normaweb.nsf/), the
legislation database of the Asamblea Nacional (División de Información Legislativa). Each document links to the scanned
issue of **La Gaceta, Diario Oficial** that published it, which is the authoritative text.

| Tag | Text | Database | Gazette |
| --- | --- | --- | --- |
{srcs}

Official whole texts used: 2014 (Texto con Reformas Incorporadas), 2022 and 2024 (Textos Consolidados of the Digesto
Jurídico Nicaragüense de la Materia Constitucional, Leyes N° 1091 and 1196), 2025 (Texto Íntegro, Ley N° 1234).
Not used: the "Texto Íntegro Preliminar" of 25 November 2024 (Gaceta 218), which is the certification of the first
reading of Ley N° 1234 and was never in force; the 1987 original and the 2010 text, which come before this record.

## Legal basis

- Copyright: Ley N° 312, Ley de Derecho de Autor y Derechos Conexos, art. 16 (laws are not protected).
- robots.txt: none on legislacion.asamblea.gob.ni or www.asamblea.gob.ni (HTTP 404, checked {day}).
- Terms of use: none published by the database or the Asamblea's site (checked {day}).
- No bot challenge: plain HTTP pages and Domino `ReadViewEntries` JSON.

## Other sources looked at

- digesto.asamblea.gob.ni (Digesto Jurídico Nicaragüense) is behind Cloudflare; not used.
- The other Central American countries (checked the same day) failed the gates: Guatemala (Incapsula bot challenge),
  Honduras and Panama (no official consolidated text online).
'''

    ok = ''
    if ver:
        c, s = ver.get('check', {}), ver.get('smoke', {})
        ok = (f'- check_repo.py: {c.get("summary", "not recorded")}\n'
              f'- test_repo.py: {s.get("passed", "?")}/{s.get("total", "?")} passed\n')
    table = '\n'.join(f'| `{l.get("tag", "ley/" + l.get("number", ""))}` | {B.author(l)[0]} | {l["kind"]} | '
                      f'{l["approved"]} | Gaceta N° {l["gazette"][0]}, {l["gazette"][1]} | {l["in_force"]} | '
                      f'{len(v["articles"])} |' for l, v, _ in vs)
    status = ('**Status: building. Work in progress on the `wip` branch; not final.**\n\n') if wip else ''
    out['README.md'] = f'''# The Constitution of Nicaragua, change by change

{status}The Constitución Política de la República de Nicaragua as a git repository, in Spanish, from the official text
with the reforms incorporated of 2014 to the reforms of January 2026. Each reform law is one commit, credited to that
law and dated the day it took effect, at noon in Managua. Source: Normas Jurídicas de Nicaragua, the legislation
database of the Asamblea Nacional (legislacion.asamblea.gob.ni).

## The questions, as git commands

| Question | Command |
| --- | --- |
| What did article 37 say on 1 June 2020? | `python tools/in_force_on.py 2020-06-01 constitucion 37` |
| ... and on 1 June 2021, after Ley N° 1057? | `python tools/in_force_on.py 2021-06-01 constitucion 37` |
| The whole Constitution as it stood on 1 March 2024 | `python tools/in_force_on.py 2024-03-01 constitucion` |
| Which law wrote each line of article 21 in 2024? | `git blame ley/1190 -- constitucion/articulo-021.md` |
| Every change to articulo-037.md, with its law and day | `git log --format="%an %(trailers:key=In-force,valueonly,separator=)" main -- constitucion/articulo-037.md` |
| Exactly what Ley N° 1057 changed, word by word | `git show --word-diff ley/1057 -- constitucion/articulo-037.md` |
| Everything one law changed | `git show --stat ley/1269` |
| The laws, with their in-force days | `git log --format="%an, in force %(trailers:key=In-force,valueonly,separator=)" main` |
| One tag per law and per official text | `git tag --list` |
| How the in-force day of each law was read | `git log --format="%an: %(trailers:key=In-force-basis,valueonly,separator=)" main` |

PowerShell splits `git show $(...):path`; use `$r = git rev-list -1 main; git show "$($r):constitucion/articulo-037.md"`.
For a date, prefer `tools/in_force_on.py`, which reads the `In-force:` trailer: `git rev-list --before=DATE` compares
commit times in your own time zone and flips at noon on the day itself. After a rebuild, `git fetch --force --tags`.

## The laws

| Tag | Author | Kind | Approved | Published | In force | Articles |
| --- | --- | --- | --- | --- | --- | --- |
{table}

See [`laws.csv`](laws.csv) and [`SOURCES.md`](SOURCES.md). Normas Jurídicas de Nicaragua lists no constitutional reform
after Ley N° 1271 (checked {day}).

## The dates, and which one we use

Each law has the day the Asamblea approved it (`Enacted:`), the issue of La Gaceta, Diario Oficial that printed it
(`Published:`), and the day it took effect (`In-force:`). **Commits are dated the day the text took effect**, at noon in
Managua (UTC-6). Every law here takes effect on its publication in La Gaceta, as its last article says; each commit's
`In-force-basis:` trailer quotes it. Two laws taking effect on one day are two commits, a second apart, in the order of
their numbers.

- The reforms of January 2024 (Leyes N° 1186, 1187, 1188 and 1190) still carry the clause of their first-reading bill
  ("Una vez sea aprobada en segunda legislatura, ... entrará en vigencia a partir de la fecha de su publicación"). The
  publications used here are the promulgated laws ("Téngase como Ley de la República"), and the official consolidation
  of 2024 incorporates them as published on these days, so they are dated by these publications.

## What "author" means

The author of a commit is the law that made the text (`Ley N° 1057`, address `ley-1057@asamblea-ni.invalid`), so `git
blame` names the law. The first commit is the official 2014 text, authored by its publisher. The committer is always
`Lexifina`.

## Read this before comparing versions

- **The first version is a baseline.** The 2014 text holds the 1987 Constitution with every reform up to Ley N° 854
  (2014) incorporated; all its lines are credited to that text (`Kind: baseline`). Read them as "in force on 10
  February 2014 at the latest".
- **Replayed versions.** Between the official texts, each reform law's version is the previous text with the words the
  law quotes put in place (`Replayed: yes`). The next official text checks them: every article a law replaced is word
  for word the same in the Digesto consolidations of 2022 and 2024. The 2026 reforms have no official text after them
  yet, so they are checked only against the words of the laws.
- **Digesto consolidations** (`Kind: consolidation`, Leyes N° 1091 and 1196) replace the replayed text with the official
  consolidated text. They change no rule, but the Digesto corrected typing errors ("fuera atractivo" -> "fuero
  atractivo"), and changed punctuation, quotation marks and paragraph breaks; those differences are in these commits,
  credited to the Digesto law that gave the text legal force. `Words-changed:` counts the files whose letters or digits
  differ.
- **2025 renumbered the articles.** Ley N° 1234 reformed most of the Constitution and ordered a Texto Íntegro with new
  numbers (202 articles became 184). From that commit on, a file name holds the article of that number in the new text.
  Compare texts, not paths, across it.
- **Ley N° 1269 art. 3** says that wherever the legal order reads "Procuraduría General de la República" it is to be
  read "Procuraduría General de Justicia". That is a rule of reading, not a textual amendment, so the other articles keep
  their printed words.
- **Blame credits whole lines**: one line is one paragraph. Use `--word-diff` for the words.

## How it is checked

`tools/check_repo.py` reads every version back from git and compares it with what the source says, byte for byte, file
by file: the official texts against their own pages, and each replayed version against the previous version plus the
words its law quotes. It then compares each official version again as a stream of letters and digits taken straight from
the page, without the line or article parser, and checks every replayed article against the next official text.
`tools/test_repo.py` checks that the commands above work. See [`REPRODUCE.md`](REPRODUCE.md).
{ok}
## Files

`constitucion/articulo-NNN.md` is one article (`articulo-046-ter.md` an article with a suffix): the `#` line is its
number, then one line per paragraph, exactly as the database prints it (its typography and typing errors are kept).
`preambulo.md` is the promulgation formula and the preamble, `estructura.md` the titles and chapters, each with the
article it opens, and `cierre.md` the closing formula with the list of earlier reforms and the Digesto's notes.

## What it does not show

- The Constitution before 2014: the 1987 original and the reforms of 1990-2014 are in the database, but only as a whole
  2014 text here.
- Changes in how the Constitution works that leave its words alone, such as the reading rule of Ley N° 1269 art. 3,
  or rulings of the Corte Suprema de Justicia. Words unchanged does not mean law unchanged.
- The texts in the languages of the Caribbean Coast (the database holds a Mayangna text of 2012).

## Licence

Laws are not protected by copyright in Nicaragua (Ley N° 312 art. 16). The database publishes no terms of use. See
[`LICENSE`](LICENSE). Tools, history and tables: CC0.
'''

    log = []
    lp = here / 'cache' / 'requests.jsonl'
    if lp.exists():
        log = [json.loads(l) for l in lp.read_text(encoding='utf-8').splitlines() if l]
    used = []
    for l in laws:
        u = S.norm_url(l['unid'])
        r = next((x for x in log if x['url'] == u), None)
        used.append(f'- {l.get("tag", "ley/" + l.get("number", ""))}: `{u}`'
                    + (f', sha256 `{r["sha256"]}`, retrieved {r["retrieved"]}' if r else ''))
    blobs = '\n'.join(f'- `{n}`: `{blob(here / n)}`' for n in TOOLS)
    n_req = len(log)
    out['REPRODUCE.md'] = f'''# Reproduce

Data retrieved {day}; built for {today}. The build is deterministic: the same data gives the same commit hashes.

## Sources and requests

Normas Jurídicas de Nicaragua (http://legislacion.asamblea.gob.ni/Normaweb.nsf/), an IBM Domino database of the Asamblea
Nacional. Two kinds of request, plain HTTP GET with a browser User-Agent and gzip, one at a time:
- the default view as JSON, `Normaweb.nsf/$defaultview?ReadViewEntries&...&outputformat=JSON` (every document's
  category, date, number, title and id: 27,028 documents), read once to find every reform of the Constitution;
- each text page, `Normaweb.nsf/xpNorma.xsp?documentId=<id>&action=openDocument`; the official text is the
  `view:_id1:computedField1` span.

Fetch rate: one request at a time, no parallel requests, each answer cached on disk with its sha256 (`tools/cache`,
git-ignored, negative answers included). {n_req} requests are logged in the cache, including the gate checks and two
Gaceta PDFs read to confirm a date and a paragraph. Before the cache existed, the triage made about 40 requests to the
same host (view pages, the probe of the constitution page, Ley N° 312). robots.txt: none (HTTP 404) on
legislacion.asamblea.gob.ni and www.asamblea.gob.ni. No terms of use are published.

The pages used, with the sha256 of each answer:
{chr(10).join(used)}

## Steps

1. `python -I -X utf8 tools/build.py --repo <dir> --today <YYYY-MM-DD>` (online once; `--offline` rebuilds from the
   cache). `--verify-rebuild` builds again in a temporary folder and compares HEAD.
2. `python -I -X utf8 tools/check_repo.py --repo <dir> --record`; `python -I -X utf8 tools/test_repo.py --repo <dir> --record`.
3. Build again (the documentation then carries the results of step 2), `--verify-rebuild`, and
   `python scripts/global-law/check_corpus.py <dir>` and `python scripts/test_corpus.py <dir> tools/in_force_on.py` from
   the lexifina repository.

Tool versions: Python 3.12 (standard library only; PyMuPDF only to read two Gaceta PDFs during the checks by hand), git,
curl (Windows). Builder blob hashes (`git hash-object`):
{blobs}

## Method

- `parse.lines`: the text span is split at every `<br>`, `<div>`, `<p>`, table row and list element; tags are dropped;
  entities decoded; runs of white space (including U+00A0 and zero-width characters) become one space; ends stripped;
  empty lines dropped. Nothing else is normalised.
- `parse.constitution`: from the line "El Presidente de la República" to the line "Dado en la Sala de Sesiones ... a los
  diez y nueve días ..." (the 1986 closing formula). A line "Artículo N" opens an article (the separator after the number
  is dropped); TÍTULO / CAPÍTULO / SECCIÓN lines and the upper-case lines after them are headings (`estructura.md`).
  Everything from the closing formula on is `cierre.md`, except a last "Observación:" line, which is a note of the
  database, not of the Gaceta. The lines before the promulgation formula (the database's title and publication lines,
  and the Digesto's header) are left out and quoted in the commit message instead.
- Replay (`versions.py`): each reform law's quoted text, from the line opening with a quotation mark and the article
  heading to the line closing the quotation, replaces the whole article; a repealed literal becomes "<letter>) Derogado."
  as the Digesto prints repealed literals; Ley N° 1270 replaces one numeral and Ley N° 1271 one paragraph, as they say.
  The build stops if the words a step needs are not there.
- Commit dates: noon in Managua, UTC-6 (summer time UTC-5 only in 2005 and 2006, before this record).

## Decisions by hand, and AI

No model wrote legal text or ran at build time. The code was written by Claude Code with Claude Opus 5.5
(`claude-opus-5-5`), which also chose the scope and read the in-force clauses. Decisions by hand:
- the 2014 text as a labelled baseline (the reforms of 1990-2014 are not replayed);
- the Constitution only: it is the one act with several official whole texts to check a replay against;
- the January 2024 reforms dated by their promulgated publication, despite the leftover first-reading clause (see README);
- the Digesto consolidations credited to the Digesto laws that gave them legal force;
- Ley N° 1269 art. 3 (a reading rule) not applied to the words;
- the end of Ley N° 1186's quotation, which the database's copy lost (the Gaceta prints it; see that commit).

## Verification record

{ok or '(not yet recorded)'}'''
    out['.gitattributes'] = '* text eol=lf\n'
    for n in TOOLS:
        out[f'tools/{n}'] = (here / n).read_bytes()
    return out
