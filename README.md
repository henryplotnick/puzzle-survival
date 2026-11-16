# Puzzle Survival

A chess puzzle survival game: puzzles start easy and get harder, three wrong moves ends the run, no clock. Pick any Lichess puzzle theme or play mixed.

Play it at https://henryplotnick.github.io/puzzle-survival/

## Data

All 6,193,530 puzzles from the [Lichess puzzle database](https://database.lichess.org/#puzzles) (public domain, file dated 2026-11-01).

- `c/NN/<chunk>.gz` holds 512 puzzles per file, with all puzzles sorted by rating.
- `i/<theme>/<band>.bin` lists where a theme's puzzles are for one 25-point rating band.
- `manifest.json` has the theme list and per-band counts.

To rebuild from a newer database file:

```
pip install zstandard numpy
python3 tools/build_data.py lichess_db_puzzle.csv.zst . 2026-11-01
```

Note that the build script deletes and recreates its output folder, so point it at a scratch folder and copy `c/`, `i/` and `manifest.json` over.

## Credits

Chess rules by [chess.js](https://github.com/jhlywa/chess.js). Piece set by Colin M.L. Burnett.
