import feedparser
from datetime import datetime
import pytz

# Шляхи
TEMPLATE_PATH = "template.html"
OUTPUT_PATH = "index.html"

# RSS-стрічка Google News
RSS_URL = "https://news.google.com/rss/search?q=real+estate+USA&hl=en-US&gl=US&ceid=US:en"

def fetch_news():
    feed = feedparser.parse(RSS_URL)
    articles = []

    for entry in feed.entries:
        title = entry.title
        link = entry.link
        published = entry.get("published", "")
        articles.append({
            "title": title,
            "link": link,
            "published": published
        })

    return articles

def generate_news_html(news_items):
    html = '<h2>📰 US Real Estate News (auto-updated)</h2>\n'
    html += "<ul class='list-unstyled'>\n"
    for item in news_items:
        html += f'''  <li style="margin-bottom:15px;">
            <a href="{item["link"]}" target="_blank">{item["title"]}</a><br>
            <small>{item["published"]}</small>
        </li>\n'''
    html += "</ul>\n"
    html += f"<p><em>Last updated: {datetime.now(pytz.timezone('US/Eastern')).strftime('%Y-%m-%d %H:%M:%S %Z')}</em></p>"
    return html

def inject_into_template(news_html):
    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        template = f.read()

    if "<!-- NEWS_CONTENT_PLACEHOLDER -->" not in template:
        raise ValueError("Placeholder <!-- NEWS_CONTENT_PLACEHOLDER --> not found in template.html")

    final_html = template.replace("<!-- NEWS_CONTENT_PLACEHOLDER -->", news_html)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(final_html)

def main():
    print("🔍 Fetching news from Google News RSS...")
    news = fetch_news()
    print(f"✅ {len(news)} articles found.")
    news_html = generate_news_html(news)
    inject_into_template(news_html)
    print("📄 index.html updated and ready for GitHub Pages!")

if __name__ == "__main__":
    main()
