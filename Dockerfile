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

# Make startup script executable
RUN chmod +x ./scripts/startup.sh

# Expose port
EXPOSE 8000

# Run startup script (scrapes data, then starts API)
CMD ["./scripts/startup.sh"]
