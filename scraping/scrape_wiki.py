import requests
from bs4 import BeautifulSoup
from time import sleep
from tqdm import tqdm
import os
import re

BASE_URL = "https://warhammer40k.fandom.com"
HEADERS = {"User-Agent": "Mozilla/5.0"}
DATA_DIR = "../data/raw"

os.makedirs(DATA_DIR, exist_ok=True)


def get_page_links(category_url: str, limit: int = 50):
    """
    Crawl a category page and extract article links.
    """
    links = set()
    next_page = category_url

    while next_page and len(links) < limit:
        print(f"Crawling: {next_page}")
        response = requests.get(next_page, headers=HEADERS)
        soup = BeautifulSoup(response.text, "html.parser")

        for a in soup.select(".category-page__member-link"):
            href = a.get("href")
            if href:
                links.add(BASE_URL + href)

        # Pagination
        next_button = soup.select_one(".category-page__pagination-next")
        next_page = BASE_URL + next_button.get("href") if next_button else None
        sleep(1)

    return list(links)[:limit]


def extract_main_content(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")

    # Remove unwanted sections
    for tag in soup(["script", "style", "aside", "nav"]):
        tag.decompose()

    content_div = soup.find("div", {"class": "mw-parser-output"})
    if not content_div:
        return ""

    paragraphs = []
    for elem in content_div.find_all(["p", "h2", "h3"]):
        text = elem.get_text(separator=" ", strip=True)
        if text and not text.lower().startswith("see also"):
            paragraphs.append(text)

    clean_text = "\n".join(paragraphs)
    return clean_text


def scrape_articles(links: list[str]):
    for url in tqdm(links, desc="Scraping articles"):
        title = url.split("/")[-1]
        path = os.path.join(DATA_DIR, f"{title}.txt")

        if os.path.exists(path):
            continue

        try:
            response = requests.get(url, headers=HEADERS)
            content = extract_main_content(response.text)

            with open(path, "w", encoding="utf-8") as f:
                f.write(content)

            sleep(1)
        except Exception as e:
            print(f"Failed to scrape {url}: {e}")


if __name__ == "__main__":
    #For the MVP we only scrape the basic lore about each faction
    category_url = f"{BASE_URL}/wiki/Category:Factions"
    article_links = get_page_links(category_url, limit=50)

    scrape_articles(article_links)
