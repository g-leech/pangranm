#!/usr/bin/env python3
"""Send all human + AI samples to the Pangram API and record predictions.

Usage:
    PANGRAM_API_KEY=... python3 run_pangram.py

Reads human_samples.json and ai_samples.json, posts each text to the Pangram
v3 endpoint, and writes every raw response to results.json. Safe to re-run:
it skips samples already recorded in results.json.
"""
import json
import os
import sys
import time
import urllib.request
import urllib.error

ENDPOINT = "https://text.api.pangramlabs.com/v3"
API_KEY = os.environ.get("PANGRAM_API_KEY", "").strip()
RESULTS = os.path.join(os.path.dirname(__file__), "results.json")
SLEEP = 0.4          # polite pause between calls
MAX_RETRIES = 3


def call(text):
    body = json.dumps({"text": text}).encode()
    req = urllib.request.Request(
        ENDPOINT, data=body, method="POST",
        headers={"Content-Type": "application/json", "x-api-key": API_KEY},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode())


def load(path):
    with open(path) as f:
        return json.load(f)


def main():
    if not API_KEY:
        sys.exit("Set PANGRAM_API_KEY in the environment first.")

    samples = load("human_samples.json") + load("ai_samples.json")

    done = {}
    if os.path.exists(RESULTS):
        done = {r["id"]: r for r in load(RESULTS)}

    results = list(done.values())
    for i, s in enumerate(samples, 1):
        if s["id"] in done:
            continue
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                resp = call(s["text"])
                if isinstance(resp, dict) and resp.get("error"):
                    # API-level error (e.g. insufficient credits) — stop early.
                    sys.exit(f"API error on {s['id']}: {resp['error']}")
                results.append({"id": s["id"], "label": s["label"], "response": resp})
                print(f"[{i}/{len(samples)}] {s['id']:32s} {s['label']:6s} ok")
                break
            except urllib.error.HTTPError as e:
                detail = e.read().decode()[:200]
                print(f"[{i}/{len(samples)}] {s['id']} HTTP {e.code}: {detail}")
                if e.code in (401, 402, 403):
                    sys.exit("Auth/credit error — stopping.")
                time.sleep(2 * attempt)
            except Exception as e:
                print(f"[{i}/{len(samples)}] {s['id']} error: {e} (attempt {attempt})")
                time.sleep(2 * attempt)
        # checkpoint after every call
        with open(RESULTS, "w") as f:
            json.dump(results, f, indent=2)
        time.sleep(SLEEP)

    with open(RESULTS, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nWrote {len(results)} results to {RESULTS}")


if __name__ == "__main__":
    main()
