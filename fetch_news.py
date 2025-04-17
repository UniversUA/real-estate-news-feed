import feedparser
import json
from datetime import datetime

def fetch_google_news():
    url = "https://news.google.com/rss/search?q=real+estate+USA&hl=en-US&gl=US&ceid=US:en"
    feed = feedparser.parse(url)
    items = [{
        "title": entry.title,
        "link": entry.link,
        "published": entry.published
    } for entry in feed.entries]
    return items

def main():
    news = fetch_google_news()
    news.sort(key=lambda x: datetime.strptime(x["published"], "%a, %d %b %Y %H:%M:%S %Z"), reverse=True)
    with open("news.json", "w") as f:
        json.dump(news, f, indent=2)

if __name__ == "__main__":
    main()
