# 🗂 x-post-queue

> A draft queue + **cost-aware** poster for X. See the API bill *before* you pay it.

[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![X API v2](https://img.shields.io/badge/X_API-v2-black.svg)](https://docs.x.com/)

## ✨ What it does

- 📝 Drafts are markdown files in `queue/` — one file, one post
- ✅ `--dry-run` validates every draft: length, links, **estimated cost**
- 🚀 `--post` publishes via the X API v2, logs each result to SQLite
- 📊 `--report` renders a `report.html` spend report

## 🖥 Demo

```bash
$ python x_queue.py --dry-run
[OK  ] example:           168 chars, 0 link(s), est. cost $0.015
[OK  ] example-with-link: 149 chars, 1 link(s), est. cost $0.200

2 draft(s), estimated total cost $0.215
```

## 💡 Why "cost-aware"?

Since Feb 2026 the X API is pay-per-use: **$0.015/post, $0.20/post containing a link**. Blind automation burns credits — this queue shows the price tag first.

## 🚀 Quick start

```bash
cp config.example.py config.py   # X API keys; leave blank for dry-run mode
pip install -r requirements.txt
python x_queue.py --dry-run
python x_queue.py --post
python x_queue.py --report
```

## 💰 Running costs

Dry-run: $0. Posting: exactly what X bills — shown upfront, no surprises.

## 🛠 Stack

Python · `requests` · X API v2 · SQLite (stdlib)

---

### 📬 Want it customized?

Team review flow, scheduled posting, multi-account routing — I build these to order.
**DM [@WebhookWizard](https://x.com/WebhookWizard)** · 50% deposit, settled in USDT.
