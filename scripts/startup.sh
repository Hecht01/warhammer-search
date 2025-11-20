#!/bin/bash
set -e

echo "========================================="
echo "Warhammer 40K Search Engine - Starting Up"
echo "========================================="

# Run scrapers if data doesn't exist or force refresh
FORCE_SCRAPE=${FORCE_SCRAPE:-false}

if [ "$FORCE_SCRAPE" = "true" ] || [ ! -f "/app/data/books.json" ]; then
    echo "📚 Scraping books data..."
    python -m scraping.scrape_books || echo "⚠️  Books scraping failed, continuing..."
else
    echo "✓ Books data already exists, skipping scrape"
fi

if [ "$FORCE_SCRAPE" = "true" ] || [ ! -f "/app/data/rules.json" ]; then
    echo "📋 Scraping rules and stratagems..."
    python -m scraping.scrape_rules || echo "⚠️  Rules scraping failed, continuing..."
else
    echo "✓ Rules data already exists, skipping scrape"
fi

# Always scrape lore (it's quick and important)
if [ -d "/app/data/raw" ]; then
    echo "📖 Lore files found in /app/data/raw"
else
    echo "⚠️  No lore files found. Run scraping/scrape_wiki.py manually if needed."
fi

echo "========================================="
echo "🚀 Starting FastAPI server..."
echo "========================================="

# Start the FastAPI application
exec uvicorn api.search:app --host 0.0.0.0 --port 8000
