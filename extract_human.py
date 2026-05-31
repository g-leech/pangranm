#!/usr/bin/env python3
"""Extract clean human prose from Gavin's blog by scraping gleech.org/archive.

Fetches the archive index, follows each post link, and pulls the running prose
out of the post body. Strips quoted material (blockquotes and their
attributions), HTML markup, and the trailing comment/subscribe furniture so
that what we feed Pangram is the author's own prose rather than markup or other
people's quotations.
"""
import json
import os
import re
import time
import html as htmllib
import urllib.request
import urllib.error

BASE = "https://www.gleech.org"
ARCHIVE_URL = BASE + "/archive"
OUT = os.path.join(os.path.dirname(__file__), "human_samples.json")
USER_AGENT = "pangranm-extract-human/1.0 (+https://gleech.org)"
REQUEST_DELAY = 0.5  # seconds between requests, to be polite
TIMEOUT = 30

MIN_WORDS = 120      # skip thin posts
TARGET_WORDS = 350   # trim each sample to roughly this for fair comparison
MAX_SAMPLES = 100


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return resp.read().decode("utf-8", errors="ignore")


def post_links(archive_html):
    """Return ordered, de-duplicated list of post URLs from the archive."""
    hrefs = re.findall(r'class=post-link href=([^\s>]+)', archive_html)
    seen = set()
    urls = []
    for href in hrefs:
        href = href.strip('"').strip("'")
        url = href if href.startswith("http") else BASE + href
        if url not in seen:
            seen.add(url)
            urls.append(url)
    return urls


def clean(post_html):
    """Pull the author's running prose out of a post's HTML."""
    m = re.search(r"<article class=post-content>(.*?)</article>",
                  post_html, flags=re.DOTALL)
    if not m:
        return ""
    text = m.group(1)
    # Drop the trailing "Leave a comment" form and subscribe block.
    text = re.split(r"<div class=accordion", text, maxsplit=1)[0]
    # Remove quoted material (blockquotes + their attributions) and non-prose
    # blocks entirely, contents and all.
    for tag in ("blockquote", "center", "style", "script", "svg", "form",
                "figure", "table"):
        text = re.sub(rf"<{tag}\b.*?</{tag}>", " ", text,
                      flags=re.DOTALL | re.IGNORECASE)
    # HTML comments and remaining tags
    text = re.sub(r"<!--.*?-->", " ", text, flags=re.DOTALL)
    text = re.sub(r"<[^>]+>", " ", text)
    # Decode entities (&amp; &rsquo; etc.)
    text = htmllib.unescape(text)
    # Footnote refs left behind as bare digits, e.g. "debate 3 ."
    text = re.sub(r"\[\d+\]", " ", text)
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


def trim_words(text, n):
    words = text.split()
    if len(words) <= n:
        return text
    return " ".join(words[:n])  # trimming mid-sentence is fine for detection


def slug_of(url):
    return url.rstrip("/").rsplit("/", 1)[-1] or url


def main():
    archive_html = fetch(ARCHIVE_URL)
    urls = post_links(archive_html)
    print(f"Found {len(urls)} post links in archive")
    samples = []
    for url in urls:
        try:
            post_html = fetch(url)
        except (urllib.error.URLError, urllib.error.HTTPError) as e:
            print(f"  skip {url}: {e}")
            continue
        finally:
            time.sleep(REQUEST_DELAY)
        body = clean(post_html)
        if len(body.split()) < MIN_WORDS:
            continue
        samples.append({
            "id": slug_of(url),
            "label": "human",
            "text": trim_words(body, TARGET_WORDS),
        })
        if len(samples) >= MAX_SAMPLES:
            break
    with open(OUT, "w") as f:
        json.dump(samples, f, indent=2, ensure_ascii=False)
    print(f"Wrote {len(samples)} human samples to {OUT}")
    wc = [len(s["text"].split()) for s in samples]
    if wc:
        print(f"Word counts: min={min(wc)} max={max(wc)} mean={sum(wc)//len(wc)}")


if __name__ == "__main__":
    main()
