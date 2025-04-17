import feedparser
from datetime import datetime
import pytz

# Шлях до шаблону та результату
TEMPLATE_PATH = "template.html"
OUTPUT_PATH = "index.html"

# Google News RSS feed по нерухомості
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
    html = "<ul>\n"
    for item in news_items:
        html += f'  <li><a href="{item["link"]}" target="_blank">{item["title"]}</a><br><small>{item["published"]}</small></li>\n'
    html += "</ul>"
    return html

def inject_into_template(news_html):
    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        template = f.read()

    final_html = template.replace("<!-- NEWS_CONTENT_PLACEHOLDER -->", news_html)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(final_html)

def main():
    print("🔍 Отримуємо новини...")
    news = fetch_news()
    print(f"✅ Знайдено {len(news)} новин.")
    html = generate_news_html(news)
    inject_into_template(html)
    print("📄 Файл index.html оновлено!")

if __name__ == "__main__":
    main()
