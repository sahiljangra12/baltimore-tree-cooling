# Clean-room reproduction record

**25 October 2026.** The committed repository was cloned into an empty directory and rebuilt from scratch:

1. `git clone` of commit `3c8648d` into a new folder (no generated files present).
2. New Python 3.10.12 virtual environment, packages installed only from `requirements-lock.txt`.
3. `bash run_all.sh`: rebuilt all tables and figures from `data/raw/extraction_packed.txt` in 16 seconds (wall clock).
4. `python3 src/09_verify.py`: **25 of 25 checks passed.**

## Rebuilt versus committed results

| File | Largest absolute difference |
|---|---|
| `outputs/tables/event_study_main.csv` | 1.4 × 10⁻¹⁵ |
| `outputs/tables/event_study_binary.csv` | 3.7 × 10⁻¹⁵ |
| `outputs/tables/csa_event_study.csv` | 2.2 × 10⁻¹⁶ |
| `outputs/results.json` (every number) | 4.4 × 10⁻¹⁶ |

The differences are at the limit of double-precision arithmetic (about 10⁻¹⁵), so the rebuilt
results are identical to the committed ones. Figure PDFs differ byte-for-byte only because they
embed a creation timestamp.

The same rebuild runs automatically on GitHub Actions for every push (`.github/workflows/reproduce.yml`).
