# ⚔️ Warhammer 40K Semantic Search Engine

Comprehensive search and reference tool for Warhammer 40,000 with semantic lore search, books database, game rules, stratagems, and faction-organized navigation.

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

### 📋 Rules & Stratagems
- **24 game rules** (12 core + 12 faction-specific)
- **28 stratagems** across 8 factions
- Filter by faction, phase, category, type, and CP cost
- Search by keyword across rule descriptions
- Quick reference for gameplay
- Includes:
  - Core Rules (Movement, Shooting, Charging, etc.)
  - Faction Rules (Oath of Moment, Reanimation Protocols, Waaagh!, etc.)
  - Stratagems organized by faction with full details

### 🎯 Faction Navigation
- **Interactive faction cards** with icons
- Browse all content organized by faction
- See counts of books, rules, and stratagems per faction
- Click any faction to view filtered content
- 13 factions covered:
  - Space Marines, Chaos, Necrons, Orks, Tyranids
  - Aeldari, T'au Empire, Astra Militarum
  - And more!

### 🎨 Web Interface
- **Dark Warhammer 40K themed UI** with gold accents
- 4 tabs: Lore Search, Books, Rules & Stratagems, Factions
- Real-time search with query highlighting
- Responsive design (mobile & desktop)
- Loading states and error handling
- Dual-panel layout for rules and stratagems

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

### Rules
```bash
GET /rules?faction=Space%20Marines&phase=Command
```

Returns game rules filtered by criteria.

**Parameters:**
- `q` (optional): Search by rule name or description
- `faction` (optional): Filter by faction (omit for core rules)
- `category` (optional): Filter by category (Core Rules, Faction)
- `phase` (optional): Filter by phase (Command, Movement, Shooting, etc.)

**Response:**
```json
[
  {
    "name": "Oath of Moment",
    "category": "Faction",
    "faction": "Space Marines",
    "description": "At start of your Command phase, select one enemy unit...",
    "phase": "Command"
  }
]
```

### Stratagems
```bash
GET /stratagems?faction=Necrons&max_cost=2
```

Returns stratagems filtered by criteria.

**Parameters:**
- `q` (optional): Search by stratagem name or effect
- `faction` (optional): Filter by faction
- `type` (optional): Filter by type (Battle Tactic, Strategic Ploy, etc.)
- `phase` (optional): Filter by phase
- `max_cost` (optional): Maximum CP cost

**Response:**
```json
[
  {
    "name": "Resurrection Protocols",
    "faction": "Necrons",
    "cost": 1,
    "type": "Epic Deed",
    "when": "End of your Command phase",
    "target": "One Necrons unit from your army",
    "effect": "Return D3 destroyed models to that unit...",
    "phase": "Command"
  }
]
```

### Factions
```bash
GET /factions
```

Returns list of all available factions.

**Response:**
```json
["Aeldari", "Astra Militarum", "Chaos", "Chaos Space Marines", "Necrons", ...]
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

### Factions (13 unique)
Space Marines, Chaos, Chaos Space Marines, Necrons, Orks, Tyranids, Aeldari, T'au Empire, Astra Militarum, Adeptus Mechanicus, Imperium, Genestealer Cults, Drukhari

### Lore Articles (23 factions)
Full wiki articles for Space Marines, Chaos, Necrons, Orks, Tyranids, Aeldari, T'au Empire, Imperium, Astra Militarum, Adeptus Mechanicus, and more!

### Books (40 total)
Organized across popular series and standalone novels from authors like Dan Abnett, Graham McNeill, Aaron Dembski-Bowden, and more.

### Game Rules (24 total)
- **12 Core Rules**: Movement, Shooting, Charging, Cover, Invulnerable Saves, etc.
- **12 Faction Rules**: Oath of Moment, Reanimation Protocols, Waaagh!, Synapse, For the Greater Good, etc.

### Stratagems (28 total)
- Space Marines: 4 stratagems
- Chaos Space Marines: 3 stratagems
- Necrons: 4 stratagems
- Orks: 4 stratagems
- Tyranids: 3 stratagems
- Aeldari: 3 stratagems
- T'au Empire: 3 stratagems
- Astra Militarum: 3 stratagems

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
- ✅ ~~Search for Warhammer 40K Rules~~ **DONE!**
- ✅ ~~Find Stratagems quickly by faction~~ **DONE!**
- ✅ ~~Faction-organized navigation~~ **DONE!**
- Add unit datasheets database
- Expand rules to include weapon profiles
- Multi-modal search (image → lore)
- Q&A system with citations using RAG
- Timeline visualization with M30-M42 events
- Army list builder integration
- Paint scheme recommendations by faction

## 🤝 Contributing

Contributions welcome! Areas to expand:
- Add more books to the database
- Expand rules and stratagems coverage
- Add unit datasheets and weapon profiles
- Scrape additional content sources (Lexicanum, 1d4chan)
- Improve UI/UX and mobile experience
- Add user authentication for saved searches

## 📝 License

This is a fan project for educational and community purposes. All Warhammer 40,000 content is owned by Games Workshop.
