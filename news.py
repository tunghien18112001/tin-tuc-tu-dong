
import feedparser
import html
import re
from datetime import datetime
from email.utils import parsedate_to_datetime
from pathlib import Path
from zoneinfo import ZoneInfo

FEED_FILE = Path("feeds.txt")
OUTPUT_FILE = Path("NEWS.md")
MAX_PER_FEED = 10

def clean_text(value):
    value = html.unescape(str(value or ""))
    value = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", value).strip()

def get_date(entry):
    try:
        if entry.get("published"):
            dt = parsedate_to_datetime(entry["published"])
            return dt.strftime("%Y-%m-%d %H:%M")
        if entry.get("updated"):
            dt = parsedate_to_datetime(entry["updated"])
            return dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        pass
    return "Chua ro"

feeds = [
    line.strip()
    for line in FEED_FILE.read_text(encoding="utf-8").splitlines()
    if line.strip() and not line.strip().startswith("#")
]

all_news = []
seen = set()
failed = []

for url in feeds:
    try:
        feed = feedparser.parse(url)

        if not feed.entries:
            failed.append(url)
            continue

        source = clean_text(
            feed.feed.get("title", url)
        )

        count = 0
        for entry in feed.entries:
            link = entry.get("link", "").strip()
            title = clean_text(entry.get("title", ""))

            if not link or not title or link in seen:
                continue

            seen.add(link)

            description = clean_text(
                entry.get("summary", entry.get("description", ""))
            )

            all_news.append({
                "title": title,
                "link": link,
                "source": source,
                "date": get_date(entry),
                "description": description[:500]
            })

            count += 1
            if count >= MAX_PER_FEED:
                break

    except Exception as error:
        print(f"Loi doc RSS {url}: {error}")
        failed.append(url)

if not all_news:
    raise RuntimeError(
        "Khong lay duoc tin. Hay kiem tra ket noi va cac RSS."
    )

now = datetime.now(
    ZoneInfo("Asia/Ho_Chi_Minh")
).strftime("%d/%m/%Y %H:%M")

lines = [
    "# BAN TIN TUC TU DONG",
    "",
    f"> Cap nhat lan cuoi: {now} (gio Viet Nam)",
    "",
    f"> Tong so bai: {len(all_news)}",
    "",
    "---",
    ""
]

for i, item in enumerate(all_news, 1):
    lines.extend([
        f"## {i}. [{item['title']}]({item['link']})",
        "",
        f"- **Nguon:** {item['source']}",
        f"- **Thoi gian dang:** {item['date']}",
    ])

    if item["description"]:
        lines.extend([
            "",
            f"> {item['description']}"
        ])

    lines.extend(["", "---", ""])

if failed:
    lines.extend([
        "## Nguon chua doc duoc",
        "",
        *[f"- `{url}`" for url in failed],
        ""
    ])

OUTPUT_FILE.write_text(
    "\n".join(lines),
    encoding="utf-8"
)

print(f"Da tong hop {len(all_news)} bai tin.")
print(f"Da ghi ket qua vao {OUTPUT_FILE}")
