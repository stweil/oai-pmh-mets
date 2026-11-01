# AGENTS.md

## What this is

Single-file CLI tool (`mets.py`, v2.0) to fetch and process METS/ALTO data
from German library OAI-PMH endpoints (UB Mannheim, Marchivum, DARIA-DE,
Giessen, WLB, SHLB, ...). No package, no tests, no CI, no lint config —
verify changes by running the script directly.

## Setup

- Python 3.15: `python3 -m venv venv3.15 && source venv3.15/bin/activate &&
  pip install -r requirements.txt` (lxml, matplotlib, Pillow, requests,
  sickle — all imports of `mets.py`).
- The script is executable and has a shebang: run as `./mets.py <command> ...`.
- `@OAI-PMH/...` arg-file paths are resolved relative to the **current
  working directory**, not to `mets.py` — run the documented commands from
  the repo root.

## Command structure

`./mets.py {layout|blur|makeblack|fix|format|images|oai} ...`

- The `oai` subcommand wraps OAI-PMH verbs via the `sickle` library:
  `GetRecord`, `Identify`, `ListIdentifiers`, `ListMetadataFormats`,
  `ListRecords`, `ListSets`.
- Files under `OAI-PMH/` (one per source, **public**) are argparse `@file`
  argument files (`fromfile_prefix_chars="@"`) containing `--oai-url=...`
  and, where applicable, `--image-url`.
- Sources that require login have a matching file in `OAI-PMH.private/`
  (**gitignored, never commit**) with `--login-url`/`--username`/`--password`.
  Pass *both* `@files`; later flags override earlier ones:
  `./mets.py oai @OAI-PMH/Marchivum @OAI-PMH.private/Marchivum GetRecord ...`
- Sources without login need only the public file:
  `./mets.py oai @OAI-PMH/UB-Giessen ListIdentifiers --set <set> > out.list`
- Do not copy credentials into code; `OAI-PMH.private/` is the only place they live.
- `images` downloads page images from the source's image cache into
  `max/<id>.jpg` in the current directory; images that already exist are
  **skipped** (safe to re-run). Requires `--image-url` and at least one
  image id; authentication is optional — at most one of `--login-url`
  (full login) or `--session-id` (reuses an existing session cookie,
  skips login), none for public images. Example:
  `./mets.py images @OAI-PMH/Marchivum @OAI-PMH.private/Marchivum <id>...`.

## GetRecord behavior (easy to miss)

- `oai GetRecord --identifier <id>` prints one record to stdout; at least
  one of `--identifier`/positional identifiers is required (clear error,
  no network access otherwise).
- Positional identifiers are written to `mets/<id>.xml` in the current
  directory; files that already exist are **skipped** (safe to re-run).
- `--recursive` follows `mets:mptr` child pointers in the LOGICAL
  `structMap` and appends discovered identifiers, fetching them too.
- All `oai` verbs accept `--pretty` (default: compact output).

## Known dead/quirky code — don't assume it works

- `fix` subcommand is registered but never dispatched in `main()` → running
  it prints `Error: unknown command fix`.
- `format` subcommand is a stub that only prints its args.
- `images` declares `--oai-url` but never uses it — do not remove it; it
  exists so shared `OAI-PMH/` source arg files (which also serve the `oai`
  subcommand) can be passed unchanged.
- `blur`/`makeblack` hardcode the ALTO v2 namespace (`//alto:Illustration`);
  only `layout` falls back to ALTO v3/v4 namespaces.
- `layout` calls `plt.show()`: it needs a GUI/display, it will not work
  headless without configuration.
