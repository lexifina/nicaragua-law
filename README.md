# The Constitution of Nicaragua, change by change

The Constitución Política de la República de Nicaragua as a git repository, in Spanish, from the official text
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
| `texto/2014` | Asamblea Nacional: texto con reformas incorporadas (2014) | baseline | 2014-02-10 | Gaceta N° 32, 2014-02-18 | 2014-02-10 | 202 |
| `ley/1014` | Ley N° 1014 | amendment | 2020-01-28 | Gaceta N° 22, 2020-02-04 | 2020-02-04 | 202 |
| `ley/1057` | Ley N° 1057 | amendment | 2021-01-18 | Gaceta N° 12, 2021-01-19 | 2021-01-19 | 202 |
| `digesto/2022` | Ley N° 1091 | consolidation | 2021-10-27 | Gaceta N° 181, 2022-09-28 | 2022-09-28 | 202 |
| `ley/1185` | Ley N° 1185 | amendment | 2024-01-16 | Gaceta N° 10, 2024-01-19 | 2024-01-19 | 202 |
| `ley/1186` | Ley N° 1186 | amendment | 2024-01-16 | Gaceta N° 10, 2024-01-19 | 2024-01-19 | 202 |
| `ley/1187` | Ley N° 1187 | amendment | 2024-01-17 | Gaceta N° 11, 2024-01-22 | 2024-01-22 | 202 |
| `ley/1188` | Ley N° 1188 | amendment | 2024-01-17 | Gaceta N° 11, 2024-01-22 | 2024-01-22 | 202 |
| `ley/1190` | Ley N° 1190 | amendment | 2024-01-18 | Gaceta N° 11, 2024-01-22 | 2024-01-22 | 202 |
| `digesto/2024` | Ley N° 1196 | consolidation | 2024-03-13 | Gaceta N° 161, 2024-08-30 | 2024-08-30 | 202 |
| `texto/2025` | Ley N° 1234 | reform | 2025-01-30 | Gaceta N° 32, 2025-02-18 | 2025-02-18 | 184 |
| `ley/1268` | Ley N° 1268 | amendment | 2026-01-14 | Gaceta N° 09, 2026-01-16 | 2026-01-16 | 184 |
| `ley/1269` | Ley N° 1269 | amendment | 2026-01-14 | Gaceta N° 09, 2026-01-16 | 2026-01-16 | 184 |
| `ley/1270` | Ley N° 1270 | amendment | 2026-01-15 | Gaceta N° 10, 2026-01-19 | 2026-01-19 | 184 |
| `ley/1271` | Ley N° 1271 | amendment | 2026-01-15 | Gaceta N° 10, 2026-01-19 | 2026-01-19 | 184 |

See [`laws.csv`](laws.csv) and [`SOURCES.md`](SOURCES.md). Normas Jurídicas de Nicaragua lists no constitutional reform
after Ley N° 1271 (checked 2026-10-28).

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
- check_repo.py: 15 versions, 2985 files byte-equal; 4 official versions equal their pages as letters and digits; 14 replayed files are runs of their laws; 0 failures
- test_repo.py: 7/7 passed

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
