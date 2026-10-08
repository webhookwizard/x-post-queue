#!/usr/bin/env python3
"""
x-post-queue — draft queue + cost-aware poster for X.

- Drafts are markdown files in queue/ (one file = one post).
- `python x_queue.py --dry-run` validates every draft: character count,
  link detection, and the *estimated API cost* under X's 2026 pay-per-use
  pricing ($0.015/post, $0.20/post containing a link).
- `python x_queue.py --post` publishes via the X API v2 (needs credentials
  in config.py) and logs each result to posts.db (SQLite).
- `python x_queue.py --report` renders report.html from the log.

Without credentials everything runs in dry-run mode — safe to demo.
"""
import argparse
import datetime
import glob
import html
import os
import re
import sqlite3
import sys

import config

COST_PER_POST = 0.015
COST_PER_LINK_POST = 0.20
CHAR_LIMIT = 280
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
QUEUE_DIR = os.path.join(BASE_DIR, "queue")
DB_PATH = os.path.join(BASE_DIR, "posts.db")
URL_RE = re.compile(r"https?://\S+")


def load_drafts():
    drafts = []
    for path in sorted(glob.glob(os.path.join(QUEUE_DIR, "*.md"))):
        with open(path, encoding="utf-8") as f:
            text = f.read().strip()
        drafts.append({
            "slug": os.path.splitext(os.path.basename(path))[0],
            "text": text,
            "path": path,
        })
    return drafts


def validate(draft):
    issues = []
    if not draft["text"]:
        issues.append("empty")
    if len(draft["text"]) > CHAR_LIMIT:
        issues.append("{} chars > {}".format(len(draft["text"]), CHAR_LIMIT))
    links = URL_RE.findall(draft["text"])
    cost = COST_PER_LINK_POST if links else COST_PER_POST
    return issues, links, cost


def get_db():
    db = sqlite3.connect(DB_PATH)
    db.execute(
        "CREATE TABLE IF NOT EXISTS posts "
        "(slug TEXT PRIMARY KEY, posted_at TEXT, cost REAL, status TEXT)"
    )
    return db


def dry_run():
    drafts = load_drafts()
    if not drafts:
        print("queue/ is empty — add a .md draft first (see queue/example.md).")
        return
    total = 0.0
    for d in drafts:
        issues, links, cost = validate(d)
        total += cost
        flag = "OK  " if not issues else "FAIL"
        line = "[{}] {}: {} chars, {} link(s), est. cost ${:.3f}".format(
            flag, d["slug"], len(d["text"]), len(links), cost)
        if issues:
            line += " — " + "; ".join(issues)
        print(line)
    print("\n{} draft(s), estimated total cost ${:.3f}".format(len(drafts), total))


def post():
    missing = [k for k in ("X_API_KEY", "X_API_SECRET", "X_ACCESS_TOKEN", "X_ACCESS_SECRET")
               if not getattr(config, k, None)]
    if missing:
        print("Missing credentials in config.py: " + ", ".join(missing))
        print("Refusing to post. Run --dry-run to validate instead.")
        sys.exit(1)
    from requests_oauthlib import OAuth1
    import requests

    auth = OAuth1(config.X_API_KEY, config.X_API_SECRET,
                  config.X_ACCESS_TOKEN, config.X_ACCESS_SECRET)
    db = get_db()
    for d in load_drafts():
        if db.execute("SELECT 1 FROM posts WHERE slug=?", (d["slug"],)).fetchone():
            print("[skip] {} already posted".format(d["slug"]))
            continue
        issues, links, cost = validate(d)
        if issues:
            print("[skip] {}: {}".format(d["slug"], "; ".join(issues)))
            continue
        r = requests.post("https://api.x.com/2/tweets", auth=auth,
                          json={"text": d["text"]}, timeout=20)
        ok = r.status_code == 201
        db.execute(
            "INSERT OR REPLACE INTO posts VALUES (?,?,?,?)",
            (d["slug"], datetime.datetime.now(datetime.timezone.utc).isoformat(),
             cost, "posted" if ok else "error {}".format(r.status_code)),
        )
        db.commit()
        print("[{}] {} (est. cost ${:.3f})".format(
            "posted" if ok else "error", d["slug"], cost))


def report():
    db = get_db()
    rows = db.execute(
        "SELECT slug, posted_at, cost, status FROM posts ORDER BY posted_at").fetchall()
    total = sum(r[2] for r in rows)
    items = "\n".join(
        "<tr><td>{}</td><td>{}</td><td>${:.3f}</td><td>{}</td></tr>".format(
            html.escape(r[0]), html.escape(r[1]), r[2], html.escape(r[3]))
        for r in rows)
    page = """<!doctype html><html><head><meta charset="utf-8"><title>x-post-queue report</title>
<style>body{font-family:sans-serif;max-width:720px;margin:2em auto}table{border-collapse:collapse;width:100%%}td,th{border:1px solid #ccc;padding:.4em .6em;text-align:left}</style>
</head><body><h1>x-post-queue report</h1><p>%d post(s), estimated API spend $%.3f</p>
<table><tr><th>slug</th><th>posted at</th><th>est. cost</th><th>status</th></tr>%s</table></body></html>""" % (
        len(rows), total, items)
    out = os.path.join(BASE_DIR, "report.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(page)
    print("wrote {}".format(out))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--post", action="store_true")
    ap.add_argument("--report", action="store_true")
    args = ap.parse_args()
    if args.post:
        post()
    elif args.report:
        report()
    else:
        dry_run()
