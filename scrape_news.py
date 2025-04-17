import feedparser
from datetime import datetime
import pytz
from dateutil import parser as dateparser

TEMPLATE_PATH = "template.html"
OUTPUT_PATH = "index.html"

RSS_FEEDS = {
    "Google Real Estate": "https://news.google.com/rss/search?q=real+estate&hl=en-US&gl=US&ceid=US:en",
    "Google Housing Market": "https://news.google.com/rss/search?q=housing+market&hl=en-US&gl=US&ceid=US:en",
    "Google Property News": "https://news.google.com/rss/search?q=property+news&hl=en-US&gl=US&ceid=US:en",
    "Google Commercial Real Estate": "https://news.google.com/rss/search?q=commercial+real+estate&hl=en-US&gl=US&ceid=US:en",
    "Bing Real Estate": "https://www.bing.com/news/search?q=real+estate&format=rss&cc=US",
    "Bing Housing Market": "https://www.bing.com/news/search?q=housing+market&format=rss&cc=US",
    "Bing Property News": "https://www.bing.com/news/search?q=property+news&format=rss&cc=US",
    "Bing Mortgage News": "https://www.bing.com/news/search?q=mortgage+news&format=rss&cc=US"
}

def fetch_all_news():
    all_articles = []
    seen = set()

    for _, url in RSS_FEEDS.items():
        feed = feedparser.parse(url)
        for entry in feed.entries:
            title = entry.title.strip()
            link = entry.link.strip()
            key = f"{title}|{link}"
            if key in seen:
                continue
            seen.add(key)

            published_str = entry.get("published", "")
            try:
                published_dt = dateparser.parse(published_str)
            except Exception:
                published_dt = datetime.min

            all_articles.append({
                "title": title,
                "link": link,
                "published": published_str,
                "datetime_obj": published_dt
            })

    all_articles.sort(key=lambda x: x["datetime_obj"], reverse=True)
    return all_articles

def generate_news_html(news_items):
    html = '<h2>📰 US Real Estate News</h2>\n'
    html += '<ul class="list-unstyled news-list">\n'
    for item in news_items:
        html += f'''<li class="news-item" style="margin-bottom:15px;">
            <a href="{item["link"]}" target="_blank">{item["title"]}</a><br>
            <small>{item["published"]}</small>
        </li>\n'''
    html += "</ul>\n"
    html += f"<p><em>Last updated: {datetime.now(pytz.timezone('US/Eastern')).strftime('%Y-%m-%d %H:%M:%S %Z')}</em></p>\n"
    return html

def inject_into_template(news_html):
    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        template = f.read()

    if "<!-- NEWS_CONTENT_PLACEHOLDER -->" not in template:
        raise ValueError("Placeholder <!-- NEWS_CONTENT_PLACEHOLDER --> not found")

    final_html = template.replace("<!-- NEWS_CONTENT_PLACEHOLDER -->", news_html)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(final_html)

def main():
    print("🔍 Fetching news...")
    news = fetch_all_news()
    print(f"✅ {len(news)} unique articles found.")
    html = generate_news_html(news)
    inject_into_template(html)
    print("📄 index.html updated!")

if __name__ == "__main__":
    main()
