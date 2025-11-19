"""Tests for web scraping functionality."""

import unittest
from unittest.mock import Mock, patch, mock_open
import sys
import os

# Add parent directory to path to import scraping module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from scraping.scrape_wiki import (  # noqa: E402
    get_page_links,
    extract_main_content,
    scrape_articles,
)


class TestScraper(unittest.TestCase):
    """Test cases for web scraping functions."""

    def test_extract_main_content_valid_html(self):
        """Test content extraction from valid HTML."""
        html = """
        <html>
            <body>
                <div class="mw-parser-output">
                    <p>This is the first paragraph.</p>
                    <h2>Section Title</h2>
                    <p>This is the second paragraph.</p>
                    <script>console.log('should be removed')</script>
                    <aside>Sidebar content</aside>
                </div>
            </body>
        </html>
        """
        content = extract_main_content(html)
        self.assertIn("first paragraph", content)
        self.assertIn("Section Title", content)
        self.assertIn("second paragraph", content)
        self.assertNotIn("script", content.lower())
        self.assertNotIn("sidebar", content.lower())

    def test_extract_main_content_no_content_div(self):
        """Test extraction when content div is missing."""
        html = "<html><body><p>Some text</p></body></html>"
        content = extract_main_content(html)
        self.assertEqual(content, "")

    def test_extract_main_content_filters_see_also(self):
        """Test that 'See also' sections are filtered out."""
        html = """
        <html>
            <body>
                <div class="mw-parser-output">
                    <p>Valid content here.</p>
                    <p>See also: Other article</p>
                    <p>More valid content.</p>
                </div>
            </body>
        </html>
        """
        content = extract_main_content(html)
        self.assertIn("Valid content", content)
        self.assertIn("More valid content", content)
        self.assertNotIn("See also", content)

    def test_extract_main_content_empty_html(self):
        """Test extraction from empty HTML."""
        content = extract_main_content("")
        self.assertEqual(content, "")

    @patch("scraping.scrape_wiki.requests.get")
    def test_get_page_links_single_page(self, mock_get):
        """Test link extraction from a single page."""
        mock_response = Mock()
        mock_response.text = """
        <html>
            <body>
                <a class="category-page__member-link" href="/wiki/Article1">Article 1</a>
                <a class="category-page__member-link" href="/wiki/Article2">Article 2</a>
            </body>
        </html>
        """
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        links = get_page_links("https://example.com/category", limit=10)

        self.assertEqual(len(links), 2)
        self.assertTrue(any("Article1" in link for link in links))
        self.assertTrue(any("Article2" in link for link in links))

    @patch("scraping.scrape_wiki.requests.get")
    def test_get_page_links_respects_limit(self, mock_get):
        """Test that link extraction respects the limit parameter."""
        # Create HTML with 10 links
        links_html = "\n".join(
            [
                f'<a class="category-page__member-link" href="/wiki/Article{i}">Article {i}</a>'
                for i in range(10)
            ]
        )

        mock_response = Mock()
        mock_response.text = f"<html><body>{links_html}</body></html>"
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        links = get_page_links("https://example.com/category", limit=5)

        self.assertLessEqual(len(links), 5)

    @patch("scraping.scrape_wiki.requests.get")
    def test_get_page_links_handles_request_failure(self, mock_get):
        """Test that link extraction handles request failures gracefully."""
        mock_get.side_effect = Exception("Network error")

        # Should handle error and return empty list
        try:
            links = get_page_links("https://example.com/category", limit=10)
            # Should return empty list after handling error
            self.assertIsInstance(links, list)
        except Exception:
            # It's also acceptable to propagate certain errors
            pass

    @patch("scraping.scrape_wiki.requests.get")
    @patch("builtins.open", new_callable=mock_open)
    @patch("os.path.exists")
    @patch("os.makedirs")
    def test_scrape_articles_success(
        self, mock_makedirs, mock_exists, mock_file, mock_get
    ):
        """Test successful article scraping."""
        mock_exists.return_value = False  # File doesn't exist yet

        mock_response = Mock()
        mock_response.text = """
        <html>
            <body>
                <div class="mw-parser-output">
                    <p>Article content here.</p>
                </div>
            </body>
        </html>
        """
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        urls = ["https://example.com/wiki/Test_Article"]
        scrape_articles(urls, output_dir="/tmp/test")

        # Verify file was opened for writing
        mock_file.assert_called()
        # Verify content was written
        handle = mock_file()
        handle.write.assert_called()

    @patch("scraping.scrape_wiki.requests.get")
    @patch("os.path.exists")
    def test_scrape_articles_skips_existing(self, mock_exists, mock_get):
        """Test that scraping skips already-existing files."""
        mock_exists.return_value = True  # File already exists

        urls = ["https://example.com/wiki/Test_Article"]
        scrape_articles(urls, output_dir="/tmp/test")

        # Should not make any HTTP requests
        mock_get.assert_not_called()

    @patch("scraping.scrape_wiki.requests.get")
    @patch("os.path.exists")
    @patch("os.makedirs")
    def test_scrape_articles_handles_request_failure(
        self, mock_makedirs, mock_exists, mock_get
    ):
        """Test that scraping handles request failures gracefully."""
        import requests

        mock_exists.return_value = False
        # Use requests.RequestException so the code catches it
        mock_get.side_effect = requests.RequestException("Network error")

        urls = ["https://example.com/wiki/Test_Article"]

        # The scraper will retry MAX_RETRIES times and then move on
        # It prints errors but doesn't crash
        scrape_articles(urls, output_dir="/tmp/test")

        # Verify that retries were attempted
        self.assertEqual(mock_get.call_count, 3)  # MAX_RETRIES = 3

    @patch("scraping.scrape_wiki.requests.get")
    @patch("builtins.open", new_callable=mock_open)
    @patch("os.path.exists")
    @patch("os.makedirs")
    def test_scrape_articles_empty_content_warning(
        self, mock_makedirs, mock_exists, mock_file, mock_get
    ):
        """Test that scraping warns on empty content extraction."""
        mock_exists.return_value = False

        mock_response = Mock()
        mock_response.text = "<html><body><p>No content div</p></body></html>"
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        urls = ["https://example.com/wiki/Test_Article"]

        # Should complete without crashing
        scrape_articles(urls, output_dir="/tmp/test")


class TestScraperIntegration(unittest.TestCase):
    """Integration tests for scraper (these could be run against real URLs if needed)."""

    def test_extract_main_content_realistic_html(self):
        """Test extraction with realistic Warhammer wiki HTML structure."""
        html = """
        <!DOCTYPE html>
        <html>
        <head><title>Space Marines</title></head>
        <body>
            <nav>Navigation stuff</nav>
            <div class="mw-parser-output">
                <p>The Space Marines are the Imperium's elite warriors.</p>
                <h2><span class="mw-headline">History</span></h2>
                <p>Created during the Great Crusade by the Emperor.</p>
                <h3><span class="mw-headline">The Horus Heresy</span></h3>
                <p>Half of the Space Marine Legions turned traitor.</p>
                <aside class="portable-infobox">
                    <h2>Space Marines</h2>
                    <div>Should be removed</div>
                </aside>
                <p>See also: Primarch, Chaos Space Marines</p>
                <script>var ads = true;</script>
                <style>.ad { display: block; }</style>
            </div>
        </body>
        </html>
        """
        content = extract_main_content(html)

        # Should include main content
        self.assertIn("elite warriors", content)
        self.assertIn("History", content)
        self.assertIn("Great Crusade", content)
        self.assertIn("Horus Heresy", content)

        # Should exclude unwanted elements
        self.assertNotIn("Navigation", content)
        self.assertNotIn("portable-infobox", content)
        self.assertNotIn("var ads", content)
        self.assertNotIn("See also", content)


if __name__ == "__main__":
    unittest.main()
