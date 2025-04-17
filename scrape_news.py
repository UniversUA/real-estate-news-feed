import requests
from bs4 import BeautifulSoup
import datetime
import pytz  # For timezone handling
import re
from urllib.parse import urljoin

# --- Configuration ---
SEARCH_QUERY = "US real estate news"
# Using a generic user-agent to mimic a browser
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}
# Google News URL (adjust if needed, e.g., for different regions/languages)
# Using the /search endpoint which might be slightly more stable than the main news page structure
BASE_URL = "https://news.google.com/"
SEARCH_URL = f"{BASE_URL}search?q={SEARCH_QUERY.replace(' ', '+')}&hl=en-US&gl=US&ceid=US%3Aen"
OUTPUT_FILE = "index.html"
TIMEZONE = "America/New_York" # Timezone for relative dates like "2 hours ago"

# --- HTML Selectors (HIGHLY LIKELY TO BREAK) ---
# These selectors target the article elements on the Google News search results page.
# They need careful inspection and adjustment if Google changes its HTML structure.
ARTICLE_SELECTOR = "article" # Main container for each news item
TITLE_SELECTOR = "h3 > a" # Often the title is within an h3 and is a link
LINK_SELECTOR = "h3 > a" # The link is usually the same element as the title
SOURCE_SELECTOR = "div > div > a" # Source name might be in a nested div/a
DATETIME_SELECTOR = "time" # Google often uses <time> tags with datetime attributes

# --- Helper Functions ---
def parse_relative_date(date_str):
    """Attempts to parse relative dates like '2 hours ago', 'Yesterday'."""
    now = datetime.datetime.now(pytz.timezone(TIMEZONE))
    date_str = date_str.lower()

    if "yesterday" in date_str:
        return now - datetime.timedelta(days=1)
    if "hour" in date_str:
        hours = int(re.search(r'(\d+)\s+hour', date_str).group(1))
        return now - datetime.timedelta(hours=hours)
    if "minute" in date_str:
        minutes = int(re.search(r'(\d+)\s+minute', date_str).group(1))
        return now - datetime.timedelta(minutes=minutes)
    if "day" in date_str:
        days = int(re.search(r'(\d+)\s+day', date_str).group(1))
        return now - datetime.timedelta(days=days)

    # Fallback or handle other formats if needed
    return now # Default to now if parsing fails

def get_absolute_url(href):
    """Converts relative URLs to absolute URLs based on Google News."""
    if href.startswith('./'):
        href = href[2:] # Remove './'
    return urljoin(BASE_URL, href)

# --- Main Script Logic ---
def fetch_news():
    """Fetches news from Google News search."""
    print(f"Fetching news from: {SEARCH_URL}")
    try:
        response = requests.get(SEARCH_URL, headers=HEADERS, timeout=15)
        response.raise_for_status() # Raise an exception for bad status codes
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching news: {e}")
        return None

def parse_news(html_content):
    """Parses the HTML content to extract news articles."""
    if not html_content:
        return []

    soup = BeautifulSoup(html_content, 'html.parser')
    articles_raw = soup.select(ARTICLE_SELECTOR)
    news_items = []

    print(f"Found {len(articles_raw)} potential articles using selector '{ARTICLE_SELECTOR}'.")

    for article in articles_raw:
        title_element = article.select_one(TITLE_SELECTOR)
        link_element = article.select_one(LINK_SELECTOR)
        source_element = article.select_one(SOURCE_SELECTOR)
        datetime_element = article.select_one(DATETIME_SELECTOR)

        title = title_element.get_text(strip=True) if title_element else "N/A"
        link = get_absolute_url(link_element['href']) if link_element and link_element.has_attr('href') else "#"
        source = source_element.get_text(strip=True) if source_element else "N/A"
        date_str = datetime_element.get_text(strip=True) if datetime_element else None
        datetime_attr = datetime_element['datetime'] if datetime_element and datetime_element.has_attr('datetime') else None

        # Prioritize datetime attribute, fall back to parsing relative string
        parsed_date = None
        if datetime_attr:
            try:
                # Google often uses ISO format like '2023-10-27T10:00:00Z'
                parsed_date = datetime.datetime.fromisoformat(datetime_attr.replace('Z', '+00:00'))
            except ValueError:
                print(f"Warning: Could not parse datetime attribute: {datetime_attr}")
                if date_str: # Fallback to relative string if attribute parsing failed
                    parsed_date = parse_relative_date(date_str)
        elif date_str:
            parsed_date = parse_relative_date(date_str)
        else:
            parsed_date = datetime.datetime.now(pytz.utc) # Fallback if no date found

        # Basic filtering: Ensure we have a title and a non-placeholder link
        if title != "N/A" and link != "#" and not link.startswith(BASE_URL): # Avoid internal Google links
             news_items.append({
                'title': title,
                'link': link,
                'source': source,
                'date': parsed_date,
                'date_str': date_str or datetime_attr or "N/A" # Store original string for display
            })

    # Sort by date, newest first
    news_items.sort(key=lambda item: item['date'], reverse=True)

    print(f"Successfully parsed {len(news_items)} articles.")
    return news_items

def generate_html(news_items):
    """Generates the index.html file content."""
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>US Top Recent Real Estate News</title>
    <style>
        body {{ font-family: sans-serif; line-height: 1.6; margin: 20px; background-color: #f4f4f4; color: #333; }}
        .container {{ max-width: 800px; margin: auto; background: #fff; padding: 20px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; text-align: center; }}
        ul {{ list-style-type: none; padding: 0; }}
        li {{ background: #eee; margin-bottom: 10px; padding: 15px; border-radius: 5px; }}
        li a {{ text-decoration: none; color: #007bff; font-weight: bold; }}
        li a:hover {{ text-decoration: underline; }}
        .source, .date {{ font-size: 0.9em; color: #555; margin-top: 5px; }}
        .footer {{ text-align: center; margin-top: 20px; font-size: 0.8em; color: #777; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>US Top Recent Real Estate News</h1>
        <p class="footer">Last updated: {datetime.datetime.now(pytz.timezone(TIMEZONE)).strftime('%Y-%m-%d %H:%M:%S %Z')}</p>
        <ul>
"""
    if not news_items:
        html_content += "<li>No news found or error fetching data.</li>"
    else:
        for item in news_items:
            # Format date nicely if possible, otherwise use the string we found
            try:
                display_date = item['date'].astimezone(pytz.timezone(TIMEZONE)).strftime('%Y-%m-%d %H:%M')
            except Exception:
                display_date = item['date_str'] # Fallback to original string

            html_content += f"""
            <li>
                <a href="{item['link']}" target="_blank" rel="noopener noreferrer">{item['title']}</a>
                <div class="source">Source: {item['source']}</div>
                <div class="date">Published: {display_date}</div>
            </li>
"""

    html_content += """
        </ul>
        <p class="footer">Disclaimer: News aggregated via automated script. Accuracy and availability depend on source website structure.</p>
    </div>
</body>
</html>
"""
    return html_content

def write_output(html_content):
    """Writes the HTML content to the output file."""
    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"Successfully wrote news to {OUTPUT_FILE}")
    except IOError as e:
        print(f"Error writing to file {OUTPUT_FILE}: {e}")

# --- Execution ---
if __name__ == "__main__":
    print("Starting news scraping process...")
    html = fetch_news()
    if html:
        news = parse_news(html)
        output_html = generate_html(news)
        write_output(output_html)
    else:
        # Generate an error page if fetching failed
        output_html = generate_html([])
        write_output(output_html)
    print("Script finished.")
