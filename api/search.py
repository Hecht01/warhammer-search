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


# Rules database with core rules and faction-specific rules
RULES_DATABASE: List[Rule] = [
    # Core Rules
    Rule(
        name="Move",
        category="Core Rules",
        description="Units can move up to their Move (M) characteristic in inches. "
        "They cannot move within Engagement Range of enemy models.",
        phase="Movement",
    ),
    Rule(
        name="Advance",
        category="Core Rules",
        description="Instead of moving normally, a unit can Advance. Roll D6 and add "
        "to Move characteristic. Cannot shoot (except Assault weapons) or charge.",
        phase="Movement",
    ),
    Rule(
        name="Fall Back",
        category="Core Rules",
        description="Units within Engagement Range can Fall Back instead of making "
        "a Normal Move. Cannot shoot or charge this turn (unless they can FLY).",
        phase="Movement",
    ),
    Rule(
        name="Shooting",
        category="Core Rules",
        description="Select targets, roll to hit, roll to wound, allocate wounds, "
        "make saving throws. Cannot shoot if within Engagement Range of enemy.",
        phase="Shooting",
    ),
    Rule(
        name="Ballistic Skill",
        category="Core Rules",
        description="To hit in shooting, roll D6. If result equals or exceeds the "
        "model's BS characteristic, it hits. Modified by range and modifiers.",
        phase="Shooting",
    ),
    Rule(
        name="Weapon Skill",
        category="Core Rules",
        description="To hit in melee, roll D6. If result equals or exceeds the "
        "model's WS characteristic, it hits.",
        phase="Fight",
    ),
    Rule(
        name="Charge",
        category="Core Rules",
        description="Roll 2D6. Unit can move that many inches toward enemy unit. "
        "Must end within Engagement Range to make charge successful.",
        phase="Charge",
    ),
    Rule(
        name="Fight",
        category="Core Rules",
        description="Select targets, make attacks, allocate wounds. Units fight if "
        "within Engagement Range or made a charge move this turn.",
        phase="Fight",
    ),
    Rule(
        name="Morale Test",
        category="Core Rules",
        description="Roll D6 and add models lost this turn. If total exceeds highest "
        "Ld in unit, one model flees for each point exceeded.",
        phase="Morale",
    ),
    Rule(
        name="Cover",
        category="Core Rules",
        description="Models fully within terrain feature gain +1 to saving throw "
        "against ranged attacks (excluding invulnerable saves).",
        phase="Shooting",
    ),
    Rule(
        name="Invulnerable Save",
        category="Core Rules",
        description="Special save that can be made instead of normal save. Never "
        "modified by AP. Typically 4++, 5++, or 6++.",
        phase=None,
    ),
    Rule(
        name="Feel No Pain",
        category="Core Rules",
        description="After a model loses a wound, roll D6. On specified value (usually "
        "5+ or 6+), that wound is ignored.",
        phase=None,
    ),
    # Space Marines Faction Rules
    Rule(
        name="Oath of Moment",
        category="Faction",
        faction="Space Marines",
        description="At start of your Command phase, select one enemy unit. Your units "
        "get +1 to Hit rolls targeting that unit until start of your next Command phase.",
        phase="Command",
    ),
    Rule(
        name="And They Shall Know No Fear",
        category="Faction",
        faction="Space Marines",
        description="You can re-roll Battle-shock and Leadership tests for Space Marine "
        "units from your army.",
        phase="Morale",
    ),
    # Chaos Space Marines
    Rule(
        name="Dark Pacts",
        category="Faction",
        faction="Chaos Space Marines",
        description="Once per battle, you can make a Dark Pact before making a Hit, "
        "Wound, or Damage roll. Re-roll result, but take D3 mortal wounds after.",
        phase=None,
    ),
    # Necrons
    Rule(
        name="Reanimation Protocols",
        category="Faction",
        faction="Necrons",
        description="At end of your turn, roll D6 for each destroyed model in Necron "
        "units. On 5+, return that model to unit with 1 wound remaining.",
        phase="Command",
    ),
    Rule(
        name="Command Protocols",
        category="Faction",
        faction="Necrons",
        description="At start of Command phase, select one protocol to be active. "
        'Affects all Necron units within 6" of a Character.',
        phase="Command",
    ),
    # Orks
    Rule(
        name="Waaagh!",
        category="Faction",
        faction="Orks",
        description="Once per battle, call Waaagh! in Command phase. Until start of "
        "next turn, Ork units can charge after Advancing and get +1 Attack.",
        phase="Command",
    ),
    Rule(
        name="Mob Rule",
        category="Faction",
        faction="Orks",
        description='Ork units within 6" of 10+ friendly Ork models automatically '
        "pass Battle-shock tests.",
        phase="Morale",
    ),
    # Tyranids
    Rule(
        name="Synapse",
        category="Faction",
        faction="Tyranids",
        description='Tyranid units within 6" of a Synapse creature automatically pass '
        "Battle-shock tests and can use Synapse abilities.",
        phase=None,
    ),
    Rule(
        name="Shadow in the Warp",
        category="Faction",
        faction="Tyranids",
        description='Enemy Psykers within 12" of Tyranid units subtract 1 from '
        "Psychic tests and suffer Perils on any double.",
        phase=None,
    ),
    # Aeldari
    Rule(
        name="Strands of Fate",
        category="Faction",
        faction="Aeldari",
        description="Gain Fate dice at start of game. Can substitute any dice roll "
        "with Fate dice. Represents Eldar foresight.",
        phase=None,
    ),
    # T'au Empire
    Rule(
        name="For the Greater Good",
        category="Faction",
        faction="Tau",
        description="Units can make Supporting Fire when friendly unit is charged "
        'within 6". Fire Overwatch at BS 5+ even if not target of charge.',
        phase="Charge",
    ),
    Rule(
        name="Markerlights",
        category="Faction",
        faction="Tau",
        description="When shooting with markerlight, place token on enemy unit. "
        "Friendly T'au units gain +1 to hit that target until end of phase.",
        phase="Shooting",
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
