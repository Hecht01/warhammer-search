"""Scrape Warhammer 40K books from Black Library and Lexicanum."""

import json
import logging
from pathlib import Path
import requests
from bs4 import BeautifulSoup
from typing import List, Dict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def scrape_lexicanum_books() -> List[Dict]:
    """Scrape book data from Lexicanum."""
    books = []

    # Lexicanum novel list pages
    urls = [
        "https://wh40k.lexicanum.com/wiki/List_of_Novels",
        "https://wh40k.lexicanum.com/wiki/List_of_Horus_Heresy_Novels_and_Novellas",
    ]

    for url in urls:
        try:
            logger.info(f"Scraping {url}")
            response = requests.get(url, timeout=10)
            if response.status_code != 200:
                logger.warning(f"Failed to fetch {url}: {response.status_code}")
                continue

            soup = BeautifulSoup(response.content, "html.parser")

            # Find tables with book information
            tables = soup.find_all("table", class_="wikitable")

            for table in tables:
                rows = table.find_all("tr")[1:]  # Skip header

                for row in rows:
                    cols = row.find_all("td")
                    if len(cols) < 2:
                        continue

                    # Extract book data
                    title_cell = cols[0]
                    title = title_cell.get_text(strip=True)

                    # Try to get author
                    author = "Unknown"
                    if len(cols) > 1:
                        author = cols[1].get_text(strip=True)

                    # Determine era and factions from title/context
                    era = "40K"
                    if "Horus Heresy" in url or "heresy" in title.lower():
                        era = "30K"

                    factions = extract_factions_from_text(title)

                    # Estimate page count (typical Black Library novel)
                    page_count = 384

                    books.append(
                        {
                            "title": title,
                            "author": author,
                            "series": None,
                            "factions": factions if factions else ["Imperium"],
                            "era": era,
                            "synopsis": f"A Warhammer 40,000 novel by {author}.",
                            "page_count": page_count,
                        }
                    )

        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            continue

    return books


def extract_factions_from_text(text: str) -> List[str]:
    """Extract faction names from text."""
    faction_keywords = {
        "Space Marines": ["space marine", "adeptus astartes", "astartes"],
        "Chaos": ["chaos"],
        "Necrons": ["necron"],
        "Orks": ["ork", "greenskin"],
        "Tyranids": ["tyranid", "hive fleet"],
        "Aeldari": ["eldar", "aeldari", "craftworld"],
        "T'au Empire": ["tau", "t'au"],
        "Astra Militarum": ["imperial guard", "astra militarum"],
        "Adeptus Mechanicus": ["mechanicus", "adeptus mechanicus"],
    }

    text_lower = text.lower()
    factions = []

    for faction, keywords in faction_keywords.items():
        if any(keyword in text_lower for keyword in keywords):
            factions.append(faction)

    return factions


def scrape_black_library_series() -> List[Dict]:
    """Get information about major Black Library series."""
    series_info = [
        {
            "name": "The Horus Heresy",
            "era": "30K",
            "factions": ["Space Marines", "Chaos", "Imperium"],
            "book_count": 54,
        },
        {
            "name": "Gaunt's Ghosts",
            "era": "40K",
            "factions": ["Astra Militarum", "Imperium"],
            "book_count": 15,
        },
        {"name": "Eisenhorn", "era": "40K", "factions": ["Imperium"], "book_count": 3},
        {
            "name": "Dawn of Fire",
            "era": "41K",
            "factions": ["Space Marines", "Imperium"],
            "book_count": 6,
        },
    ]

    return series_info


def save_books(books: List[Dict], output_file: Path):
    """Save scraped books to JSON file."""
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(books, f, indent=2, ensure_ascii=False)

    logger.info(f"Saved {len(books)} books to {output_file}")


def main():
    """Main scraping function."""
    logger.info("Starting book scraping...")

    books = []

    # Scrape from Lexicanum
    lexicanum_books = scrape_lexicanum_books()
    books.extend(lexicanum_books)

    # Deduplicate by title
    seen_titles = set()
    unique_books = []
    for book in books:
        if book["title"] not in seen_titles:
            seen_titles.add(book["title"])
            unique_books.append(book)

    # Save to file
    output_file = Path(__file__).parent.parent / "data" / "books.json"
    save_books(unique_books, output_file)

    logger.info(f"Book scraping complete! Collected {len(unique_books)} unique books.")


if __name__ == "__main__":
    main()
