"""FastAPI application for semantic search of Warhammer 40K lore."""

import os
import time
import logging
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


# In-memory books database with curated Warhammer 40K books
BOOKS_DATABASE: List[Book] = [
    # ===== HORUS HERESY SERIES (30K) =====
    Book(
        title="Horus Rising",
        author="Dan Abnett",
        series="The Horus Heresy",
        factions=["Space Marines", "Imperium"],
        era="30K",
        synopsis="The first book in the Horus Heresy series. Witness the beginning of the galaxy's greatest betrayal.",
        page_count=416,
    ),
    Book(
        title="False Gods",
        author="Graham McNeill",
        series="The Horus Heresy",
        factions=["Space Marines", "Chaos"],
        era="30K",
        synopsis="Horus's corruption begins as the Warmaster falls to the dark powers of Chaos.",
        page_count=416,
    ),
    Book(
        title="Galaxy in Flames",
        author="Ben Counter",
        series="The Horus Heresy",
        factions=["Space Marines", "Chaos"],
        era="30K",
        synopsis="The Isstvan III atrocity - where loyal Astartes are betrayed by their traitorous brothers.",
        page_count=416,
    ),
    Book(
        title="The Flight of the Eisenstein",
        author="James Swallow",
        series="The Horus Heresy",
        factions=["Space Marines", "Imperium"],
        era="30K",
        synopsis="Captain Garro's desperate flight to warn the Emperor of Horus's treachery.",
        page_count=416,
    ),
    Book(
        title="Fulgrim",
        author="Graham McNeill",
        series="The Horus Heresy",
        factions=["Space Marines", "Chaos"],
        era="30K",
        synopsis="The tragic fall of the Primarch Fulgrim and his Emperor's Children Legion.",
        page_count=512,
    ),
    Book(
        title="Descent of Angels",
        author="Mitchel Scanlon",
        series="The Horus Heresy",
        factions=["Space Marines"],
        era="30K",
        synopsis="The early history of the Dark Angels Legion and their homeworld Caliban.",
        page_count=416,
    ),
    Book(
        title="Legion",
        author="Dan Abnett",
        series="The Horus Heresy",
        factions=["Space Marines"],
        era="30K",
        synopsis="The mysterious Alpha Legion operates in the shadows during the Great Crusade.",
        page_count=416,
    ),
    Book(
        title="Battle for the Abyss",
        author="Ben Counter",
        series="The Horus Heresy",
        factions=["Space Marines", "Chaos"],
        era="30K",
        synopsis="A desperate mission to stop a massive Chaos warship from reaching Ultramar.",
        page_count=416,
    ),
    Book(
        title="Mechanicum",
        author="Graham McNeill",
        series="The Horus Heresy",
        factions=["Adeptus Mechanicus", "Chaos"],
        era="30K",
        synopsis="The civil war on Mars as the Mechanicum is torn apart by the Heresy.",
        page_count=416,
    ),
    Book(
        title="A Thousand Sons",
        author="Graham McNeill",
        series="The Horus Heresy",
        factions=["Space Marines", "Chaos"],
        era="30K",
        synopsis="Magnus the Red and his Thousand Sons Legion fall to the temptations of sorcery.",
        page_count=528,
    ),
    Book(
        title="Prospero Burns",
        author="Dan Abnett",
        series="The Horus Heresy",
        factions=["Space Marines"],
        era="30K",
        synopsis="The Space Wolves' assault on Prospero, told from the executioners' perspective.",
        page_count=416,
    ),
    Book(
        title="Know No Fear",
        author="Dan Abnett",
        series="The Horus Heresy",
        factions=["Space Marines", "Chaos"],
        era="30K",
        synopsis="The Word Bearers' devastating betrayal of the Ultramarines at Calth.",
        page_count=432,
    ),
    Book(
        title="The First Heretic",
        author="Aaron Dembski-Bowden",
        series="The Horus Heresy",
        factions=["Space Marines", "Chaos"],
        era="30K",
        synopsis="Lorgar and the Word Bearers begin their fall to Chaos worship.",
        page_count=416,
    ),
    Book(
        title="Fear to Tread",
        author="James Swallow",
        series="The Horus Heresy",
        factions=["Space Marines", "Chaos"],
        era="30K",
        synopsis="Sanguinius and the Blood Angels face daemonic corruption at Signus Prime.",
        page_count=512,
    ),
    Book(
        title="The Unremembered Empire",
        author="Dan Abnett",
        series="The Horus Heresy",
        factions=["Space Marines"],
        era="30K",
        synopsis="Guilliman attempts to create Imperium Secundus as the Heresy rages.",
        page_count=480,
    ),
    Book(
        title="Betrayer",
        author="Aaron Dembski-Bowden",
        series="The Horus Heresy",
        factions=["Space Marines", "Chaos"],
        era="30K",
        synopsis="Angron's transformation into a daemon prince and the World Eaters' fall.",
        page_count=432,
    ),
    Book(
        title="The Master of Mankind",
        author="Aaron Dembski-Bowden",
        series="The Horus Heresy",
        factions=["Imperium", "Chaos"],
        era="30K",
        synopsis="The Emperor defends the Imperial Palace and battles in the Webway.",
        page_count=336,
    ),
    Book(
        title="Praetorian of Dorn",
        author="John French",
        series="The Horus Heresy",
        factions=["Space Marines", "Chaos"],
        era="30K",
        synopsis="Rogal Dorn fortifies Terra while Alpha Legion infiltrators plot sabotage.",
        page_count=432,
    ),
    Book(
        title="The Path of Heaven",
        author="Chris Wraight",
        series="The Horus Heresy",
        factions=["Space Marines"],
        era="30K",
        synopsis="The White Scars race to Terra pursued by the Death Guard fleet.",
        page_count=416,
    ),
    # ===== GAUNT'S GHOSTS SERIES (40K) =====
    Book(
        title="First and Only",
        author="Dan Abnett",
        series="Gaunt's Ghosts",
        factions=["Astra Militarum", "Imperium"],
        era="40K",
        synopsis="Follow Colonel-Commissar Ibram Gaunt and his regiment of Tanith First and Only.",
        page_count=320,
    ),
    Book(
        title="Ghostmaker",
        author="Dan Abnett",
        series="Gaunt's Ghosts",
        factions=["Astra Militarum", "Imperium"],
        era="40K",
        synopsis="The Tanith First continue their campaigns across the war-torn Sabbat Worlds.",
        page_count=320,
    ),
    Book(
        title="Necropolis",
        author="Dan Abnett",
        series="Gaunt's Ghosts",
        factions=["Astra Militarum", "Imperium", "Chaos"],
        era="40K",
        synopsis="The epic siege of Vervunhive as Gaunt's Ghosts defend against overwhelming Chaos forces.",
        page_count=416,
    ),
    Book(
        title="Honour Guard",
        author="Dan Abnett",
        series="Gaunt's Ghosts",
        factions=["Astra Militarum", "Imperium"],
        era="40K",
        synopsis="Gaunt must protect a sacred shrine world from the forces of Chaos.",
        page_count=320,
    ),
    Book(
        title="The Guns of Tanith",
        author="Dan Abnett",
        series="Gaunt's Ghosts",
        factions=["Astra Militarum", "Imperium"],
        era="40K",
        synopsis="The Ghosts undertake a daring mission behind enemy lines on a forest moon.",
        page_count=320,
    ),
    Book(
        title="Straight Silver",
        author="Dan Abnett",
        series="Gaunt's Ghosts",
        factions=["Astra Militarum", "Imperium", "Chaos"],
        era="40K",
        synopsis="Brutal trench warfare as the Ghosts assault a heavily fortified Chaos position.",
        page_count=320,
    ),
    Book(
        title="Sabbat Martyr",
        author="Dan Abnett",
        series="Gaunt's Ghosts",
        factions=["Astra Militarum", "Imperium", "Chaos"],
        era="40K",
        synopsis="Gaunt faces political intrigue and assassination attempts while a saint returns.",
        page_count=416,
    ),
    Book(
        title="Traitor General",
        author="Dan Abnett",
        series="Gaunt's Ghosts",
        factions=["Astra Militarum", "Imperium", "Chaos"],
        era="40K",
        synopsis="A covert mission to assassinate a traitorous Imperial commander.",
        page_count=416,
    ),
    Book(
        title="His Last Command",
        author="Dan Abnett",
        series="Gaunt's Ghosts",
        factions=["Astra Militarum", "Imperium"],
        era="40K",
        synopsis="The Ghosts are scattered across multiple warzones in a devastating campaign.",
        page_count=416,
    ),
    Book(
        title="The Armour of Contempt",
        author="Dan Abnett",
        series="Gaunt's Ghosts",
        factions=["Astra Militarum", "Imperium", "Chaos"],
        era="40K",
        synopsis="Gaunt's Ghosts must survive in a labor camp behind enemy lines.",
        page_count=416,
    ),
    Book(
        title="Only in Death",
        author="Dan Abnett",
        series="Gaunt's Ghosts",
        factions=["Astra Militarum", "Imperium", "Chaos"],
        era="40K",
        synopsis="Horror and mystery haunt the Ghosts in a sinister fortress.",
        page_count=416,
    ),
    Book(
        title="Blood Pact",
        author="Dan Abnett",
        series="Gaunt's Ghosts",
        factions=["Astra Militarum", "Imperium", "Chaos"],
        era="40K",
        synopsis="Gaunt hunts for a valuable artifact that could turn the tide of war.",
        page_count=416,
    ),
    # ===== EISENHORN & RAVENOR SERIES (40K) =====
    Book(
        title="Xenos",
        author="Dan Abnett",
        series="Eisenhorn",
        factions=["Imperium"],
        era="40K",
        synopsis="Inquisitor Gregor Eisenhorn hunts aliens and heretics in this classic trilogy opener.",
        page_count=320,
    ),
    Book(
        title="Malleus",
        author="Dan Abnett",
        series="Eisenhorn",
        factions=["Imperium", "Chaos"],
        era="40K",
        synopsis="Eisenhorn faces daemonic threats and questions his own methods.",
        page_count=416,
    ),
    Book(
        title="Hereticus",
        author="Dan Abnett",
        series="Eisenhorn",
        factions=["Imperium", "Chaos"],
        era="40K",
        synopsis="The thrilling conclusion as Eisenhorn walks the line between loyalty and damnation.",
        page_count=416,
    ),
    Book(
        title="Ravenor",
        author="Dan Abnett",
        series="Ravenor",
        factions=["Imperium"],
        era="40K",
        synopsis="Inquisitor Gideon Ravenor, encased in a life support chair, hunts heretics.",
        page_count=320,
    ),
    Book(
        title="Ravenor Returned",
        author="Dan Abnett",
        series="Ravenor",
        factions=["Imperium", "Chaos"],
        era="40K",
        synopsis="Ravenor continues his investigation into a conspiracy spanning multiple worlds.",
        page_count=416,
    ),
    Book(
        title="Ravenor Rogue",
        author="Dan Abnett",
        series="Ravenor",
        factions=["Imperium", "Chaos"],
        era="40K",
        synopsis="The explosive finale as Ravenor goes rogue to stop a terrible threat.",
        page_count=416,
    ),
    Book(
        title="The Magos",
        author="Dan Abnett",
        series="Eisenhorn",
        factions=["Imperium", "Chaos"],
        era="40K",
        synopsis="A collection of Eisenhorn stories including a new full-length novel.",
        page_count=592,
    ),
    Book(
        title="Pariah",
        author="Dan Abnett",
        series="Bequin",
        factions=["Imperium"],
        era="40K",
        synopsis="The first book in a new trilogy connecting Eisenhorn and Ravenor.",
        page_count=368,
    ),
    # ===== SPACE MARINES - VARIOUS CHAPTERS (40K/41K) =====
    Book(
        title="Ragnar Blackmane",
        author="Aaron Dembski-Bowden",
        series=None,
        factions=["Space Marines"],
        era="40K",
        synopsis="The legendary Space Wolf returns in this action-packed novel.",
        page_count=240,
    ),
    Book(
        title="Blood of Asaheim",
        author="Chris Wraight",
        series="Space Wolves",
        factions=["Space Marines"],
        era="40K",
        synopsis="A Space Wolves pack fights to survive on a daemon-infested world.",
        page_count=416,
    ),
    Book(
        title="The Devastation of Baal",
        author="Guy Haley",
        series=None,
        factions=["Space Marines", "Tyranids"],
        era="41K",
        synopsis="The Blood Angels defend their homeworld against Hive Fleet Leviathan.",
        page_count=384,
    ),
    Book(
        title="Dark Imperium",
        author="Guy Haley",
        series="Dark Imperium",
        factions=["Space Marines", "Chaos"],
        era="41K",
        synopsis="Roboute Guilliman returns to lead the Imperium in the Era Indomitus.",
        page_count=384,
    ),
    Book(
        title="Dante",
        author="Guy Haley",
        series=None,
        factions=["Space Marines"],
        era="40K",
        synopsis="The story of Commander Dante, oldest living Space Marine.",
        page_count=400,
    ),
    Book(
        title="Plague War",
        author="Guy Haley",
        series="Dark Imperium",
        factions=["Space Marines", "Chaos"],
        era="41K",
        synopsis="Guilliman battles Mortarion and the Death Guard in Ultramar.",
        page_count=400,
    ),
    Book(
        title="Godblight",
        author="Guy Haley",
        series="Dark Imperium",
        factions=["Space Marines", "Chaos"],
        era="41K",
        synopsis="The epic conclusion as Guilliman confronts Nurgle's plague.",
        page_count=448,
    ),
    Book(
        title="Spear of the Emperor",
        author="Aaron Dembski-Bowden",
        series=None,
        factions=["Space Marines"],
        era="41K",
        synopsis="A serf's perspective on the mysterious Emperor's Spears Chapter.",
        page_count=352,
    ),
    Book(
        title="The Phoenician",
        author="Josh Reynolds",
        series=None,
        factions=["Space Marines"],
        era="40K",
        synopsis="The Tome Keepers Chapter hunts for forbidden knowledge.",
        page_count=304,
    ),
    # ===== SPACE MARINE BATTLES SERIES =====
    Book(
        title="Helsreach",
        author="Aaron Dembski-Bowden",
        series="Space Marine Battles",
        factions=["Space Marines", "Orks"],
        era="40K",
        synopsis="Grimaldus and the Black Templars defend Hive Helsreach from an Ork invasion.",
        page_count=416,
    ),
    Book(
        title="Rynn's World",
        author="Steve Parker",
        series="Space Marine Battles",
        factions=["Space Marines", "Orks"],
        era="40K",
        synopsis="The Crimson Fists fight for survival after their fortress-monastery is destroyed.",
        page_count=416,
    ),
    Book(
        title="The Purging of Kadillus",
        author="Gav Thorpe",
        series="Space Marine Battles",
        factions=["Space Marines", "Orks"],
        era="40K",
        synopsis="The Dark Angels battle an Ork Waaagh! while hunting the Fallen.",
        page_count=416,
    ),
    Book(
        title="Fall of Damnos",
        author="Nick Kyme",
        series="Space Marine Battles",
        factions=["Space Marines", "Necrons"],
        era="40K",
        synopsis="The Ultramarines face an awakening Necron dynasty on Damnos.",
        page_count=416,
    ),
    Book(
        title="Battle of the Fang",
        author="Chris Wraight",
        series="Space Marine Battles",
        factions=["Space Marines", "Chaos"],
        era="40K",
        synopsis="The Space Wolves defend their homeworld from the Thousand Sons.",
        page_count=416,
    ),
    # ===== CHAOS SPACE MARINES (40K/41K) =====
    Book(
        title="The Talon of Horus",
        author="Aaron Dembski-Bowden",
        series="Black Legion",
        factions=["Chaos Space Marines", "Chaos"],
        era="40K",
        synopsis="Abaddon the Despoiler rises to power after the Horus Heresy.",
        page_count=448,
    ),
    Book(
        title="Black Legion",
        author="Aaron Dembski-Bowden",
        series="Black Legion",
        factions=["Chaos Space Marines", "Chaos"],
        era="40K",
        synopsis="Abaddon forges his Black Legion and launches his Black Crusades.",
        page_count=432,
    ),
    Book(
        title="Lords of Silence",
        author="Chris Wraight",
        series=None,
        factions=["Chaos Space Marines", "Chaos"],
        era="41K",
        synopsis="Inside look at a Death Guard warband in the Era Indomitus.",
        page_count=336,
    ),
    Book(
        title="Storm of Iron",
        author="Graham McNeill",
        series=None,
        factions=["Chaos Space Marines", "Chaos"],
        era="40K",
        synopsis="The Iron Warriors besiege an Imperial fortress in this brutal tale.",
        page_count=416,
    ),
    Book(
        title="Night Lords: Soul Hunter",
        author="Aaron Dembski-Bowden",
        series="Night Lords",
        factions=["Chaos Space Marines", "Chaos"],
        era="40K",
        synopsis="A Night Lords warband struggles to survive in the Eye of Terror.",
        page_count=416,
    ),
    Book(
        title="Night Lords: Blood Reaver",
        author="Aaron Dembski-Bowden",
        series="Night Lords",
        factions=["Chaos Space Marines", "Chaos"],
        era="40K",
        synopsis="The Night Lords raid Imperial space in search of supplies and revenge.",
        page_count=416,
    ),
    Book(
        title="Night Lords: Void Stalker",
        author="Aaron Dembski-Bowden",
        series="Night Lords",
        factions=["Chaos Space Marines", "Chaos"],
        era="40K",
        synopsis="The explosive conclusion to the Night Lords trilogy.",
        page_count=416,
    ),
    # ===== NECRONS (40K) =====
    Book(
        title="The Infinite and the Divine",
        author="Robert Rath",
        series=None,
        factions=["Necrons"],
        era="40K",
        synopsis="A millennia-spanning rivalry between two Necron Overlords. Darkly comedic.",
        page_count=416,
    ),
    Book(
        title="Severed",
        author="Nate Crowley",
        series=None,
        factions=["Necrons"],
        era="40K",
        synopsis="Zahndrekh and Obyron, the most eccentric duo in the galaxy.",
        page_count=128,
    ),
    Book(
        title="The Twice-Dead King: Ruin",
        author="Nate Crowley",
        series="The Twice-Dead King",
        factions=["Necrons"],
        era="40K",
        synopsis="A Necron prince struggles with madness while defending his crumbling dynasty.",
        page_count=368,
    ),
    Book(
        title="The Twice-Dead King: Reign",
        author="Nate Crowley",
        series="The Twice-Dead King",
        factions=["Necrons"],
        era="40K",
        synopsis="Oltyx must embrace his transformation to save his people.",
        page_count=400,
    ),
    # ===== TYRANIDS (40K) =====
    Book(
        title="Pharos",
        author="Guy Haley",
        series="The Horus Heresy",
        factions=["Space Marines", "Tyranids"],
        era="30K",
        synopsis="The Pharos beacon draws the attention of the Tyranid Hive Mind.",
        page_count=512,
    ),
    Book(
        title="Warriors of Ultramar",
        author="Graham McNeill",
        series="Ultramarines",
        factions=["Space Marines", "Tyranids"],
        era="40K",
        synopsis="Captain Uriel Ventris battles a Tyranid invasion of Tarsis Ultra.",
        page_count=416,
    ),
    Book(
        title="Day of Ascension",
        author="Adrian Tchaikovsky",
        series=None,
        factions=["Tyranids", "Genestealer Cults"],
        era="40K",
        synopsis="A planet's population unknowingly embraces their Genestealer Cult overlords.",
        page_count=320,
    ),
    # ===== ORKS (40K) =====
    Book(
        title="Evil Sun Rising",
        author="Guy Haley",
        series=None,
        factions=["Orks"],
        era="40K",
        synopsis="An Ork warboss's rise to power through brutal cunning.",
        page_count=368,
    ),
    Book(
        title="Brutal Kunnin",
        author="Mike Brooks",
        series=None,
        factions=["Orks", "Astra Militarum"],
        era="40K",
        synopsis="Ufthak Blackhawk leads a daring raid on an Imperial world.",
        page_count=400,
    ),
    Book(
        title="Da Big Dakka",
        author="Mike Brooks",
        series=None,
        factions=["Orks"],
        era="40K",
        synopsis="Ufthak returns with more dakka, bigger explosions, and cunning plans.",
        page_count=400,
    ),
    # ===== AELDARI (40K) =====
    Book(
        title="Path of the Warrior",
        author="Gav Thorpe",
        series="Path of the Eldar",
        factions=["Aeldari"],
        era="40K",
        synopsis="Walk the Path of the Warrior with the Aeldari of Craftworld Alaitoc.",
        page_count=416,
    ),
    Book(
        title="Path of the Seer",
        author="Gav Thorpe",
        series="Path of the Eldar",
        factions=["Aeldari"],
        era="40K",
        synopsis="The second book following an Aeldari's journey through the Paths.",
        page_count=416,
    ),
    Book(
        title="Path of the Outcast",
        author="Gav Thorpe",
        series="Path of the Eldar",
        factions=["Aeldari"],
        era="40K",
        synopsis="The final book exploring those who leave the Craftworlds behind.",
        page_count=416,
    ),
    Book(
        title="Valedor",
        author="Guy Haley",
        series=None,
        factions=["Aeldari", "Tyranids"],
        era="40K",
        synopsis="Craftworld Eldar unite against a Tyranid threat.",
        page_count=384,
    ),
    Book(
        title="Wild Rider",
        author="Robbie MacNiven",
        series=None,
        factions=["Aeldari"],
        era="40K",
        synopsis="A Wild Rider must save her Craftworld from destruction.",
        page_count=368,
    ),
    Book(
        title="Path of the Dark Eldar",
        author="Andy Chambers",
        series="Dark Eldar",
        factions=["Aeldari"],
        era="40K",
        synopsis="A trilogy exploring the depraved society of Commorragh.",
        page_count=784,
    ),
    # ===== T'AU EMPIRE (40K) =====
    Book(
        title="Fire Warrior",
        author="Simon Spurrier",
        series=None,
        factions=["Tau"],
        era="40K",
        synopsis="A Fire Warrior's first taste of war in the Greater Good.",
        page_count=288,
    ),
    Book(
        title="Blades of Damocles",
        author="Phil Kelly",
        series=None,
        factions=["Tau", "Space Marines"],
        era="40K",
        synopsis="The Damocles Crusade - Imperium vs T'au Empire.",
        page_count=480,
    ),
    Book(
        title="Farsight: Crisis of Faith",
        author="Phil Kelly",
        series=None,
        factions=["Tau"],
        era="40K",
        synopsis="Commander Farsight breaks from the T'au Empire to forge his own path.",
        page_count=368,
    ),
    Book(
        title="Farsight: Empire of Lies",
        author="Phil Kelly",
        series=None,
        factions=["Tau"],
        era="40K",
        synopsis="Farsight uncovers dark secrets at the heart of the T'au Empire.",
        page_count=368,
    ),
    Book(
        title="War of Secrets",
        author="Phil Kelly",
        series=None,
        factions=["Tau", "Space Marines"],
        era="40K",
        synopsis="Dark Angels and T'au clash over a vital world.",
        page_count=368,
    ),
    # ===== ADEPTUS MECHANICUS (40K) =====
    Book(
        title="Skitarius",
        author="Rob Sanders",
        series="Tech-Priest",
        factions=["Adeptus Mechanicus", "Imperium"],
        era="40K",
        synopsis="Follow the cybernetic warriors of the Adeptus Mechanicus.",
        page_count=256,
    ),
    Book(
        title="Tech-Priest",
        author="Rob Sanders",
        series="Tech-Priest",
        factions=["Adeptus Mechanicus", "Imperium"],
        era="40K",
        synopsis="A tech-priest's quest for knowledge in the name of the Omnissiah.",
        page_count=256,
    ),
    Book(
        title="Forge of Mars",
        author="Graham McNeill",
        series="Forge of Mars",
        factions=["Adeptus Mechanicus", "Imperium"],
        era="40K",
        synopsis="An Ark Mechanicus ventures into the unknown in search of lost technology.",
        page_count=976,
    ),
    # ===== ASTRA MILITARUM (40K) =====
    Book(
        title="Fifteen Hours",
        author="Mitchel Scanlon",
        series=None,
        factions=["Astra Militarum", "Imperium"],
        era="40K",
        synopsis="A guardsman's first and last day in the Imperial Guard. Brutally realistic.",
        page_count=288,
    ),
    Book(
        title="For the Emperor",
        author="Sandy Mitchell",
        series="Ciaphas Cain",
        factions=["Astra Militarum", "Imperium"],
        era="40K",
        synopsis="The first in the humorous series following the reluctant hero Commissar Cain.",
        page_count=320,
    ),
    Book(
        title="Caves of Ice",
        author="Sandy Mitchell",
        series="Ciaphas Cain",
        factions=["Astra Militarum", "Imperium", "Necrons"],
        era="40K",
        synopsis="Cain investigates mysterious happenings on an ice world.",
        page_count=320,
    ),
    Book(
        title="The Traitor's Hand",
        author="Sandy Mitchell",
        series="Ciaphas Cain",
        factions=["Astra Militarum", "Imperium", "Chaos"],
        era="40K",
        synopsis="Cain must root out a Chaos cult while avoiding actual danger.",
        page_count=320,
    ),
    Book(
        title="Death or Glory",
        author="Sandy Mitchell",
        series="Ciaphas Cain",
        factions=["Astra Militarum", "Imperium", "Orks"],
        era="40K",
        synopsis="Cain and a ragtag group try to escape through Ork-held territory.",
        page_count=320,
    ),
    Book(
        title="Cadian Blood",
        author="Aaron Dembski-Bowden",
        series=None,
        factions=["Astra Militarum", "Imperium", "Chaos"],
        era="40K",
        synopsis="Cadian shock troops battle zombie hordes on a plague world.",
        page_count=416,
    ),
    Book(
        title="Baneblade",
        author="Guy Haley",
        series=None,
        factions=["Astra Militarum", "Imperium"],
        era="40K",
        synopsis="The crew of a massive super-heavy tank fights across a war-torn world.",
        page_count=416,
    ),
    # ===== SISTERS OF BATTLE (40K) =====
    Book(
        title="Faith and Fire",
        author="James Swallow",
        series="Sisters of Battle",
        factions=["Imperium"],
        era="40K",
        synopsis="The Adepta Sororitas bring the Emperor's fury to heretics.",
        page_count=416,
    ),
    Book(
        title="Celestine: The Living Saint",
        author="Andy Clark",
        series=None,
        factions=["Imperium"],
        era="40K",
        synopsis="The story of Saint Celestine's resurrection and crusade.",
        page_count=368,
    ),
    # ===== WARHAMMER CRIME SERIES =====
    Book(
        title="Bloodlines",
        author="Chris Wraight",
        series="Warhammer Crime",
        factions=["Imperium"],
        era="40K",
        synopsis="A probator investigates murder and corruption in the underhive of Varangantua.",
        page_count=352,
    ),
    Book(
        title="Flesh and Steel",
        author="Guy Haley",
        series="Warhammer Crime",
        factions=["Imperium"],
        era="40K",
        synopsis="A detective and his Ogryn partner solve crimes in a hive city.",
        page_count=320,
    ),
    Book(
        title="Grim Repast",
        author="Marc Collins",
        series="Warhammer Crime",
        factions=["Imperium"],
        era="40K",
        synopsis="A murder mystery in the upper spires of a hive city.",
        page_count=288,
    ),
    Book(
        title="The Vorbis Conspiracy",
        author="Gary Kloster",
        series="Warhammer Crime",
        factions=["Imperium"],
        era="40K",
        synopsis="An investigation into corporate espionage and murder.",
        page_count=304,
    ),
    # ===== WARHAMMER HORROR SERIES =====
    Book(
        title="The Wicked and the Damned",
        author="Various",
        series="Warhammer Horror",
        factions=["Chaos", "Imperium"],
        era="40K",
        synopsis="Three sinners confess their tales of horror aboard a ship in the warp.",
        page_count=320,
    ),
    Book(
        title="The Reverie",
        author="Peter Fehervari",
        series="Warhammer Horror",
        factions=["Imperium"],
        era="40K",
        synopsis="A colonist awakens to find reality itself unraveling.",
        page_count=304,
    ),
    Book(
        title="Maledictions",
        author="Various",
        series="Warhammer Horror",
        factions=["Imperium", "Chaos"],
        era="40K",
        synopsis="A collection of dark tales from the grimdark future.",
        page_count=352,
    ),
    Book(
        title="The Harrowing of Absalom",
        author="Various",
        series="Warhammer Horror",
        factions=["Imperium"],
        era="40K",
        synopsis="Horror stories set on the haunted world of Absalom.",
        page_count=320,
    ),
    # ===== RECENT RELEASES (2020-2024) =====
    Book(
        title="The Endless War",
        author="Chris Wraight",
        series=None,
        factions=["Imperium", "Chaos"],
        era="41K",
        synopsis="The Siege of Terra's aftermath and the founding of the Indomitus Crusade.",
        page_count=400,
    ),
    Book(
        title="Avenging Son",
        author="Guy Haley",
        series="Dawn of Fire",
        factions=["Space Marines", "Chaos"],
        era="41K",
        synopsis="The first Dawn of Fire novel, following the Indomitus Crusade.",
        page_count=368,
    ),
    Book(
        title="The Gate of Bones",
        author="Andy Clark",
        series="Dawn of Fire",
        factions=["Space Marines", "Chaos"],
        era="41K",
        synopsis="Imperial forces battle to secure a vital warp gate.",
        page_count=400,
    ),
    Book(
        title="Wolftime",
        author="Gav Thorpe",
        series="Dawn of Fire",
        factions=["Space Marines", "Chaos"],
        era="41K",
        synopsis="Space Wolves and their Primaris reinforcements clash with the Death Guard.",
        page_count=384,
    ),
    Book(
        title="The Throne of Light",
        author="Guy Haley",
        series="Dawn of Fire",
        factions=["Space Marines", "Chaos"],
        era="41K",
        synopsis="The Indomitus Crusade faces its greatest challenges yet.",
        page_count=416,
    ),
    Book(
        title="Leviathan",
        author="Darius Hinks",
        series=None,
        factions=["Space Marines", "Tyranids"],
        era="41K",
        synopsis="The newest Tyranid invasion threatens the Imperium Nihilus.",
        page_count=368,
    ),
    # ===== CLASSIC STANDALONES =====
    Book(
        title="Space Marine",
        author="Ian Watson",
        series=None,
        factions=["Space Marines"],
        era="40K",
        synopsis="One of the earliest Space Marine novels - a classic.",
        page_count=288,
    ),
]


# Rules database with core rules and faction-specific rules
RULES_DATABASE: List[Rule] = [
    # ========== CORE RULES - MOVEMENT PHASE ==========
    Rule(
        name="Move",
        category="Core Rules",
        description="Units can move up to their Move (M) characteristic in inches. "
        "They cannot move within Engagement Range of enemy models unless they have special abilities.",
        phase="Movement",
    ),
    Rule(
        name="Advance",
        category="Core Rules",
        description="Instead of moving normally, a unit can Advance. Roll D6 and add "
        "to Move characteristic. Cannot shoot (except Assault weapons) or charge this turn.",
        phase="Movement",
    ),
    Rule(
        name="Fall Back",
        category="Core Rules",
        description="Units within Engagement Range can Fall Back instead of making "
        "a Normal Move. Cannot shoot or charge this turn (unless they have FLY keyword).",
        phase="Movement",
    ),
    Rule(
        name="Remain Stationary",
        category="Core Rules",
        description="A unit that does not move in the Movement phase counts as Remaining Stationary. "
        "Some weapons and abilities gain bonuses when the unit Remains Stationary.",
        phase="Movement",
    ),
    Rule(
        name="Engagement Range",
        category="Core Rules",
        description='Engagement Range is within 1" horizontally and 5" vertically of an enemy model. '
        "Units within Engagement Range cannot shoot (unless specifically allowed) and must Fall Back or Fight.",
        phase="Any",
    ),
    # ========== CORE RULES - UNIVERSAL SPECIAL ABILITIES ==========
    Rule(
        name="Deep Strike",
        category="Universal Special Rule",
        description="During Declare Battle Formations, units with this ability can be set up in Reserves. "
        'In the Reinforcements step of your Movement phase, set up anywhere more than 9" from enemy models.',
        phase="Movement",
    ),
    Rule(
        name="Scouts",
        category="Universal Special Rule",
        description='Before the first turn begins, units with Scouts can make a Normal move of up to 6" or a '
        'Normal move of up to D6". Cannot move within 9" of enemy models.',
        phase="Movement",
    ),
    Rule(
        name="Infiltrators",
        category="Universal Special Rule",
        description="During Declare Battle Formations, units with Infiltrators can be set up anywhere on the "
        'battlefield more than 9" from enemy deployment zone and enemy models.',
        phase="Movement",
    ),
    Rule(
        name="Stealth",
        category="Universal Special Rule",
        description="If every model in a unit has Stealth, ranged attacks targeting that unit take -1 to Hit rolls. "
        "Represents camouflage, concealment technology, or supernatural obscurement.",
        phase="Shooting",
    ),
    Rule(
        name="Lone Operative",
        category="Universal Special Rule",
        description="Unless part of an Attached unit, this unit can only be selected as target of ranged attack if "
        'attacking model is within 12". Common on stealthy specialists like Assassins.',
        phase="Shooting",
    ),
    Rule(
        name="Leader",
        category="Universal Special Rule",
        description="Character units with Leader can be attached to Bodyguard units before battle. "
        "While attached, Character cannot be targeted separately and uses Bodyguard's Toughness for attacks.",
        phase="Any",
    ),
    Rule(
        name="Deadly Demise",
        category="Universal Special Rule",
        description='When a model with Deadly Demise is destroyed, roll D6 for each unit within 6". '
        "On 6, that unit suffers mortal wounds equal to Deadly Demise value (e.g., Deadly Demise D3).",
        phase="Any",
    ),
    Rule(
        name="Big Guns Never Tire",
        category="Universal Special Rule",
        description="Vehicles with this ability can shoot even if within Engagement Range of enemy units, "
        "and can target enemy units within Engagement Range with ranged weapons (at -1 to Hit).",
        phase="Shooting",
    ),
    # ========== CORE RULES - SHOOTING PHASE ==========
    Rule(
        name="Shooting",
        category="Core Rules",
        description="Select eligible targets, roll to hit using BS, roll to wound using weapon Strength vs target Toughness, "
        "allocate wounds, defender makes saving throws. Cannot shoot if within Engagement Range (unless specifically allowed).",
        phase="Shooting",
    ),
    Rule(
        name="Ballistic Skill (BS)",
        category="Core Rules",
        description="To hit with ranged weapons, roll D6. If result equals or exceeds the "
        "model's BS characteristic, it hits. An unmodified roll of 6 is a Critical Hit.",
        phase="Shooting",
    ),
    Rule(
        name="Cover",
        category="Core Rules",
        description="If target is in Cover (fully within terrain), ranged attacks against them get worse AP by 1 "
        "(e.g., AP-2 becomes AP-1, AP-1 becomes AP0). Does not affect invulnerable saves.",
        phase="Shooting",
    ),
    Rule(
        name="Fire Overwatch",
        category="Core Rules",
        description="1CP Stratagem. When enemy declares charge, one of your units can shoot at them "
        "(hit only on unmodified 6s). Can only be used once per turn. Towering units cannot fire Overwatch.",
        phase="Charge",
    ),
    # ========== CORE RULES - CHARGE & FIGHT PHASE ==========
    Rule(
        name="Charge",
        category="Core Rules",
        description="Roll 2D6. Unit can move that many inches toward enemy unit, must end within Engagement Range "
        "to make charge successful. Cannot charge if Advanced this turn (unless specifically allowed).",
        phase="Charge",
    ),
    Rule(
        name="Fight",
        category="Core Rules",
        description="Units within Engagement Range or that charged this turn can fight. Select targets, "
        "roll to hit using WS, roll to wound, allocate wounds, make saves. Units that charged fight first.",
        phase="Fight",
    ),
    Rule(
        name="Weapon Skill (WS)",
        category="Core Rules",
        description="To hit in melee combat, roll D6. If result equals or exceeds the "
        "model's WS characteristic, it hits. An unmodified roll of 6 is a Critical Hit.",
        phase="Fight",
    ),
    Rule(
        name="Fights First",
        category="Core Rules",
        description="Units that charged, were charged, or have Fights First ability fight in Fights First step. "
        "After all Fights First units have fought, remaining units fight.",
        phase="Fight",
    ),
    # ========== CORE RULES - MORALE & BATTLE-SHOCK ==========
    Rule(
        name="Battle-shock",
        category="Core Rules",
        description="In Command phase, if unit is Below Half-strength, take Battle-shock test (roll 2D6, "
        "compare to Ld). If failed, unit is Battle-shocked until next Command phase: OC becomes 0, cannot use Stratagems.",
        phase="Command",
    ),
    # ========== CORE RULES - SAVING THROWS ==========
    Rule(
        name="Invulnerable Save",
        category="Core Rules",
        description="Special save that can be made instead of normal save. Never "
        "modified by AP or other modifiers. Typically 4++, 5++, or 6++. Represents force fields, supernatural protection.",
        phase="Any",
    ),
    Rule(
        name="Feel No Pain (FNP)",
        category="Core Rules",
        description="After a model loses a wound (after saves), roll D6 for each wound. On specified value "
        "(usually 4+, 5+, or 6+), that wound is ignored. FNP works against mortal wounds.",
        phase="Any",
    ),
    # ========== CORE RULES - WEAPON ABILITIES ==========
    Rule(
        name="Critical Hit",
        category="Core Rules",
        description="An unmodified Hit roll of 6 is always successful and is a Critical Hit. "
        "Critical Hits trigger abilities like Lethal Hits and Sustained Hits. Some abilities cause Criticals on 5+ or other values.",
        phase="Any",
    ),
    Rule(
        name="Critical Wound",
        category="Core Rules",
        description="An unmodified Wound roll of 6 is always successful and is a Critical Wound. "
        "Critical Wounds trigger abilities like Devastating Wounds. Anti- abilities can cause Criticals on lower values.",
        phase="Any",
    ),
    Rule(
        name="Lethal Hits",
        category="Universal Special Rule",
        description="Each time an attack with this weapon scores a Critical Hit, automatically wound the target "
        "(do not make a Wound roll). Extremely powerful against high-Toughness targets.",
        phase="Any",
    ),
    Rule(
        name="Sustained Hits",
        category="Universal Special Rule",
        description="Each time an attack with this weapon scores a Critical Hit, generate X additional hit(s) "
        "(e.g., Sustained Hits 1 = 1 extra hit, Sustained Hits 2 = 2 extra hits). Extra hits must still roll to wound.",
        phase="Any",
    ),
    Rule(
        name="Devastating Wounds",
        category="Universal Special Rule",
        description="Each time an attack with this weapon scores a Critical Wound, target cannot make saves "
        "(including invulnerable saves). Inflicts mortal wounds equal to Damage characteristic.",
        phase="Any",
    ),
    Rule(
        name="Twin-Linked",
        category="Universal Special Rule",
        description="Weapons with Twin-Linked can re-roll the Wound roll. Represents weapons with multiple "
        "barrels or firing mechanisms working in tandem.",
        phase="Any",
    ),
    Rule(
        name="Anti-Keyword X+",
        category="Universal Special Rule",
        description="When attacking targets with the specified keyword (e.g., Anti-Vehicle, Anti-Monster, Anti-Infantry), "
        "Wound rolls of X+ are Critical Wounds. Anti-Vehicle 4+ makes 4+ wound rolls Critical against Vehicles.",
        phase="Any",
    ),
    Rule(
        name="Assault",
        category="Universal Special Rule",
        description="Weapons with Assault can be shot even if the firing unit Advanced this turn. "
        "Represents lighter weapons that can be fired on the move.",
        phase="Shooting",
    ),
    Rule(
        name="Heavy",
        category="Universal Special Rule",
        description="Weapons with Heavy get +1 to Hit if the firing unit Remained Stationary. "
        "Represents heavy weapons that benefit from stable firing positions.",
        phase="Shooting",
    ),
    Rule(
        name="Rapid Fire",
        category="Universal Special Rule",
        description="Weapons with Rapid Fire X increase their Attacks characteristic by X when targeting "
        'units within half the weapon\'s range (e.g., Rapid Fire 2 at 12" range gains +2 attacks at 6" or less).',
        phase="Shooting",
    ),
    Rule(
        name="Blast",
        category="Universal Special Rule",
        description="Weapons with Blast cannot target units within Engagement Range of friendly units. "
        "When targeting units with 6+ models, Blast weapons get maximum number of attacks automatically.",
        phase="Shooting",
    ),
    Rule(
        name="Torrent",
        category="Universal Special Rule",
        description="Weapons with Torrent automatically hit their target (no Hit roll required). "
        "Typically found on flame weapons. Still requires Wound rolls.",
        phase="Shooting",
    ),
    Rule(
        name="Ignores Cover",
        category="Universal Special Rule",
        description="Attacks with Ignores Cover are not affected by target being in Cover. "
        "Target does not get Cover's AP improvement against these attacks.",
        phase="Shooting",
    ),
    Rule(
        name="Precision",
        category="Universal Special Rule",
        description="When attacking with Precision weapon, on Critical Hit you can select which model in target unit "
        "takes the damage (even if it's a Character or other special model).",
        phase="Any",
    ),
    Rule(
        name="Hazardous",
        category="Universal Special Rule",
        description="After firing a Hazardous weapon, roll one D6 for each hit roll of 1. "
        "For each 1-2 result, firing unit suffers 1 mortal wound. Represents unstable or dangerous weapons.",
        phase="Shooting",
    ),
    # ========== FACTION RULES - IMPERIUM ==========
    Rule(
        name="Oath of Moment",
        category="Faction",
        faction="Space Marines",
        description="At start of your Command phase, select one enemy unit to be your Oath of Moment target. "
        "All your Space Marines units get +1 to Hit rolls when targeting that unit until start of next Command phase.",
        phase="Command",
    ),
    Rule(
        name="And They Shall Know No Fear",
        category="Faction",
        faction="Space Marines",
        description="Space Marines units can re-roll Battle-shock and Leadership tests. "
        "Represents their exceptional training, genetic enhancement, and unshakeable resolve.",
        phase="Command",
    ),
    Rule(
        name="Voice of Command",
        category="Faction",
        faction="Astra Militarum",
        description='OFFICER models can issue Orders in Command phase to friendly units within 6". '
        "Orders include: Take Aim (+1 to Hit), First Rank Fire Second Rank Fire (Rapid Fire), Move Move Move (extra move), Fix Bayonets (melee bonuses).",
        phase="Command",
    ),
    Rule(
        name="Acts of Faith",
        category="Faction",
        faction="Adepta Sororitas",
        description="Gain Miracle dice at start of each round and when units are destroyed. Before making a dice roll "
        "(Advance, Charge, Hit, Wound, Damage, Save, Battle-shock), can substitute one die with a Miracle die. Each unit once per phase.",
        phase="Any",
    ),
    Rule(
        name="Martial Ka'tah",
        category="Faction",
        faction="Adeptus Custodes",
        description="At start of Fight phase, select one Martial Ka'tah stance for your Custodes units. "
        "Stances provide different combat bonuses. Represents the supreme martial prowess of the Emperor's guardians.",
        phase="Fight",
    ),
    Rule(
        name="Teleport Assault",
        category="Faction",
        faction="Grey Knights",
        description="At end of opponent's turn, can place 1-4 Grey Knights units (depending on battle size) into Strategic Reserves. "
        "They return in Reinforcements step of your next Movement phase using Deep Strike rules. Represents teleportation.",
        phase="Movement",
    ),
    Rule(
        name="Doctrina Imperatives",
        category="Faction",
        faction="Adeptus Mechanicus",
        description="At start of battle round, select one Doctrina Imperative: Protector Imperative (+1 BS, -1 to be hit in melee) "
        "or Conqueror Imperative (+1 WS, +1 to be hit by ranged). Affects eligible Skitarii units until end of round.",
        phase="Command",
    ),
    Rule(
        name="Code Chivalric",
        category="Faction",
        faction="Imperial Knights",
        description="Before battle, select or randomly determine an Oath (one Deed and one Quality). "
        "First time your Deed is completed, army becomes Honoured and gains 2-3CP. Represents knightly honor codes.",
        phase="Command",
    ),
    # ========== FACTION RULES - CHAOS ==========
    Rule(
        name="Dark Pacts",
        category="Faction",
        faction="Chaos Space Marines",
        description="Each time you make a Hit, Wound, or Damage roll for a Chaos Space Marines unit, you can make a Dark Pact "
        "to re-roll that die. After resolving attack, that unit suffers D3 mortal wounds (bargaining with Chaos is costly).",
        phase="Any",
    ),
    Rule(
        name="Blessings of Khorne",
        category="Faction",
        faction="World Eaters",
        description="At start of battle round, roll 8D6. Use those dice to activate up to two Blessings of Khorne "
        "(requiring specific dice results like doubles, triples). Each Blessing affects all World Eaters units until end of round.",
        phase="Command",
    ),
    Rule(
        name="Nurgle's Gift",
        category="Faction",
        faction="Death Guard",
        description='Enemy units within Contagion Range (3" round 1, 6" round 2, 9" round 3+) of Death Guard models are Afflicted: '
        "-1 Toughness and one additional penalty (varies by plague chosen: -1 to Hit, -1 Save, or -1 OC/Ld/Move).",
        phase="Any",
    ),
    Rule(
        name="Cabal of Sorcerers",
        category="Faction",
        faction="Thousand Sons",
        description="At end of Command phase, Thousand Sons Psykers generate Cabal points based on their ability value. "
        "Spend Cabal points to activate Rituals (psychic powers). Pool resets to zero at start of your next Command phase.",
        phase="Command",
    ),
    # ========== FACTION RULES - XENOS ==========
    Rule(
        name="Reanimation Protocols",
        category="Faction",
        faction="Necrons",
        description="At end of your turn, for each destroyed model in Necrons units, roll D6. "
        "On 5+, return that model to the unit with 1 wound remaining. Represents Necron self-repair technology.",
        phase="Command",
    ),
    Rule(
        name="Command Protocols",
        category="Faction",
        faction="Necrons",
        description="At start of Command phase, select one Command Protocol to be active (cannot repeat until all used). "
        'Affects all Necrons units within 6" of a Noble. Protocols provide various battlefield bonuses.',
        phase="Command",
    ),
    Rule(
        name="Waaagh!",
        category="Faction",
        faction="Orks",
        description="Once per battle in your Command phase, declare Waaagh! Until start of next turn, "
        "Ork units can Advance and still Charge, and melee weapons get +1 Attacks. Represents Ork battle frenzy.",
        phase="Command",
    ),
    Rule(
        name="Mob Rule",
        category="Faction",
        faction="Orks",
        description='Ork units within 6" of 10 or more friendly Ork models automatically pass Battle-shock tests. '
        "When there's enough boyz around, Orks never run away - they're too busy having fun!",
        phase="Command",
    ),
    Rule(
        name="Synapse",
        category="Faction",
        faction="Tyranids",
        description='Tyranid units within 6" of a Synapse creature automatically pass Battle-shock tests and can use '
        "Synapse abilities from their datasheets. Represents the Hive Mind's control over the swarm.",
        phase="Any",
    ),
    Rule(
        name="Shadow in the Warp",
        category="Faction",
        faction="Tyranids",
        description='Enemy Psykers within 12" of Tyranid units subtract 1 from Psychic tests. '
        "Represents the psychic interference created by the Hive Mind's presence.",
        phase="Any",
    ),
    Rule(
        name="Strands of Fate",
        category="Faction",
        faction="Aeldari",
        description="Gain Fate dice at start of game and during battle. Before making any dice roll, "
        "can substitute one die with a Fate die of chosen value. Represents Aeldari foresight and divination.",
        phase="Any",
    ),
    Rule(
        name="Power from Pain",
        category="Faction",
        faction="Drukhari",
        description="Gain Pain tokens at battle start and when destroying enemy units. At start of any phase, "
        'spend Pain tokens to make one unit Empowered until end of phase (gains Pain ability bonuses like re-rolls, auto-Advance 8", etc.).',
        phase="Any",
    ),
    Rule(
        name="For the Greater Good",
        category="Faction",
        faction="Tau",
        description="When enemy declares charge against T'au unit, other T'au units within 6\" can fire Supporting Fire "
        "at charging unit (hit only on 6s). Fire Overwatch even if not the target of charge. Cannot be used by units within Engagement Range.",
        phase="Charge",
    ),
    Rule(
        name="Markerlights",
        category="Faction",
        faction="Tau",
        description="When shooting with markerlight weapon, place markerlight token on hit target unit instead of rolling to wound. "
        "Friendly T'au units get +1 to Hit rolls against marked targets until end of phase.",
        phase="Shooting",
    ),
    Rule(
        name="Cult Ambush",
        category="Faction",
        faction="Genestealer Cults",
        description="Gain Resurgence points based on battle size. When unit destroyed, spend points to return identical unit "
        "to Cult Ambush (arrives as Reinforcements with Sustained Hits 1 and Ignores Cover until end of next Fight phase).",
        phase="Movement",
    ),
    Rule(
        name="Judgement Tokens",
        category="Faction",
        faction="Leagues of Votann",
        description="When enemy destroys Votann unit, that enemy gains 1 Judgement token (max 2). When targeting units with tokens, "
        "get +1 to Hit (1 token) or +1 to Hit and +1 to Wound (2 tokens). Represents Kin marking priority targets for vengeance.",
        phase="Any",
    ),
]


# Stratagems database organized by faction
STRATAGEMS_DATABASE: List[Stratagem] = [
    # Space Marines
    Stratagem(
        name="Armour of Contempt",
        faction="Space Marines",
        cost=1,
        type="Battle Tactic",
        when="Opponent's Shooting or Fight phase, just after enemy selects targets",
        target="One Space Marines unit from your army",
        effect="Improve AP of attacks by 1 (e.g., AP-2 becomes AP-1) against this unit "
        "until end of phase.",
        phase="Shooting",
    ),
    Stratagem(
        name="Rapid Fire",
        faction="Space Marines",
        cost=1,
        type="Strategic Ploy",
        when="Your Shooting phase",
        target="One Space Marines Infantry unit",
        effect='Bolt weapons in this unit have Range increased by 6" and gain Sustained '
        "Hits 1 until end of phase.",
        phase="Shooting",
    ),
    Stratagem(
        name="Honour the Chapter",
        faction="Space Marines",
        cost=2,
        type="Epic Deed",
        when="Your Fight phase, just after a Space Marines unit fights",
        target="That unit",
        effect="That unit can fight again. This cannot be used on a unit that has "
        "already fought twice this phase.",
        phase="Fight",
    ),
    Stratagem(
        name="Orbital Strike",
        faction="Space Marines",
        cost=2,
        type="Strategic Ploy",
        when="Your Shooting phase",
        target="One enemy unit",
        effect="Roll 6D6 if unit is visible to a Space Marines Character. For each 4+, "
        "that unit suffers 1 mortal wound.",
        phase="Shooting",
    ),
    # Chaos Space Marines
    Stratagem(
        name="Let the Galaxy Burn",
        faction="Chaos Space Marines",
        cost=1,
        type="Battle Tactic",
        when="Your Shooting phase",
        target="One Chaos Space Marines unit",
        effect="Weapons in that unit gain +1 to Wound rolls until end of phase.",
        phase="Shooting",
    ),
    Stratagem(
        name="Veterans of the Long War",
        faction="Chaos Space Marines",
        cost=1,
        type="Battle Tactic",
        when="Your Shooting or Fight phase",
        target="One Chaos Space Marines unit",
        effect="+1 to Hit and Wound rolls against Imperium units until end of phase.",
        phase="Shooting",
    ),
    Stratagem(
        name="Warp-Sight Plea",
        faction="Chaos Space Marines",
        cost=1,
        type="Epic Deed",
        when="Your Command phase",
        target="One Chaos Space Marines Psyker",
        effect="That Psyker can attempt to manifest one additional psychic power this "
        "phase but suffers D3 mortal wounds.",
        phase="Command",
    ),
    # Necrons
    Stratagem(
        name="Resurrection Protocols",
        faction="Necrons",
        cost=1,
        type="Epic Deed",
        when="End of your Command phase",
        target="One Necrons unit from your army",
        effect="Return D3 destroyed models to that unit with full wounds. If a "
        "Character, return with D3 wounds.",
        phase="Command",
    ),
    Stratagem(
        name="Adaptive Subroutines",
        faction="Necrons",
        cost=1,
        type="Battle Tactic",
        when="Your Shooting or Fight phase",
        target="One Necrons unit",
        effect="Re-roll Hit rolls of 1 and re-roll Wound rolls of 1 until end of phase.",
        phase="Shooting",
    ),
    Stratagem(
        name="Disruption Fields",
        faction="Necrons",
        cost=1,
        type="Wargear",
        when="Your Fight phase",
        target="One Necrons unit",
        effect="Melee weapons in this unit gain +1 Strength and AP-1 until end of phase.",
        phase="Fight",
    ),
    Stratagem(
        name="Quantum Shielding",
        faction="Necrons",
        cost=2,
        type="Wargear",
        when="Opponent's Shooting phase",
        target="One Necrons Vehicle",
        effect="Halve Damage (rounding up) from attacks against this model until end "
        "of phase.",
        phase="Shooting",
    ),
    # Orks
    Stratagem(
        name="Mob Up",
        faction="Orks",
        cost=1,
        type="Strategic Ploy",
        when="End of your Movement phase",
        target='Two Ork Infantry units within 2" of each other',
        effect="Merge both units into one. Combined unit gains benefits of larger mob.",
        phase="Movement",
    ),
    Stratagem(
        name="Da Jump",
        faction="Orks",
        cost=1,
        type="Strategic Ploy",
        when="Your Movement phase",
        target="One Ork Infantry unit",
        effect='Remove unit from battlefield and set up anywhere more than 9" from '
        "enemy models. Counts as Remaining Stationary.",
        phase="Movement",
    ),
    Stratagem(
        name="Get Stuck In",
        faction="Orks",
        cost=1,
        type="Battle Tactic",
        when="Your Fight phase",
        target="One Ork unit that charged this turn",
        effect="Melee weapons gain +1 to Wound and +1 Attack until end of phase.",
        phase="Fight",
    ),
    Stratagem(
        name="More Dakka",
        faction="Orks",
        cost=1,
        type="Battle Tactic",
        when="Your Shooting phase",
        target="One Ork unit",
        effect="Ranged weapons gain Sustained Hits 1 until end of phase.",
        phase="Shooting",
    ),
    # Tyranids
    Stratagem(
        name="Endless Swarm",
        faction="Tyranids",
        cost=2,
        type="Epic Deed",
        when="Your Command phase",
        target="One destroyed Tyranids unit with models that cost 25pts or less",
        effect="Return that unit to Strategic Reserves with half starting strength "
        "(rounding up).",
        phase="Command",
    ),
    Stratagem(
        name="Synaptic Channeling",
        faction="Tyranids",
        cost=1,
        type="Battle Tactic",
        when="Your Shooting or Fight phase",
        target="One Tyranids unit within Synapse",
        effect="That unit can re-roll all Hit rolls and Wound rolls until end of phase.",
        phase="Shooting",
    ),
    Stratagem(
        name="Metabolic Overdrive",
        faction="Tyranids",
        cost=1,
        type="Strategic Ploy",
        when="Your Movement phase",
        target="One Tyranids unit",
        effect='That unit can Advance and still Shoot and Charge this turn. +2" to '
        "Advance and Charge rolls.",
        phase="Movement",
    ),
    # Aeldari
    Stratagem(
        name="Bladestorm",
        faction="Aeldari",
        cost=1,
        type="Battle Tactic",
        when="Your Shooting phase",
        target="One Aeldari unit",
        effect="Shuriken weapons in this unit gain Sustained Hits 1 and Lethal Hits "
        "until end of phase.",
        phase="Shooting",
    ),
    Stratagem(
        name="Lightning-Fast Reactions",
        faction="Aeldari",
        cost=1,
        type="Battle Tactic",
        when="Opponent's Shooting or Fight phase",
        target="One Aeldari unit",
        effect="-1 to Hit rolls against this unit and improve invulnerable save by 1 "
        "(e.g., 4++ becomes 3++) until end of phase.",
        phase="Shooting",
    ),
    Stratagem(
        name="Phantasm",
        faction="Aeldari",
        cost=1,
        type="Strategic Ploy",
        when="End of opponent's Movement phase",
        target="One Aeldari unit",
        effect='Remove unit from battlefield and redeploy anywhere more than 6" from '
        "enemy models.",
        phase="Movement",
    ),
    # T'au Empire
    Stratagem(
        name="Focused Fire",
        faction="Tau",
        cost=1,
        type="Battle Tactic",
        when="Your Shooting phase",
        target="One T'au Empire unit",
        effect="Select one enemy unit. This unit's weapons gain +1 to Wound against "
        "that target until end of phase.",
        phase="Shooting",
    ),
    Stratagem(
        name="Kauyon",
        faction="Tau",
        cost=2,
        type="Strategic Ploy",
        when="Your Command phase",
        target="All T'au Empire units within 6\" of a Commander",
        effect="Those units count as Remaining Stationary this turn. +1 to Hit with "
        "ranged weapons.",
        phase="Command",
    ),
    Stratagem(
        name="Mont'ka",
        faction="Tau",
        cost=2,
        type="Strategic Ploy",
        when="Your Movement phase",
        target="All T'au Empire units within 6\" of a Commander",
        effect="Those units can Advance and still Shoot. Ranged weapons gain AP-1 "
        "until end of turn.",
        phase="Movement",
    ),
    # Astra Militarum
    Stratagem(
        name="Fire on My Command",
        faction="Astra Militarum",
        cost=1,
        type="Battle Tactic",
        when="Your Shooting phase",
        target='One Astra Militarum Infantry unit within 6" of an Officer',
        effect="Add 1 to Hit rolls and weapons gain Lethal Hits until end of phase.",
        phase="Shooting",
    ),
    Stratagem(
        name="Fix Bayonets!",
        faction="Astra Militarum",
        cost=1,
        type="Battle Tactic",
        when="Your Fight phase",
        target="One Astra Militarum Infantry unit that charged",
        effect="+1 Attack and +1 to Wound in melee until end of phase.",
        phase="Fight",
    ),
    Stratagem(
        name="Send in the Next Wave",
        faction="Astra Militarum",
        cost=2,
        type="Epic Deed",
        when="Your Command phase",
        target="One destroyed Astra Militarum Infantry unit",
        effect="Return unit to Strategic Reserves with half starting strength. Can "
        "arrive from any battlefield edge.",
        phase="Command",
    ),
    # Adeptus Mechanicus
    Stratagem(
        name="Enriched Rounds",
        faction="Adeptus Mechanicus",
        cost=1,
        type="Wargear",
        when="Your Shooting phase",
        target="One Adeptus Mechanicus unit",
        effect="Ranged weapons equipped by models in that unit gain Lethal Hits until end of phase.",
        phase="Shooting",
    ),
    Stratagem(
        name="Binharic Override",
        faction="Adeptus Mechanicus",
        cost=1,
        type="Strategic Ploy",
        when="Your Command phase",
        target="One Adeptus Mechanicus Vehicle or Monster",
        effect="That model regains D3 lost wounds. If already at full wounds, gains +1 to hit rolls until end of turn.",
        phase="Command",
    ),
    # Drukhari
    Stratagem(
        name="Prey on the Weak",
        faction="Drukhari",
        cost=1,
        type="Battle Tactic",
        when="Your Shooting or Fight phase",
        target="One Drukhari unit",
        effect="Attacks made by this unit get +1 to Wound rolls against targets that are Below Half-strength.",
        phase="Shooting",
    ),
    Stratagem(
        name="Hyperstimm Backlash",
        faction="Drukhari",
        cost=1,
        type="Strategic Ploy",
        when="Your Fight phase",
        target="One Drukhari Infantry unit",
        effect="That unit can fight again, but suffers D3 mortal wounds after fighting.",
        phase="Fight",
    ),
    # Genestealer Cults
    Stratagem(
        name="Lying in Wait",
        faction="Genestealer Cults",
        cost=1,
        type="Strategic Ploy",
        when="Opponent's Movement phase, when enemy unit ends move",
        target='One Genestealer Cults Infantry unit within 9" of that enemy',
        effect="Your unit can shoot at that enemy unit as if it were your Shooting phase.",
        phase="Movement",
    ),
    Stratagem(
        name="A Plan Generations in the Making",
        faction="Genestealer Cults",
        cost=2,
        type="Epic Deed",
        when="Your Command phase",
        target="Your army",
        effect="Gain D3 Resurgence points to add to your pool.",
        phase="Command",
    ),
    # Leagues of Votann
    Stratagem(
        name="Ancestral Judgement",
        faction="Leagues of Votann",
        cost=1,
        type="Battle Tactic",
        when="Your Shooting or Fight phase",
        target="One Leagues of Votann unit",
        effect="Select one enemy unit. That enemy unit gains 1 Judgement token (to a maximum of 2).",
        phase="Shooting",
    ),
    Stratagem(
        name="Void Armour",
        faction="Leagues of Votann",
        cost=1,
        type="Wargear",
        when="Opponent's Shooting or Fight phase",
        target="One Leagues of Votann unit",
        effect="Improve that unit's Save characteristic by 1 (e.g., 3+ becomes 2+) until end of phase.",
        phase="Shooting",
    ),
    # Death Guard
    Stratagem(
        name="Disgusting Force",
        faction="Death Guard",
        cost=1,
        type="Battle Tactic",
        when="Your Fight phase",
        target="One Death Guard unit that made a charge move this turn",
        effect="Melee weapons in this unit gain Lethal Hits until end of phase.",
        phase="Fight",
    ),
    Stratagem(
        name="Shambling Horde",
        faction="Death Guard",
        cost=1,
        type="Strategic Ploy",
        when="Your Movement phase",
        target="One Death Guard Infantry unit",
        effect='That unit can move an additional 3" this phase but cannot Advance.',
        phase="Movement",
    ),
    Stratagem(
        name="Cloud of Flies",
        faction="Death Guard",
        cost=1,
        type="Battle Tactic",
        when="Opponent's Shooting phase",
        target="One Death Guard Infantry unit",
        effect="Ranged attacks against this unit get -1 to Hit until end of phase.",
        phase="Shooting",
    ),
    # World Eaters
    Stratagem(
        name="Rage Unbound",
        faction="World Eaters",
        cost=1,
        type="Battle Tactic",
        when="Your Fight phase",
        target="One World Eaters unit",
        effect="Melee weapons gain +1 Strength until end of phase.",
        phase="Fight",
    ),
    Stratagem(
        name="Skulls for the Skull Throne",
        faction="World Eaters",
        cost=1,
        type="Epic Deed",
        when="Any phase, when a Character model is destroyed by a World Eaters unit",
        target="Your army",
        effect="Roll one extra D6 for your next Blessings of Khorne roll.",
        phase="Any",
    ),
    # Grey Knights
    Stratagem(
        name="Psychic Onslaught",
        faction="Grey Knights",
        cost=1,
        type="Battle Tactic",
        when="Your Shooting phase",
        target="One Grey Knights Psyker unit",
        effect="Ranged weapons gain Devastating Wounds until end of phase.",
        phase="Shooting",
    ),
    Stratagem(
        name="Heed the Prognosticars",
        faction="Grey Knights",
        cost=1,
        type="Strategic Ploy",
        when="Your Command phase",
        target="One Grey Knights unit arriving from Reserves this turn",
        effect='That unit can be set up anywhere more than 6" from enemy models instead of 9".',
        phase="Command",
    ),
    Stratagem(
        name="Purge the Daemon",
        faction="Grey Knights",
        cost=1,
        type="Battle Tactic",
        when="Your Shooting or Fight phase",
        target="One Grey Knights unit",
        effect="Attacks against Daemon units gain +1 to Wound and improve AP by 1 until end of phase.",
        phase="Shooting",
    ),
    # Thousand Sons
    Stratagem(
        name="Sorcerous Facade",
        faction="Thousand Sons",
        cost=1,
        type="Strategic Ploy",
        when="End of your Movement phase",
        target="One Thousand Sons Infantry unit",
        effect='Remove that unit from the battlefield and set it up anywhere wholly within 6" of its previous position and more than 3" from enemy models.',
        phase="Movement",
    ),
    Stratagem(
        name="Wrath of the Wronged",
        faction="Thousand Sons",
        cost=1,
        type="Battle Tactic",
        when="Your Shooting phase",
        target="One Thousand Sons unit",
        effect="Ranged weapons gain +1 to Wound against Imperium units until end of phase.",
        phase="Shooting",
    ),
    # Adepta Sororitas
    Stratagem(
        name="Holy Rage",
        faction="Adepta Sororitas",
        cost=1,
        type="Battle Tactic",
        when="Your Fight phase",
        target="One Adepta Sororitas unit that charged this turn",
        effect="Melee weapons gain +1 to Wound rolls until end of phase.",
        phase="Fight",
    ),
    Stratagem(
        name="Divine Guidance",
        faction="Adepta Sororitas",
        cost=1,
        type="Battle Tactic",
        when="Your Shooting phase",
        target="One Adepta Sororitas unit",
        effect="Bolt weapons and Flamer weapons gain Sustained Hits 1 until end of phase.",
        phase="Shooting",
    ),
    Stratagem(
        name="Purity of Faith",
        faction="Adepta Sororitas",
        cost=1,
        type="Epic Deed",
        when="Any phase",
        target="One Adepta Sororitas Character",
        effect="Roll 2D6 and add both results to your Miracle dice pool.",
        phase="Any",
    ),
    # Adeptus Custodes
    Stratagem(
        name="Sentinel Storm",
        faction="Adeptus Custodes",
        cost=1,
        type="Battle Tactic",
        when="Your Shooting phase",
        target="One Adeptus Custodes unit that Remained Stationary",
        effect="Ranged weapons gain Sustained Hits 1 until end of phase.",
        phase="Shooting",
    ),
    Stratagem(
        name="Arcane Genetic Alchemy",
        faction="Adeptus Custodes",
        cost=1,
        type="Epic Deed",
        when="Any phase, when an Adeptus Custodes model would lose a wound",
        target="That model",
        effect="Roll one D6. On 5+, that wound is not lost.",
        phase="Any",
    ),
    # Imperial Knights
    Stratagem(
        name="Thunderstomp",
        faction="Imperial Knights",
        cost=1,
        type="Battle Tactic",
        when="Your Fight phase",
        target="One Imperial Knights Titanic unit that charged",
        effect="Roll one D6 for each enemy unit within Engagement Range. On 2-5, that unit suffers D3 mortal wounds. On 6, that unit suffers 3 mortal wounds.",
        phase="Fight",
    ),
    Stratagem(
        name="Rotate Ion Shields",
        faction="Imperial Knights",
        cost=1,
        type="Wargear",
        when="Opponent's Shooting phase",
        target="One Imperial Knights model",
        effect="That model has a 4+ invulnerable save against ranged attacks until end of phase.",
        phase="Shooting",
    ),
    Stratagem(
        name="Full Tilt",
        faction="Imperial Knights",
        cost=2,
        type="Strategic Ploy",
        when="Your Charge phase",
        target="One Imperial Knights Titanic unit",
        effect="Add 3 to Charge roll for that unit and improve AP of melee weapons by 1 if charge successful.",
        phase="Charge",
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
