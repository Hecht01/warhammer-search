"""FastAPI application for semantic search of Warhammer 40K lore."""

import os
import time
import logging
import json
from pathlib import Path
from typing import List, Optional
from fastapi import FastAPI, Query, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Warhammer 40K Search API",
    description="Semantic search engine for Warhammer 40K lore and content",
    version="1.0.0",
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Configuration from environment variables with defaults
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "warhammer40kLore")
MODEL_NAME = os.getenv("MODEL_NAME", "all-MiniLM-L6-v2")

# Initialize clients
try:
    client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    model = SentenceTransformer(MODEL_NAME)
except Exception as e:
    raise RuntimeError(f"Failed to initialize API components: {e}") from e


@app.on_event("startup")
async def startup_event():
    """Initialize lore data on startup if Qdrant is empty."""
    logger.info("Starting up Warhammer 40K Search API...")

    # Wait for Qdrant to be ready
    max_retries = 30
    for i in range(max_retries):
        try:
            client.get_collections()
            logger.info("Successfully connected to Qdrant")
            break
        except Exception as e:
            if i < max_retries - 1:
                logger.info(f"Waiting for Qdrant... (attempt {i+1}/{max_retries})")
                time.sleep(2)
            else:
                logger.error(
                    f"Failed to connect to Qdrant after {max_retries} attempts"
                )
                raise e

    # Initialize lore data if needed
    try:
        from indexing.init_data import init_lore_data

        init_lore_data(
            host=QDRANT_HOST, port=QDRANT_PORT, collection_name=COLLECTION_NAME
        )
    except Exception as e:
        logger.error(f"Failed to initialize lore data: {e}")
        # Don't crash the API if initialization fails
        logger.warning("API will start but search may not work until data is loaded")


class SearchResponse(BaseModel):
    """Response model for search results."""

    text: str
    score: float


class Book(BaseModel):
    """Model for a Warhammer 40K book."""

    title: str
    author: str
    series: Optional[str] = None
    factions: List[str]
    era: Optional[str] = None
    synopsis: Optional[str] = None
    page_count: Optional[int] = None


class Rule(BaseModel):
    """Model for a Warhammer 40K game rule."""

    name: str
    category: str  # "Core Rules", "Movement", "Shooting", "Melee", "Faction"
    faction: Optional[str] = None  # None for core rules
    description: str
    phase: Optional[str] = (
        None  # "Command", "Movement", "Shooting", "Charge", "Fight", "Morale"
    )


class Stratagem(BaseModel):
    """Model for a Warhammer 40K stratagem."""

    name: str
    faction: str
    cost: int  # CP cost
    type: str  # "Battle Tactic", "Strategic Ploy", "Epic Deed", "Wargear"
    when: str  # When this stratagem is used
    target: str  # What units this affects
    effect: str  # What it does
    phase: Optional[str] = None


@app.get("/search", response_model=List[SearchResponse])
def search(
    q: str = Query(..., min_length=1, description="Your question or query"),
    limit: int = Query(5, ge=1, le=100, description="Number of results to return"),
) -> List[SearchResponse]:
    """
    Perform semantic search on Warhammer 40K lore.

    Args:
        q: Search query string
        limit: Maximum number of results to return (1-100)

    Returns:
        List of search results with text and similarity scores

    Raises:
        HTTPException: If the search fails
    """
    try:
        # Encode the query
        query_vector = model.encode(q).tolist()

        # Search in Qdrant
        hits = client.search(
            collection_name=COLLECTION_NAME, query_vector=query_vector, limit=limit
        )

        return [
            SearchResponse(text=hit.payload["text"], score=hit.score) for hit in hits
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@app.get("/health")
def health_check() -> dict:
    """Health check endpoint."""
    try:
        # Verify Qdrant connection
        client.get_collections()
        return {
            "status": "healthy",
            "qdrant_host": QDRANT_HOST,
            "qdrant_port": QDRANT_PORT,
            "collection": COLLECTION_NAME,
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


# Data loading functions
def load_books_from_json() -> List[Book]:
    """Load books from JSON file or return empty list."""
    books_file = Path(__file__).parent.parent / "data" / "books.json"
    if not books_file.exists():
        logger.warning(f"Books file not found: {books_file}")
        return []

    try:
        with open(books_file, "r", encoding="utf-8") as f:
            books_data = json.load(f)
        return [Book(**book) for book in books_data]
    except Exception as e:
        logger.error(f"Error loading books: {e}")
        return []


def load_rules_from_json() -> List[Rule]:
    """Load rules from JSON file or return empty list."""
    rules_file = Path(__file__).parent.parent / "data" / "rules.json"
    if not rules_file.exists():
        logger.warning(f"Rules file not found: {rules_file}")
        return []

    try:
        with open(rules_file, "r", encoding="utf-8") as f:
            rules_data = json.load(f)
        return [Rule(**rule) for rule in rules_data]
    except Exception as e:
        logger.error(f"Error loading rules: {e}")
        return []


def load_stratagems_from_json() -> List[Stratagem]:
    """Load stratagems from JSON file or return empty list."""
    stratagems_file = Path(__file__).parent.parent / "data" / "stratagems.json"
    if not stratagems_file.exists():
        logger.warning(f"Stratagems file not found: {stratagems_file}")
        return []

    try:
        with open(stratagems_file, "r", encoding="utf-8") as f:
            stratagems_data = json.load(f)
        return [Stratagem(**strat) for strat in stratagems_data]
    except Exception as e:
        logger.error(f"Error loading stratagems: {e}")
        return []


# Load data from JSON files (populated by scrapers on startup)
BOOKS_DATABASE: List[Book] = load_books_from_json()
logger.info(f"Loaded {len(BOOKS_DATABASE)} books from data files")

RULES_DATABASE: List[Rule] = load_rules_from_json()
logger.info(f"Loaded {len(RULES_DATABASE)} rules from data files")

STRATAGEMS_DATABASE: List[Stratagem] = load_stratagems_from_json()
logger.info(f"Loaded {len(STRATAGEMS_DATABASE)} stratagems from data files")


@app.get("/", include_in_schema=False)
async def root():
    """Serve the web UI."""
    return FileResponse("static/index.html")


@app.get("/books", response_model=List[Book])
def get_books(
    q: Optional[str] = Query(
        None, description="Search query for title, author, or series"
    ),
    faction: Optional[str] = Query(None, description="Filter by faction"),
    era: Optional[str] = Query(None, description="Filter by era (30K, 40K, 41K)"),
) -> List[Book]:
    """
    Get Warhammer 40K books with optional filtering.

    Args:
        q: Search query for title, author, or series
        faction: Filter by faction name
        era: Filter by era (30K, 40K, 41K)

    Returns:
        List of books matching the criteria
    """
    results = BOOKS_DATABASE.copy()

    # Filter by search query
    if q:
        q_lower = q.lower()
        results = [
            book
            for book in results
            if q_lower in book.title.lower()
            or q_lower in book.author.lower()
            or (book.series and q_lower in book.series.lower())
        ]

    # Filter by faction
    if faction:
        results = [book for book in results if faction in book.factions]

    # Filter by era
    if era:
        results = [book for book in results if book.era == era]

    return results


@app.get("/rules", response_model=List[Rule])
def get_rules(
    q: Optional[str] = Query(
        None, description="Search query for rule name or description"
    ),
    faction: Optional[str] = Query(
        None, description="Filter by faction (empty for core rules)"
    ),
    category: Optional[str] = Query(None, description="Filter by category"),
    phase: Optional[str] = Query(None, description="Filter by phase"),
) -> List[Rule]:
    """
    Get Warhammer 40K rules with optional filtering.

    Args:
        q: Search query for rule name or description
        faction: Filter by faction name (None for core rules)
        category: Filter by category (Core Rules, Movement, Shooting, etc.)
        phase: Filter by phase (Command, Movement, Shooting, etc.)

    Returns:
        List of rules matching the criteria
    """
    results = RULES_DATABASE.copy()

    # Filter by search query
    if q:
        q_lower = q.lower()
        results = [
            rule
            for rule in results
            if q_lower in rule.name.lower() or q_lower in rule.description.lower()
        ]

    # Filter by faction
    if faction:
        results = [rule for rule in results if rule.faction == faction]

    # Filter by category
    if category:
        results = [rule for rule in results if rule.category == category]

    # Filter by phase
    if phase:
        results = [rule for rule in results if rule.phase == phase]

    return results


@app.get("/stratagems", response_model=List[Stratagem])
def get_stratagems(
    q: Optional[str] = Query(
        None, description="Search query for stratagem name or effect"
    ),
    faction: Optional[str] = Query(None, description="Filter by faction"),
    type: Optional[str] = Query(None, description="Filter by type"),
    phase: Optional[str] = Query(None, description="Filter by phase"),
    max_cost: Optional[int] = Query(None, description="Maximum CP cost"),
) -> List[Stratagem]:
    """
    Get Warhammer 40K stratagems with optional filtering.

    Args:
        q: Search query for stratagem name or effect
        faction: Filter by faction name
        type: Filter by type (Battle Tactic, Strategic Ploy, etc.)
        phase: Filter by phase
        max_cost: Maximum CP cost

    Returns:
        List of stratagems matching the criteria
    """
    results = STRATAGEMS_DATABASE.copy()

    # Filter by search query
    if q:
        q_lower = q.lower()
        results = [
            stratagem
            for stratagem in results
            if q_lower in stratagem.name.lower()
            or q_lower in stratagem.effect.lower()
            or q_lower in stratagem.when.lower()
        ]

    # Filter by faction
    if faction:
        results = [s for s in results if s.faction == faction]

    # Filter by type
    if type:
        results = [s for s in results if s.type == type]

    # Filter by phase
    if phase:
        results = [s for s in results if s.phase == phase]

    # Filter by max cost
    if max_cost is not None:
        results = [s for s in results if s.cost <= max_cost]

    return results


@app.get("/factions", response_model=List[str])
def get_factions() -> List[str]:
    """
    Get list of all available factions across all content types.

    Returns:
        Sorted list of unique faction names
    """
    factions = set()

    # Collect from books
    for book in BOOKS_DATABASE:
        factions.update(book.factions)

    # Collect from rules
    for rule in RULES_DATABASE:
        if rule.faction:
            factions.add(rule.faction)

    # Collect from stratagems
    for stratagem in STRATAGEMS_DATABASE:
        factions.add(stratagem.faction)

    return sorted(list(factions))
