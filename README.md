# Nicaragua: law history in git


The law of Nicaragua as a git history: one file per article, one commit per version on the day it took effect, and the law that made each change as the commit's author. `git blame` names the law behind every paragraph; `git log` lists every change to an article; picking a date gives the text in force that day.

Part of [lexifina/global-law](https://github.com/lexifina/global-law), one git history for every country's law: this is Nicaragua's national law, which global-law reads at `nicaragua/national/acts/`.

**What is in it now:** the Constitución Política de la República de Nicaragua, in 15 versions from the official text of 2014 to Ley N° 1271 (in force 19 January 2026): four official whole texts (2014, the Digesto consolidations of 2022 and 2024, and the Texto Íntegro of 2025) and 11 reform laws between them. No other act yet. [`laws.csv`](laws.csv) lists every version with its Gaceta and its in-force day, and [`SOURCES.md`](SOURCES.md) links each one to its page and its Gaceta issue.

Each article is one file in `constitucion/` (`constitucion/articulo-001.md` is Article 1); `preambulo.md`, `estructura.md` (titles and chapters) and `cierre.md` (the closing formula) hold the rest. Ley N° 1234 renumbered the articles on 18 February 2025 (202 became 184): from then on a file holds the article of that number in the new text, so compare texts, not paths, across that commit.

The text is in Spanish, as Normas Jurídicas de Nicaragua prints it, typing errors included. An English translation is not part of this record.

## Questions as git commands

| Question | Command |
| --- | --- |
| Every change to Article 1 of the Constitution | `git log -p --word-diff -- constitucion/articulo-001.md` |
| Which law wrote each line of Article 1? | `git blame constitucion/articulo-001.md` |
| Every version of the Constitution, with the day each took effect | `git log --format="%h %(trailers:key=In-force,valueonly,separator=) %an" -- constitucion` |
| Article 1 as in force on 1 January 2024 | `python tools/in_force_on.py 2024-01-01 constitucion 1` |

**Outside git**, we also host this record publicly, for free:

- **[Ask Claude about Nicaraguan law](https://global-law.lexifina.com/v1/try_claude?country=nicaragua)**: opens Claude with a first question ready.
- **[Ask ChatGPT](https://global-law.lexifina.com/v1/try_chatgpt?country=nicaragua)**: the same question in ChatGPT.
- **[Call the API in your browser](https://global-law.lexifina.com/v1/search_law?query=vacaciones&jurisdictions=nicaragua)**: a search of Nicaraguan law for "vacaciones" (paid leave), returned as JSON. See the [documentation here](https://lexifina.com/api/global-law).

Both assistants read the record through the free Global law connector (MCP, `https://global-law.lexifina.com/mcp`); the first time, the chat gives you the link that adds it. Ask in Spanish or in English.

**Host it yourself easily.** All it takes is git and Python, and the tools run on your machine:

```sh
git clone --depth 1 https://github.com/lexifina/global-law && cd global-law
python3 tools/countries.py add nicaragua/national/acts
python3 tools/law.py show 2026-01-01 nicaragua/national/acts/constitucion/articulo-001.md
```

Opened in Claude Code, Cursor, VS Code or Codex, the clone also starts a local MCP server with the same tools ([MCP.md](https://github.com/lexifina/global-law/blob/main/MCP.md)).

## Dates

Each commit is dated at noon, America/Managua (UTC-6), on the day the version took effect, and carries it in its `In-force:` trailer, beside `Enacted:` (approved by the Asamblea Nacional) and `Published:` (the issue of La Gaceta, Diario Oficial):

- every law here takes effect on its publication in La Gaceta, as its last article says, and the commit's `In-force-basis:` trailer quotes that clause; two laws in force on one day are two commits a second apart, in the order of their numbers;
- the reforms of January 2024 (Leyes N° 1186, 1187, 1188 and 1190) still carry the clause of their first-reading bill; they are dated by the publication of the promulgated laws, which the 2024 consolidation incorporates;
- the 2014 text is dated 10 February 2014, the day Ley N° 854, whose reforms it incorporates, took effect: read its lines as in force on that day at the latest.

Each change is credited to the law that made it (`Ley N° 1057`); the 2014 text, which holds the 1987 Constitution with every reform up to Ley N° 854, to its publisher, and the Digesto consolidations to the laws that gave them legal force (Leyes N° 1091 and 1196). Those consolidations change no rule, but their commits carry the Digesto's corrections of typing errors and punctuation. The committer is Lexifina.

## How it is checked

- `tools/check_repo.py` compares every version in git, byte for byte, with what the source says: the four official texts with their own pages, and each reform law's version with the previous one plus the words the law quotes (15 versions, 2,985 files, 0 failures).
- Each official text is compared again as letters and digits taken straight from its page, without the parser, and every article a reform law replaced is word for word the same in the next official text. The 2026 reforms have no official text after them yet.
- `tools/test_repo.py` checks that blame, the dated tool and the commands above work. The results, the sha256 of every page used and the steps to rebuild it with the same hashes are in [`REPRODUCE.md`](REPRODUCE.md).

## What it does not show

- **Other acts.** Only the Constitution is here; Normas Jurídicas de Nicaragua listed 27,028 documents on 28 October 2026.
- **The Constitution before 2014.** The 1987 original and the reforms of 1990 to 2014 are here only as the 2014 text.
- **Changes that leave the words alone**, such as Ley N° 1269 art. 3 (read "Procuraduría General de Justicia" wherever the law says "Procuraduría General de la República") or rulings of the Corte Suprema de Justicia.
- **Texts in the languages of the Caribbean Coast** (the database holds a Mayangna text of 2012).

## Sources

| Source | Kind | Past versions | Notes |
| --- | --- | --- | --- |
| [Normas Jurídicas de Nicaragua](http://legislacion.asamblea.gob.ni/Normaweb.nsf/) (Asamblea Nacional) | Official legislation database | yes, the whole texts of 2014, 2022, 2024 and 2025 and every reform law | Each document links to the scan of the La Gaceta issue that published it |
| La Gaceta, Diario Oficial | Official gazette, the authoritative text | as published | Two issues read by hand to confirm a date and a paragraph |

## Licence

See [`LICENSE`](LICENSE). Laws are not protected by copyright in Nicaragua (Ley N° 312, Ley de Derecho de Autor y Derechos Conexos, art. 16), and the database publishes no terms of use. The history, tables and tools are CC0 1.0.

No AI model wrote legal text or ran at build time; the code was written by Claude Code with Claude Opus 5.5, which also chose the scope and read the in-force clauses (see [`REPRODUCE.md`](REPRODUCE.md)).

## More

From [lexifina/global-law](https://github.com/lexifina/global-law):

- [FEATURES.md](https://github.com/lexifina/global-law/blob/main/FEATURES.md): every feature, and what every corpus must support (`git blame`, `law.py`, the MCP tools)
- [FAQ.md](https://github.com/lexifina/global-law/blob/main/FAQ.md): questions and answers · [CONTRIBUTING.md](https://github.com/lexifina/global-law/blob/main/CONTRIBUTING.md): proposing changes · [MCP.md](https://github.com/lexifina/global-law/blob/main/MCP.md): the MCP server · [REPRODUCE.md](https://github.com/lexifina/global-law/blob/main/REPRODUCE.md): how it was built · [CHANGELOG.md](https://github.com/lexifina/global-law/blob/main/CHANGELOG.md)
- [FRESHNESS.md](https://github.com/lexifina/global-law/blob/main/FRESHNESS.md): how current each corpus is · [Monitoring](https://github.com/lexifina/global-law/tree/main/monitoring): whether updates are running · [WATCHING.md](https://github.com/lexifina/global-law/blob/main/WATCHING.md): how each official source is watched for changes
- [performance/](https://github.com/lexifina/global-law/tree/main/performance): how fast the tools are, measured
- [visualisations/](https://github.com/lexifina/global-law/tree/main/visualisations): charts and bridges across the world's law
- [Vulnerabilities](https://github.com/lexifina/global-law/tree/main/vulnerabilities): mistakes in legislation as published
