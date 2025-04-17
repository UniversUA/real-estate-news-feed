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
TEMPLATE_FILE = "template.html" # Input template file
OUTPUT_FILE = "index.html"      # Final output file
TIMEZONE = "America/New_York" # Timezone for relative dates like "2 hours ago"
NEWS_PLACEHOLDER = "<!-- NEWS_CONTENT_PLACEHOLDER -->" # Placeholder in template

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
    try:
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
    except (AttributeError, ValueError): # Handle cases where regex doesn't match or int conversion fails
        print(f"Warning: Could not parse relative date string: {date_str}")
    # Fallback or handle other formats if needed
    return now # Default to now if parsing fails

def get_absolute_url(href):
    """Converts relative URLs to absolute URLs based on Google News."""
    if href and href.startswith('./'):
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

        # Fallback if no date could be parsed at all
        if parsed_date is None:
             parsed_date = datetime.datetime.now(pytz.utc) # Use UTC for consistency if defaulting

        # Basic filtering: Ensure we have a title and a non-placeholder link
        # Also check if the source is not Google itself (sometimes happens)
        if title != "N/A" and link != "#" and not link.startswith(BASE_URL) and source != "Google News":
             news_items.append({
                'title': title,
                'link': link,
                'source': source,
                'date': parsed_date,
                'date_str': date_str or datetime_attr or "N/A" # Store original string for display
            })

    # Sort by date, newest first
    news_items.sort(key=lambda item: item['date'], reverse=True)

    print(f"Successfully parsed {len(news_items)} valid articles.")
    return news_items

def generate_news_list_html(news_items):
    """Generates the HTML list (ul) for the news items."""
    if not news_items:
        return "<ul><li>No news found or error fetching data. Check Action logs for details.</li></ul>"

    list_items_html = ""
    for item in news_items:
        # Format date nicely if possible, otherwise use the string we found
        try:
            # Using a simpler format suitable for a list
            display_date = item['date'].astimezone(pytz.timezone(TIMEZONE)).strftime('%b %d, %H:%M %Z')
        except Exception as e:
            print(f"Warning: Could not format date {item['date']}: {e}")
            display_date = item['date_str'] # Fallback to original string

        # Using basic list item structure, assuming styling comes from template.html
        # Escape title and source just in case they contain HTML characters
        escaped_title = requests.utils.escape(item['title'])
        escaped_source = requests.utils.escape(item['source'])
        list_items_html += f"""
        <li>
            <a href="{item['link']}" target="_blank" rel="noopener noreferrer">{escaped_title}</a>
            <div style="font-size: 0.9em; color: #555;">
                Source: {escaped_source} | Published: {display_date}
            </div>
        </li>
"""

    # Wrap the list items in a <ul> tag
    # Add a timestamp comment for debugging/verification
    timestamp = datetime.datetime.now(pytz.timezone(TIMEZONE)).strftime('%Y-%m-%d %H:%M:%S %Z')
    full_list_html = f"""
<!-- News list generated at {timestamp} -->
<ul class="news-list"> <!-- Add a class for potential styling -->
{list_items_html}
</ul>
<!-- End of generated news list -->
"""
    return full_list_html

# --- Fallback write function (only used if template reading fails) ---
def write_output_fallback(html_content):
    """Writes basic HTML content to the output file (used for fallback errors)."""
    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"Successfully wrote basic fallback output to {OUTPUT_FILE}")
    except IOError as e:
        print(f"Error writing basic fallback output to file {OUTPUT_FILE}: {e}")

# --- Main function to handle template processing ---
def write_final_html(news_list_html):
    """Reads the template, injects the news list, and writes to the output file."""
    try:
        with open(TEMPLATE_FILE, 'r', encoding='utf-8') as f:
            template_content = f.read()
    except IOError as e:
        print(f"Error reading template file {TEMPLATE_FILE}: {e}")
        # Fallback: generate a basic error page if template is missing
        error_html = f"<html><head><title>Error</title></head><body><h1>Error</h1><p>Could not read template file: {TEMPLATE_FILE}</p><h2>Generated News Content:</h2>{news_list_html}</body></html>"
        write_output_fallback(error_html) # Use the fallback write function
        return False # Indicate failure

    if NEWS_PLACEHOLDER not in template_content:
        print(f"Error: Placeholder '{NEWS_PLACEHOLDER}' not found in {TEMPLATE_FILE}.")
        # Fallback: Append news to the end if placeholder is missing, but log error
        final_html = template_content + "\n<hr><h2>Appended News (Placeholder Missing):</h2>\n" + news_list_html
    else:
        final_html = template_content.replace(NEWS_PLACEHOLDER, news_list_html)

    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.write(final_html)
        print(f"Successfully wrote final HTML to {OUTPUT_FILE}")
        return True # Indicate success
    except IOError as e:
        print(f"Error writing final HTML to {OUTPUT_FILE}: {e}")
        return False # Indicate failure

# --- Execution ---
if __name__ == "__main__":
    print(f"--- Starting news scraping process at {datetime.datetime.now()} ---")
    html_content = fetch_news()
    news_items = [] # Initialize empty list
    if html_content:
        news_items = parse_news(html_content)
    else:
        print("Fetching news failed. Proceeding with empty news list.")

    # Generate only the news list HTML
    news_list_html_content = generate_news_list_html(news_items)

    # Inject the list into the template and write the final index.html
    success = write_final_html(news_list_html_content)

    if success:
        print(f"--- Script finished successfully at {datetime.datetime.now()} ---")
    else:
        print(f"--- Script finished with errors at {datetime.datetime.now()} ---")
