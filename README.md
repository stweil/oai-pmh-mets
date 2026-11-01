# oai-pmh-mets

A single-file Python CLI tool for fetching and processing METS/ALTO data
from German library OAI-PMH endpoints (UB Mannheim, Marchivum, DARIA-DE,
Giessen, WLB, SHLB, ...).

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Usage

```
./mets.py {layout|blur|makeblack|fix|format|images|oai} ...
```

- `oai` — run an OAI-PMH verb (`GetRecord`, `Identify`, `ListIdentifiers`,
  `ListMetadataFormats`, `ListRecords`, `ListSets`) via the `sickle`
  library. Results are printed to stdout; `GetRecord` with positional
  identifiers additionally writes files to `mets/<id>.xml` (existing
  files are skipped).
- `images` — download page images from a source's image cache into
  `max/<id>.jpg` (existing files are skipped).
- `layout` — visualize the ALTO layout of a file (opens a matplotlib
  window).
- `blur` / `makeblack` — blur or black out `Illustration` regions in a
  page image, using their coordinates from an ALTO file.
- `format` — stub, see `AGENTS.md`.

### Source argument files

Each file under `OAI-PMH/` holds the URL settings for one source and is
passed to `mets.py` as an argparse argument file (`@file`):

```bash
./mets.py oai @OAI-PMH/UB-Giessen ListIdentifiers --set ubg-ihd-zuz > ubg-ihd-zuz.list
```

Sources that require login additionally have a file under `OAI-PMH.private/`
with `--login-url`/`--username`/`--password`; pass both files — later
values override earlier ones:

```bash
./mets.py oai @OAI-PMH/Marchivum @OAI-PMH.private/Marchivum GetRecord --identifier 1234
```

`OAI-PMH.private/` is gitignored and **must never be committed**.
Alternatively, `--session-id` reuses an existing session cookie and
skips login.

## Contributing

See `AGENTS.md` for development notes, including known quirks of the code.

## License

GPL-3.0 or later, see [LICENSE.md](LICENSE.md).
