# ⚔️ Warhammer 40K Semantic Search Engine

Semantic search over the Warhammer 40K universe using Qdrant and Sentence Transformers. Features a dark-themed web UI and comprehensive books database organized by faction.

## ✨ Features

### 🔍 Semantic Lore Search
- Scrapes Warhammer 40K wiki articles (23 factions included)
- Intelligent text chunking with sentence boundary detection
- Embeddings via Sentence Transformers (all-MiniLM-L6-v2)
- Stores embeddings in Qdrant vector database
- Semantic search API with similarity scoring
- Result highlighting and relevance scores

### 📚 Books Database
- **40 curated Warhammer 40K books** with detailed metadata
- Filter by **faction** (Space Marines, Chaos, Necrons, etc.)
- Filter by **era** (30K Horus Heresy, 40K, 41K Era Indomitus)
- Search by title, author, or series
- Includes popular series:
  - Horus Heresy
  - Gaunt's Ghosts
  - Eisenhorn
  - Black Legion
  - Ciaphas Cain
  - And many more!

### 🎨 Web Interface
- **Dark Warhammer 40K themed UI** with gold accents
- Tabbed interface for Lore Search and Books
- Real-time search with query highlighting
- Responsive design (mobile & desktop)
- Loading states and error handling

## 🚀 Quick Start

### Using Docker Compose (Recommended)

```bash
# Start all services
docker-compose up -d

# Access the web UI
open http://localhost:8000
```

The web interface will be available at `http://localhost:8000` with both lore search and books browsing.

### Manual Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Start Qdrant (in separate terminal)
docker run -p 6333:6333 qdrant/qdrant

# Index the data (first time only)
python -m indexing.embed
python -m indexing.qdrant_loader

# Start the API server
uvicorn api.search:app --reload

# Access the web UI
open http://localhost:8000
```

## 📡 API Endpoints

### Lore Search
```bash
GET /search?q=Emperor&limit=10
```

Returns semantic search results from the lore database.

**Parameters:**
- `q` (required): Search query
- `limit` (optional): Number of results (default: 5, max: 100)

**Response:**
```json
[
  {
    "text": "The Emperor of Mankind is the immortal...",
    "score": 0.89
  }
]
```

### Books
```bash
GET /books?faction=Space%20Marines&era=40K
```

Returns books filtered by criteria.

**Parameters:**
- `q` (optional): Search by title, author, or series
- `faction` (optional): Filter by faction
- `era` (optional): Filter by era (30K, 40K, 41K)

**Response:**
```json
[
  {
    "title": "Dante",
    "author": "Guy Haley",
    "series": null,
    "factions": ["Space Marines"],
    "era": "40K",
    "synopsis": "The story of Commander Dante..."
  }
]
```

### Health Check
```bash
GET /health
```

Returns API and Qdrant connection status.

## 🛠️ Architecture

```
Web Scraper → Text Chunking → Embeddings → Qdrant → FastAPI → Web UI
```

- **Scraping**: BeautifulSoup4 extracts text from Warhammer 40K Fandom Wiki
- **Chunking**: 500-character chunks with 50-char overlap, sentence-aware
- **Embeddings**: all-MiniLM-L6-v2 (384-dimensional vectors)
- **Vector DB**: Qdrant for similarity search
- **API**: FastAPI with Pydantic models
- **Frontend**: Vanilla JavaScript with dark theme

## 📊 Data Included

### Factions (23 total)
Space Marines, Chaos, Necrons, Orks, Tyranids, Aeldari, T'au Empire, Imperium, Astra Militarum, Adeptus Mechanicus, and more!

### Books (40 total)
Organized across popular series and standalone novels from authors like Dan Abnett, Graham McNeill, Aaron Dembski-Bowden, and more.

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_api.py -v
```

## 🏗️ Future Features
- ✅ ~~Find 40k Books for your favorite factions~~ **DONE!**
- ✅ ~~Web UI~~ **DONE!**
- Search for Warhammer 40K Rules (datasheets, core rules)
- Find Stratagems quickly by faction
- Multi-modal search (image → lore)
- Q&A system with citations
- Timeline visualization

## 🤝 Contributing

Contributions welcome! Areas to expand:
- Add more books to the database
- Scrape additional content sources
- Implement rules/stratagems database
- Improve UI/UX

## 📝 License

This is a fan project for educational and community purposes. All Warhammer 40,000 content is owned by Games Workshop.
