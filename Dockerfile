FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy code
COPY ./api ./api
COPY ./indexing ./indexing
COPY ./scraping ./scraping
COPY ./scripts ./scripts
COPY ./static ./static

# Create data directories for scrapers to write to
RUN mkdir -p /app/data/raw

# Create startup script inline to avoid line ending issues
RUN echo '#!/bin/bash\n\
set -e\n\
echo "========================================="\n\
echo "Warhammer 40K Search Engine - Starting Up"\n\
echo "========================================="\n\
FORCE_SCRAPE=${FORCE_SCRAPE:-false}\n\
if [ "$FORCE_SCRAPE" = "true" ] || [ ! -f "/app/data/books.json" ]; then\n\
  echo "📚 Scraping books data..."\n\
  python -m scraping.scrape_books || echo "⚠️  Books scraping failed, continuing..."\n\
else\n\
  echo "✓ Books data already exists, skipping scrape"\n\
fi\n\
if [ "$FORCE_SCRAPE" = "true" ] || [ ! -f "/app/data/rules.json" ]; then\n\
  echo "📋 Scraping rules and stratagems..."\n\
  python -m scraping.scrape_rules || echo "⚠️  Rules scraping failed, continuing..."\n\
else\n\
  echo "✓ Rules data already exists, skipping scrape"\n\
fi\n\
LORE_FILE_COUNT=$(find /app/data/raw -name "*.txt" 2>/dev/null | wc -l)\n\
if [ "$FORCE_SCRAPE" = "true" ] || [ "$LORE_FILE_COUNT" -lt 10 ]; then\n\
  echo "📖 Scraping lore from Warhammer 40K wiki..."\n\
  python -m scraping.scrape_wiki || echo "⚠️  Lore scraping failed, continuing..."\n\
else\n\
  echo "✓ Lore data already exists ($LORE_FILE_COUNT files), skipping scrape"\n\
fi\n\
echo "========================================="\n\
echo "🚀 Starting FastAPI server..."\n\
echo "========================================="\n\
exec uvicorn api.search:app --host 0.0.0.0 --port 8000\n\
' > /app/startup.sh && chmod +x /app/startup.sh

# Expose port
EXPOSE 8000

# Run startup script (scrapes data, then starts API)
CMD ["/bin/bash", "/app/startup.sh"]
