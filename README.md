# pangranm

A small experiment testing how well [Pangram](https://www.pangram.com/)'s AI-text
detector distinguishes human-written prose from AI-generated prose.

The setup is a balanced 200-sample benchmark: 100 human samples (trimmed prose
from a personal Jekyll blog) and 100 AI samples (generated essays across five
topic areas). Each sample is sent to the Pangram v3 API and scored against its
known true label.

## Result

On this set Pangram scored a perfect **200/200 (100% accuracy)** — every AI
sample was flagged AI and every human sample was cleared, with no false
positives. The numeric `fraction_ai` score was a clean 0.00 for human samples
and 1.00 for AI samples. Run `python3 analyze.py` to reproduce the report.

## Files

| File | What it is |
| --- | --- |
| `human_samples.json` | 100 human samples (`id`, `label`, `text`) |
| `ai_samples.json` | 100 AI samples (`id`, `label`, `text`) |
| `ai_raw/` | Source AI essays by topic: `essay`, `hist`, `life`, `sci`, `tech` |
| `results.json` | Raw Pangram API responses, one per sample |
| `extract_human.py` | Builds `human_samples.json` from blog posts |
| `run_pangram.py` | Sends all samples to the Pangram API → `results.json` |
| `analyze.py` | Scores `results.json` into a confusion matrix + accuracy report |

## Usage

The scripts use only the Python standard library — no dependencies to install.

**1. (Optional) Rebuild the human samples** from local Jekyll posts. This reads
`[~/code/argmin-gravitas/_posts](https://github.com/g-leech/argmin-gravitas/tree/master/_posts)`, strips frontmatter, Liquid tags, HTML, and
quoted material, and trims each post to ~350 words:

```bash
python3 extract_human.py
```

**2. Run the detection.** The API key is read from the environment and is never
stored in the repo. The script is safe to re-run — it skips samples already
recorded in `results.json` and checkpoints after every call:

```bash
PANGRAM_API_KEY=... python3 run_pangram.py
```

**3. Analyze the results:**

```bash
python3 analyze.py
```

## Notes

- `PANGRAM_API_KEY` is passed inline at runtime and lives only in your shell —
  it is not written to any file in this repo. There is no `.gitignore`; if you
  switch to storing the key in a `.env` file, add one first.
- The Pangram endpoint is `https://text.api.pangramlabs.com/v3`.
- "Flagged AI" means `prediction_short` is anything other than `"Human"`;
  `analyze.py` also reports a numeric view using `fraction_ai >= 0.5`.
