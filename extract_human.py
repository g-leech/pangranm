#!/usr/bin/env python3
"""Extract clean human prose from Jekyll posts in ../argmin-gravitas/_posts.

Strips YAML frontmatter, Liquid tags/assigns, HTML tags, and quoted material
(blockquotes and Markdown '>' quotes) so that what we feed Pangram is the
author's own running prose rather than markup or other people's quotations.
"""
import json
import os
import re
import glob

POSTS_DIR = os.path.expanduser("~/code/argmin-gravitas/_posts")
OUT = os.path.join(os.path.dirname(__file__), "human_samples.json")
MIN_WORDS = 120      # skip thin posts
TARGET_WORDS = 350   # trim each sample to roughly this for fair comparison
MAX_SAMPLES = 100


def strip_frontmatter(text):
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            return parts[2]
    return text


def clean(text):
    text = strip_frontmatter(text)
    # Liquid tags/expressions {% ... %} and {{ ... }}
    text = re.sub(r"\{%.*?%\}", " ", text, flags=re.DOTALL)
    text = re.sub(r"\{\{.*?\}\}", " ", text, flags=re.DOTALL)
    # HTML comments and tags
    text = re.sub(r"<!--.*?-->", " ", text, flags=re.DOTALL)
    text = re.sub(r"<[^>]+>", " ", text)
    # Drop Markdown blockquote lines (other people's words)
    lines = [ln for ln in text.splitlines() if not ln.lstrip().startswith(">")]
    text = "\n".join(lines)
    # Markdown links [text](url) -> text ; images ![..](..) -> ''
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", text)
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    # Headings / list markers / emphasis punctuation
    text = re.sub(r"^[#>*\-\s]+", "", text, flags=re.MULTILINE)
    text = text.replace("**", "").replace("__", "").replace("`", "")
    # Footnote refs like [3]
    text = re.sub(r"\[\d+\]", " ", text)
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


def trim_words(text, n):
    words = text.split()
    if len(words) <= n:
        return text
    trimmed = " ".join(words[:n])
    # cut back to last sentence end for cleanliness
    m = re.search(r"^(.*[.!?])\s", trimmed[::-1])
    return trimmed  # keep simple; trimming mid-sentence is fine for detection


def main():
    paths = sorted(glob.glob(os.path.join(POSTS_DIR, "*.md"))
                   + glob.glob(os.path.join(POSTS_DIR, "*.markdown")))
    samples = []
    for p in paths:
        with open(p, encoding="utf-8", errors="ignore") as f:
            raw = f.read()
        body = clean(raw)
        if len(body.split()) < MIN_WORDS:
            continue
        samples.append({
            "id": os.path.basename(p),
            "label": "human",
            "text": trim_words(body, TARGET_WORDS),
        })
        if len(samples) >= MAX_SAMPLES:
            break
    with open(OUT, "w") as f:
        json.dump(samples, f, indent=2, ensure_ascii=False)
    print(f"Wrote {len(samples)} human samples to {OUT}")
    wc = [len(s["text"].split()) for s in samples]
    print(f"Word counts: min={min(wc)} max={max(wc)} mean={sum(wc)//len(wc)}")


if __name__ == "__main__":
    main()
