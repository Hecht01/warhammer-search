"""FastAPI application for semantic search of Warhammer 40K lore."""

import os
from typing import List, Optional
from fastapi import FastAPI, Query, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

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


# In-memory books database with curated Warhammer 40K books
BOOKS_DATABASE: List[Book] = [
    # Horus Heresy Series (30K)
    Book(
        title="Horus Rising",
        author="Dan Abnett",
        series="The Horus Heresy",
        factions=["Space Marines", "Imperium"],
        era="30K",
        synopsis="The first book in the Horus Heresy series. "
        "Witness the beginning of the galaxy's greatest betrayal.",
    ),
    Book(
        title="False Gods",
        author="Graham McNeill",
        series="The Horus Heresy",
        factions=["Space Marines", "Chaos"],
        era="30K",
        synopsis="Horus's corruption begins as the Warmaster falls to the dark "
        "powers of Chaos.",
    ),
    Book(
        title="Galaxy in Flames",
        author="Ben Counter",
        series="The Horus Heresy",
        factions=["Space Marines", "Chaos"],
        era="30K",
        synopsis="The Isstvan III atrocity - where loyal Astartes are betrayed by "
        "their traitorous brothers.",
    ),
    Book(
        title="The Flight of the Eisenstein",
        author="James Swallow",
        series="The Horus Heresy",
        factions=["Space Marines", "Imperium"],
        era="30K",
        synopsis="Captain Garro's desperate flight to warn the Emperor of Horus's "
        "treachery.",
    ),
    Book(
        title="Fulgrim",
        author="Graham McNeill",
        series="The Horus Heresy",
        factions=["Space Marines", "Chaos"],
        era="30K",
        synopsis="The tragic fall of the Primarch Fulgrim and his Emperor's "
        "Children Legion.",
    ),
    # Gaunt's Ghosts (Astra Militarum)
    Book(
        title="First and Only",
        author="Dan Abnett",
        series="Gaunt's Ghosts",
        factions=["Astra Militarum", "Imperium"],
        era="40K",
        synopsis="Follow Colonel-Commissar Ibram Gaunt and his regiment of "
        "Tanith First and Only.",
    ),
    Book(
        title="Ghostmaker",
        author="Dan Abnett",
        series="Gaunt's Ghosts",
        factions=["Astra Militarum", "Imperium"],
        era="40K",
        synopsis="The Tanith First continue their campaigns across the war-torn "
        "Sabbat Worlds.",
    ),
    Book(
        title="Necropolis",
        author="Dan Abnett",
        series="Gaunt's Ghosts",
        factions=["Astra Militarum", "Imperium", "Chaos"],
        era="40K",
        synopsis="The epic siege of Vervunhive as Gaunt's Ghosts defend against "
        "overwhelming Chaos forces.",
    ),
    # Eisenhorn Trilogy
    Book(
        title="Xenos",
        author="Dan Abnett",
        series="Eisenhorn",
        factions=["Imperium"],
        era="40K",
        synopsis="Inquisitor Gregor Eisenhorn hunts aliens and heretics in this "
        "classic trilogy opener.",
    ),
    Book(
        title="Malleus",
        author="Dan Abnett",
        series="Eisenhorn",
        factions=["Imperium", "Chaos"],
        era="40K",
        synopsis="Eisenhorn faces daemonic threats and questions his own methods.",
    ),
    Book(
        title="Hereticus",
        author="Dan Abnett",
        series="Eisenhorn",
        factions=["Imperium", "Chaos"],
        era="40K",
        synopsis="The thrilling conclusion as Eisenhorn walks the line between "
        "loyalty and damnation.",
    ),
    # Space Marines
    Book(
        title="Ragnar Blackmane",
        author="Aaron Dembski-Bowden",
        series=None,
        factions=["Space Marines"],
        era="40K",
        synopsis="The legendary Space Wolf returns in this action-packed novel.",
    ),
    Book(
        title="Blood of Asaheim",
        author="Chris Wraight",
        series="Space Wolves",
        factions=["Space Marines"],
        era="40K",
        synopsis="A Space Wolves pack fights to survive on a daemon-infested world.",
    ),
    Book(
        title="The Devastation of Baal",
        author="Guy Haley",
        series=None,
        factions=["Space Marines", "Tyranids"],
        era="41K",
        synopsis="The Blood Angels defend their homeworld against Hive Fleet "
        "Leviathan.",
    ),
    Book(
        title="Dark Imperium",
        author="Guy Haley",
        series="Dark Imperium",
        factions=["Space Marines", "Chaos"],
        era="41K",
        synopsis="Roboute Guilliman returns to lead the Imperium in the Era "
        "Indomitus.",
    ),
    Book(
        title="Dante",
        author="Guy Haley",
        series=None,
        factions=["Space Marines"],
        era="40K",
        synopsis="The story of Commander Dante, oldest living Space Marine.",
    ),
    # Chaos
    Book(
        title="The Talon of Horus",
        author="Aaron Dembski-Bowden",
        series="Black Legion",
        factions=["Chaos Space Marines", "Chaos"],
        era="40K",
        synopsis="Abaddon the Despoiler rises to power after the Horus Heresy.",
    ),
    Book(
        title="Black Legion",
        author="Aaron Dembski-Bowden",
        series="Black Legion",
        factions=["Chaos Space Marines", "Chaos"],
        era="40K",
        synopsis="Abaddon forges his Black Legion and launches his Black Crusades.",
    ),
    Book(
        title="Lords of Silence",
        author="Chris Wraight",
        series=None,
        factions=["Chaos Space Marines", "Chaos"],
        era="41K",
        synopsis="Inside look at a Death Guard warband in the Era Indomitus.",
    ),
    # Necrons
    Book(
        title="The Infinite and the Divine",
        author="Robert Rath",
        series=None,
        factions=["Necrons"],
        era="40K",
        synopsis="A millennia-spanning rivalry between two Necron Overlords. "
        "Darkly comedic.",
    ),
    Book(
        title="Severed",
        author="Nate Crowley",
        series=None,
        factions=["Necrons"],
        era="40K",
        synopsis="Zahndrekh and Obyron, the most eccentric duo in the galaxy.",
    ),
    # Orks
    Book(
        title="Evil Sun Rising",
        author="Guy Haley",
        series=None,
        factions=["Orks"],
        era="40K",
        synopsis="An Ork warboss's rise to power through brutal cunning.",
    ),
    Book(
        title="Brutal Kunnin",
        author="Mike Brooks",
        series=None,
        factions=["Orks", "Astra Militarum"],
        era="40K",
        synopsis="Ufthak Blackhawk leads a daring raid on an Imperial world.",
    ),
    # Aeldari
    Book(
        title="Path of the Warrior",
        author="Gav Thorpe",
        series="Path of the Eldar",
        factions=["Aeldari"],
        era="40K",
        synopsis="Walk the Path of the Warrior with the Aeldari of Craftworld Alaitoc.",
    ),
    Book(
        title="Path of the Seer",
        author="Gav Thorpe",
        series="Path of the Eldar",
        factions=["Aeldari"],
        era="40K",
        synopsis="The second book following an Aeldari's journey through the Paths.",
    ),
    Book(
        title="Valedor",
        author="Guy Haley",
        series=None,
        factions=["Aeldari", "Tyranids"],
        era="40K",
        synopsis="Craftworld Eldar unite against a Tyranid threat.",
    ),
    # T'au Empire
    Book(
        title="Fire Warrior",
        author="Simon Spurrier",
        series=None,
        factions=["Tau"],
        era="40K",
        synopsis="A Fire Warrior's first taste of war in the Greater Good.",
    ),
    Book(
        title="Blades of Damocles",
        author="Phil Kelly",
        series=None,
        factions=["Tau", "Space Marines"],
        era="40K",
        synopsis="The Damocles Crusade - Imperium vs T'au Empire.",
    ),
    # Adeptus Mechanicus
    Book(
        title="Skitarius",
        author="Rob Sanders",
        series="Tech-Priest",
        factions=["Adeptus Mechanicus", "Imperium"],
        era="40K",
        synopsis="Follow the cybernetic warriors of the Adeptus Mechanicus.",
    ),
    Book(
        title="Tech-Priest",
        author="Rob Sanders",
        series="Tech-Priest",
        factions=["Adeptus Mechanicus", "Imperium"],
        era="40K",
        synopsis="A tech-priest's quest for knowledge in the name of the Omnissiah.",
    ),
    # Standalone Classics
    Book(
        title="Fifteen Hours",
        author="Mitchel Scanlon",
        series=None,
        factions=["Astra Militarum", "Imperium"],
        era="40K",
        synopsis="A guardsman's first and last day in the Imperial Guard. "
        "Brutally realistic.",
    ),
    Book(
        title="Storm of Iron",
        author="Graham McNeill",
        series=None,
        factions=["Chaos Space Marines", "Chaos"],
        era="40K",
        synopsis="The Iron Warriors besiege an Imperial fortress in this brutal tale.",
    ),
    Book(
        title="Space Marine",
        author="Ian Watson",
        series=None,
        factions=["Space Marines"],
        era="40K",
        synopsis="One of the earliest Space Marine novels - a classic.",
    ),
    # Sisters of Battle
    Book(
        title="Faith and Fire",
        author="James Swallow",
        series="Sisters of Battle",
        factions=["Imperium"],
        era="40K",
        synopsis="The Adepta Sororitas bring the Emperor's fury to heretics.",
    ),
    # Ciaphas Cain
    Book(
        title="For the Emperor",
        author="Sandy Mitchell",
        series="Ciaphas Cain",
        factions=["Astra Militarum", "Imperium"],
        era="40K",
        synopsis="The first in the humorous series following the reluctant hero "
        "Commissar Cain.",
    ),
    Book(
        title="Caves of Ice",
        author="Sandy Mitchell",
        series="Ciaphas Cain",
        factions=["Astra Militarum", "Imperium", "Necrons"],
        era="40K",
        synopsis="Cain investigates mysterious happenings on an ice world.",
    ),
]


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
