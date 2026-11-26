# Estructura / Structure

Una carpeta por norma, un archivo por artículo. / One folder per norm, one file per article.

```
constitucion/                         Constitución Política (texto de 2014 a hoy)
codigos/<nombre>/                     códigos (Código Penal, Código Civil, Código del Trabajo, ...)
leyes/<año>/<número>-<nombre>/        leyes de la Asamblea Nacional (año de publicación en La Gaceta)
decretos-ley/<año>/<número>-<nombre>/ decretos-ley
reglamentos/<año>/<número>-<nombre>/  reglamentos
decretos/<año>/<número>-<nombre>/     decretos ejecutivos y presidenciales
normas.csv                            índice: carpeta, número, título, versiones, fuente en Normaweb
```

Inside a norm's folder / dentro de la carpeta de una norma:

- `preambulo.md`: title, approval and publication lines, enacting formula (todo lo anterior al primer artículo);
- `articulo-NNN.md` (`articulo-NNN-bis.md`, ...): one article, headed `# Artículo N`; codes with more than 900
  articles group them in sub-folders of 500 (`0001-0500/`, ...), so no folder holds more than 1,000 entries;
- `estructura.md`: the headings (Libro, Título, Capítulo, Sección) and the article each comes before;
- `cierre.md`: the signing and promulgation lines;
- `texto.md` instead of the articles when a norm has no numbered articles.

## History / historia

One commit per version of a norm. The versions are the documents Normaweb links as one norm ("Ver enlace a última
versión de Texto Publicado"): the text as first published and the later official texts (Digesto consolidations,
texts with the reforms incorporated).

- Commit date: 12:00 America/Managua on the day the version came into force. For the first text, its own vigencia
  clause (publication in La Gaceta, or N days/months after it, or a stated day); for a later official text, its
  publication in La Gaceta. The trailer `In-force-basis` quotes the clause or names the rule used. Days before
  1970 cannot be git dates: those commits carry 1970-01-01 and the real day at the start of the subject.
- Author: the law that made the version (`Ley N° 641`; for a Digesto consolidation the Digesto law, e.g. `Ley N°
  1159`). Committer: Lexifina.
- Trailers: `Kind` (baseline, consolidation), `Enacted`, `Published`, `In-force`, `In-force-basis`,
  `Consolidated-to`, `Digesto`, `Affecting`, `Source` (the Normaweb page), `Gazette` (the La Gaceta PDF).
- Not in this record: amendments between two official texts (the reform laws are their own folders under `leyes/`),
  and repeal dates. Norms whose newest Normaweb text is not marked "Vigente" are held out until a repeal date can
  be recorded.
