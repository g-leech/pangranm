#!/usr/bin/env python3
"""Score Pangram results into a confusion matrix and accuracy report.

Uses the real Pangram v3 response schema:
  prediction_short : short categorical call, e.g. "Human", "AI", "Mixed"
  fraction_ai      : numeric fraction of the document judged AI-written
  fraction_ai_assisted, fraction_human, headline, ...

A document is treated as "flagged AI" if prediction_short is anything other
than "Human". We report the full category breakdown per truth class as well
as the collapsed binary confusion matrix and a numeric (fraction_ai >= 0.5)
view for comparison.
"""
import json
import os
from collections import Counter

RESULTS = os.path.join(os.path.dirname(__file__), "results.json")


def short(resp):
    return (resp or {}).get("prediction_short", "?")


def flagged_ai(resp):
    """Binary: did Pangram call this anything other than purely Human?"""
    return short(resp).strip().lower() != "human"


def frac_ai(resp):
    v = (resp or {}).get("fraction_ai")
    return v if isinstance(v, (int, float)) else None


def confusion(results, predicate):
    tp = fp = tn = fn = 0
    for r in results:
        truth_ai = r["label"] == "ai"
        pred_ai = predicate(r["response"])
        if truth_ai and pred_ai:
            tp += 1
        elif truth_ai and not pred_ai:
            fn += 1
        elif not truth_ai and pred_ai:
            fp += 1
        else:
            tn += 1
    return tp, fp, tn, fn


def report(title, tp, fp, tn, fn):
    n_ai, n_human, total = tp + fn, tn + fp, tp + fp + tn + fn
    print(f"\n--- {title} ---")
    print("Confusion (rows=truth, cols=Pangram):")
    print(f"{'':14s}{'flag AI':>10s}{'call human':>12s}")
    print(f"{'truth AI':14s}{tp:>10d}{fn:>12d}")
    print(f"{'truth human':14s}{fp:>10d}{tn:>12d}")
    if n_ai:
        print(f"AI recall (AI caught):          {tp}/{n_ai} = {tp/n_ai:.1%}")
    if n_human:
        print(f"Human specificity (cleared):    {tn}/{n_human} = {tn/n_human:.1%}")
        print(f"False-positive rate:            {fp}/{n_human} = {fp/n_human:.1%}")
    if total:
        print(f"Overall accuracy:               {tp+tn}/{total} = {(tp+tn)/total:.1%}")


def main():
    with open(RESULTS) as f:
        results = [r for r in json.load(f) if isinstance(r.get("response"), dict)]

    print("=" * 60)
    print(f"PANGRAM DETECTION RESULTS  (n={len(results)})")
    print("=" * 60)

    # Category breakdown per truth class
    for truth in ("human", "ai"):
        cats = Counter(short(r["response"]) for r in results if r["label"] == truth)
        n = sum(cats.values())
        print(f"\nTruth = {truth.upper()}  ({n} samples) — prediction_short breakdown:")
        for cat, c in cats.most_common():
            print(f"    {cat:24s} {c:3d}  ({c/n:.0%})")

    # Binary confusion: anything not "Human" counts as an AI flag
    report("Binary: prediction_short != 'Human'", *confusion(results, flagged_ai))

    # Numeric view: fraction_ai >= 0.5
    have_frac = [r for r in results if frac_ai(r["response"]) is not None]
    if have_frac:
        report("Numeric: fraction_ai >= 0.50",
               *confusion(have_frac, lambda resp: frac_ai(resp) >= 0.5))

    # Mean fraction_ai per truth class
    print("\nMean fraction_ai by truth class:")
    for truth in ("human", "ai"):
        vals = [frac_ai(r["response"]) for r in results
                if r["label"] == truth and frac_ai(r["response"]) is not None]
        if vals:
            print(f"    {truth:6s}: {sum(vals)/len(vals):.3f}  "
                  f"(min {min(vals):.2f}, max {max(vals):.2f})")


if __name__ == "__main__":
    main()
