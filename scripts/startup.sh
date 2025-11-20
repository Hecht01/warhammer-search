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

# Scrape lore from Warhammer 40K wiki
LORE_FILE_COUNT=$(find /app/data/raw -name "*.txt" 2>/dev/null | wc -l)
if [ "$FORCE_SCRAPE" = "true" ] || [ "$LORE_FILE_COUNT" -lt 10 ]; then
    echo "📖 Scraping lore from Warhammer 40K wiki..."
    python -m scraping.scrape_wiki || echo "⚠️  Lore scraping failed, continuing..."
else
    echo "✓ Lore data already exists ($LORE_FILE_COUNT files), skipping scrape"
fi

echo "========================================="
echo "🚀 Starting FastAPI server..."
echo "========================================="

# Start the FastAPI application
exec uvicorn api.search:app --host 0.0.0.0 --port 8000
