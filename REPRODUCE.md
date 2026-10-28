# Reproduce

Data retrieved 2026-10-28; built for 2026-10-29. The build is deterministic: the same data gives the same commit hashes.

## Sources and requests

Normas Jurídicas de Nicaragua (http://legislacion.asamblea.gob.ni/Normaweb.nsf/), an IBM Domino database of the Asamblea
Nacional. Two kinds of request, plain HTTP GET with a browser User-Agent and gzip, one at a time:
- the default view as JSON, `Normaweb.nsf/$defaultview?ReadViewEntries&...&outputformat=JSON` (every document's
  category, date, number, title and id: 27,028 documents), read once to find every reform of the Constitution;
- each text page, `Normaweb.nsf/xpNorma.xsp?documentId=<id>&action=openDocument`; the official text is the
  `view:_id1:computedField1` span.

Fetch rate: one request at a time, no parallel requests, each answer cached on disk with its sha256 (`tools/cache`,
git-ignored, negative answers included). 79 requests are logged in the cache, including the gate checks and two
Gaceta PDFs read to confirm a date and a paragraph. Before the cache existed, the triage made about 40 requests to the
same host (view pages, the probe of the constitution page, Ley N° 312). robots.txt: none (HTTP 404) on
legislacion.asamblea.gob.ni and www.asamblea.gob.ni. No terms of use are published.

The pages used, with the sha256 of each answer:
- texto/2014: `http://legislacion.asamblea.gob.ni/Normaweb.nsf/xpNorma.xsp?documentId=C93CBD0FF408D07306257C8C004F6953&action=openDocument`, sha256 `21162d0ab38fc0e4e15ce2f19bd138a108d3923f020736eb9d609f3f5f33921f`, retrieved 2026-10-28T23:31:39Z
- ley/1014: `http://legislacion.asamblea.gob.ni/Normaweb.nsf/xpNorma.xsp?documentId=5EDEF87CC36977F906258722004F1211&action=openDocument`, sha256 `3f6c7a4b94037a0a86895396eab9f5291711873c4d955955e8bea130c7a5df0b`, retrieved 2026-10-28T23:31:44Z
- ley/1057: `http://legislacion.asamblea.gob.ni/Normaweb.nsf/xpNorma.xsp?documentId=259E2FCBC244949106258662007A06E6&action=openDocument`, sha256 `465fd0dcb2be592ab334c4a937cddb8ee0b815f82084b4ed0585eb3036811014`, retrieved 2026-10-28T23:31:45Z
- digesto/2022: `http://legislacion.asamblea.gob.ni/Normaweb.nsf/xpNorma.xsp?documentId=2BA40AEED64D0549062588CC00768418&action=openDocument`, sha256 `bd9f4eaf1e7a6dd563a91c1c58c65c792aae447ca06a6ea86e081f3cc6ab4022`, retrieved 2026-10-28T23:31:50Z
- ley/1185: `http://legislacion.asamblea.gob.ni/Normaweb.nsf/xpNorma.xsp?documentId=6F652D291FEBC77006258AB40069B6C5&action=openDocument`, sha256 `0d20f1112f928d7f2765a386f2b6e65bf752c0d347298c5f9c4c96604a79a147`, retrieved 2026-10-28T23:31:45Z
- ley/1186: `http://legislacion.asamblea.gob.ni/Normaweb.nsf/xpNorma.xsp?documentId=8E897220BA33496406258AA9006FC1D8&action=openDocument`, sha256 `a7591bd43f1f0cc134d18e915ef48eadb67965f64e597f7b364e96f43123e5dd`, retrieved 2026-10-28T23:31:46Z
- ley/1187: `http://legislacion.asamblea.gob.ni/Normaweb.nsf/xpNorma.xsp?documentId=5D94AB00AF6773AC06258AAC004B32D7&action=openDocument`, sha256 `c972fe4792e3cb40c64a1c4422c65fa2d700e77043b7b088c9e5e0f60699adcc`, retrieved 2026-10-28T23:31:46Z
- ley/1188: `http://legislacion.asamblea.gob.ni/Normaweb.nsf/xpNorma.xsp?documentId=7A49A016CD1ABCA906258AAC004D31F6&action=openDocument`, sha256 `ef540e74e77fab92ae588a9fb1eda2f08cd001ce4eb7ac19ee7ababf978ab4ec`, retrieved 2026-10-28T23:31:47Z
- ley/1190: `http://legislacion.asamblea.gob.ni/Normaweb.nsf/xpNorma.xsp?documentId=B7DBCF55D795103406258AAC004E2D4E&action=openDocument`, sha256 `51d0b326d0c0ed14809757cd678fe027c8c047c88d971a1d17c76890755247e6`, retrieved 2026-10-28T23:31:47Z
- digesto/2024: `http://legislacion.asamblea.gob.ni/Normaweb.nsf/xpNorma.xsp?documentId=7BAB8534B193AA9606258B89005E93F0&action=openDocument`, sha256 `ce4a803c7fcc610409eaeaf9bd0e37a253b1fe9ce08c1f55528d63c85f89ee84`, retrieved 2026-10-28T23:31:50Z
- texto/2025: `http://legislacion.asamblea.gob.ni/Normaweb.nsf/xpNorma.xsp?documentId=2798FEE6DACD52B506258C360051E856&action=openDocument`, sha256 `ce7f2ed843d77712a5cfce9d4413ad1ee9b197779b6c2b97979cd0035bfd4a6c`, retrieved 2026-10-28T23:31:44Z
- ley/1268: `http://legislacion.asamblea.gob.ni/Normaweb.nsf/xpNorma.xsp?documentId=0A8606CDF5AC451F06258D5C005CBEE8&action=openDocument`, sha256 `17feee0acadbc69f67d6d20e330c0fc590f49ff715e7becc8636405d44d57ebb`, retrieved 2026-10-28T23:31:47Z
- ley/1269: `http://legislacion.asamblea.gob.ni/Normaweb.nsf/xpNorma.xsp?documentId=1C542C6C8834FF1206258D5C007918C4&action=openDocument`, sha256 `29075c3baaceda3b0634de340fa05de070f21f681b9444e6f5fd3acc2b3bbcff`, retrieved 2026-10-28T23:31:48Z
- ley/1270: `http://legislacion.asamblea.gob.ni/Normaweb.nsf/xpNorma.xsp?documentId=F3E19EB1F057532B06258D5C005C0CE6&action=openDocument`, sha256 `4dc3bed5b2addfaa61d689a07eccf610b2378908379d90390a761da40c6db752`, retrieved 2026-10-28T23:31:48Z
- ley/1271: `http://legislacion.asamblea.gob.ni/Normaweb.nsf/xpNorma.xsp?documentId=2070D3F189509FC106258D5C005C3CB6&action=openDocument`, sha256 `5eb9d65cf634b99a45bd137226c9a05688d4a597a72fd903230f7f82fc4120db`, retrieved 2026-10-28T23:31:49Z

## Steps

1. `python -I -X utf8 tools/build.py --repo <dir> --today <YYYY-MM-DD>` (online once; `--offline` rebuilds from the
   cache). `--verify-rebuild` builds again in a temporary folder and compares HEAD.
2. `python -I -X utf8 tools/check_repo.py --repo <dir> --record`; `python -I -X utf8 tools/test_repo.py --repo <dir> --record`.
3. Build again (the documentation then carries the results of step 2), `--verify-rebuild`, and
   `python scripts/global-law/check_corpus.py <dir>` and `python scripts/test_corpus.py <dir> tools/in_force_on.py` from
   the lexifina repository.

Tool versions: Python 3.12 (standard library only; PyMuPDF only to read two Gaceta PDFs during the checks by hand), git,
curl (Windows). Builder blob hashes (`git hash-object`):
- `build.py`: `31403c1d47354fe593ae6309b98b1f86e924376d`
- `source.py`: `d03b5d2706cb3f96eb038accae19df936dad8011`
- `parse.py`: `87a38c395a96802c9e2d506634d2b4336b078722`
- `versions.py`: `be7d3b0bc0ab072b313e5fcd0329c0c5eecedf7f`
- `reproduce.py`: `05d1324f59ad752c496c2389747d2f30b2066d21`
- `check_repo.py`: `2a617c511721db5b9a78bc40de05b8b639b5f551`
- `test_repo.py`: `4189e293142ceaf5ae2ce8095e1c6018c022c9f3`
- `in_force_on.py`: `876777d83baf9bfa93b9954352360a53503a05c7`

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

- check_repo.py: 15 versions, 2985 files byte-equal; 4 official versions equal their pages as letters and digits; 14 replayed files are runs of their laws; 0 failures
- test_repo.py: 7/7 passed
