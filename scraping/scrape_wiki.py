"""Web scraper for extracting Warhammer 40K lore from the Fandom wiki."""

from typing import List, Set, Optional
import requests
from bs4 import BeautifulSoup
from time import sleep
import os
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "https://warhammer40k.fandom.com"
HEADERS = {"User-Agent": "Mozilla/5.0"}
DATA_DIR = Path(__file__).parent.parent / "data" / "raw"
REQUEST_TIMEOUT = 30  # seconds
MAX_RETRIES = 3

os.makedirs(DATA_DIR, exist_ok=True)


def get_page_links(category_url: str, limit: int = 50) -> List[str]:
    """
    Crawl a category page and extract article links with pagination.

    Args:
        category_url: URL of the category page to crawl
        limit: Maximum number of links to extract

    Returns:
        List of article URLs

    Raises:
        requests.RequestException: If HTTP request fails
    """
    links: Set[str] = set()
    next_page: Optional[str] = category_url

    while next_page and len(links) < limit:
        logger.info(f"Crawling: {next_page}")

        try:
            response = requests.get(next_page, headers=HEADERS, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"Failed to fetch {next_page}: {e}")
            break

        soup = BeautifulSoup(response.text, "html.parser")

        # Extract article links
        for a in soup.select(".category-page__member-link"):
            href = a.get("href")
            if href:
                links.add(BASE_URL + href)

        # Handle pagination
        next_button = soup.select_one(".category-page__pagination-next")
        next_page = BASE_URL + next_button.get("href") if next_button else None
        sleep(1)  # Rate limiting

    return list(links)[:limit]


def extract_main_content(html: str) -> str:
    """
    Extract main text content from a wiki article HTML.

    Args:
        html: Raw HTML string of the article

    Returns:
        Cleaned text content with paragraphs and headings
    """
    soup = BeautifulSoup(html, "html.parser")

    # Remove unwanted sections
    for tag in soup(["script", "style", "aside", "nav"]):
        tag.decompose()

    content_div = soup.find("div", {"class": "mw-parser-output"})
    if not content_div:
        return ""

    paragraphs: List[str] = []
    for elem in content_div.find_all(["p", "h2", "h3"]):
        text = elem.get_text(separator=" ", strip=True)
        if text and not text.lower().startswith("see also"):
            paragraphs.append(text)

    clean_text = "\n".join(paragraphs)
    return clean_text


def scrape_articles(links: List[str], output_dir: Path = DATA_DIR) -> None:
    """
    Scrape articles from the given URLs and save to text files.

    Args:
        links: List of article URLs to scrape
        output_dir: Directory to save scraped content

    Raises:
        OSError: If file writing fails
    """
    os.makedirs(output_dir, exist_ok=True)

    logger.info(f"Scraping {len(links)} articles...")
    for idx, url in enumerate(links, 1):
        title = url.split("/")[-1]
        path = os.path.join(output_dir, f"{title}.txt")

        # Skip if already scraped
        if os.path.exists(path):
            continue

        retries = 0
        while retries < MAX_RETRIES:
            try:
                response = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
                response.raise_for_status()

                content = extract_main_content(response.text)

                if content:
                    with open(path, "w", encoding="utf-8") as f:
                        f.write(content)
                    logger.info(f"[{idx}/{len(links)}] Scraped: {title}")
                else:
                    logger.warning(f"No content extracted from {url}")

                sleep(1)  # Rate limiting
                break  # Success, exit retry loop

            except requests.RequestException as e:
                retries += 1
                logger.error(f"Failed to scrape {url} (attempt {retries}/{MAX_RETRIES}): {e}")
                if retries < MAX_RETRIES:
                    sleep(2**retries)  # Exponential backoff
            except OSError as e:
                logger.error(f"Failed to write {path}: {e}")
                break


if __name__ == "__main__":
    logger.info("Starting Warhammer 40K lore scraping...")

    # Scrape multiple categories for comprehensive lore coverage
    categories = [
        ("Factions", 30),
        ("Characters", 20),
        ("Planets", 15),
        ("Space_Marine_Chapters", 20),
        ("Chaos_Space_Marine_Legions", 10),
        ("Xenos", 15),
    ]

    all_links = []
    for category, limit in categories:
        logger.info(f"Fetching links from Category:{category}...")
        category_url = f"{BASE_URL}/wiki/Category:{category}"
        try:
            links = get_page_links(category_url, limit=limit)
            all_links.extend(links)
            logger.info(f"Found {len(links)} articles in {category}")
        except Exception as e:
            logger.error(f"Failed to get links from {category}: {e}")

    # Remove duplicates
    all_links = list(set(all_links))
    logger.info(f"Total unique articles to scrape: {len(all_links)}")

    scrape_articles(all_links)
    logger.info("Lore scraping complete!")
