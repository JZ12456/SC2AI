# Terran Bot (Half-Baked)

Features:
- Rule-based Terran bot (macro + army) for SC2 using python-sc2.
- Smart micro: focus fire, kiting, Medivac support.
- Medivac drops and healing logic.
- Auto-save replays to `replays/` folder.
- Logs match stats to `match_log.csv`.
- Works against all races with configurable difficulty.

## Requirements (SC2 needed)

- Python virtual enviornement
- BurnySC2-0.11.2
- numpy
- pandas

## Run

python terran_bot_v2.py --race Zerg --difficulty Medium
```
replace `Zerg` with `Protoss` or `Terran` and `Medium` with `Easy`/`Hard` as needed
