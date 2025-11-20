<script>
  import { onMount } from 'svelte';

  const API_BASE = window.location.origin;

  let factions = [];
  let selectedFaction = null;
  let factionDetails = null;
  let loading = false;

  const FACTION_SUMMARIES = {
    'Space Marines': 'The Angels of Death - genetically enhanced super-soldiers created by the Emperor to defend humanity. Organized into Chapters of 1000 warriors, they are the Imperium\'s finest.',
    'Chaos': 'Dark forces that worship the Ruinous Powers. Corrupted souls who have turned from the Emperor\'s light to serve the Dark Gods of the Warp.',
    'Chaos Space Marines': 'Traitor Legions who betrayed the Emperor during the Horus Heresy. Once noble Space Marines, now damned servants of Chaos.',
    'Necrons': 'Ancient robotic warriors who ruled the galaxy millions of years ago. Now awakening from their tomb worlds to reclaim their empire.',
    'Orks': 'Green-skinned barbarous aliens driven by an instinctive love of violence and war. The more they fight, the stronger they become.',
    'Tyranids': 'Extra-galactic bio-horrors that devour all biomass in their path. A hive mind controlling countless horrors from beyond the galaxy.',
    'Aeldari': 'Ancient and sophisticated aliens whose empire once spanned the galaxy. Now a dying race fighting for survival.',
    'T\'au Empire': 'Young and technologically advanced xenos race united under the philosophy of the Greater Good.',
    'Astra Militarum': 'The Imperial Guard - countless billions of human soldiers defending the Imperium with faith, courage, and sheer numbers.',
    'Adeptus Mechanicus': 'Tech-priests of Mars who worship the Machine God. Keepers of ancient technology and knowledge.',
    'Imperium': 'The Imperium of Man - a galaxy-spanning empire of one million worlds, ruled by the undying God-Emperor.',
    'Genestealer Cults': 'Insidious cults that worship the Tyranid hive mind, preparing worlds for consumption from within.',
    'Drukhari': 'Dark Kin - sadistic raiders who feed on suffering. Pirates and slavers from the dark city of Commorragh.',
    'Adepta Sororitas': 'The Sisters of Battle - fanatical warriors of faith who serve the Emperor with bolter and flamer.',
    'Leagues of Votann': 'Abhuman descendants of ancient human colonies. Resilient miners and traders known as Squats.'
  };

  async function loadFactions() {
    try {
      const response = await fetch(`${API_BASE}/factions`);
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      factions = await response.json();
    } catch (error) {
      console.error('Error loading factions:', error);
    }
  }

  async function selectFaction(faction) {
    selectedFaction = faction;
    loading = true;
    factionDetails = null;

    try {
      const [booksRes, rulesRes, stratsRes] = await Promise.all([
        fetch(`${API_BASE}/books?faction=${encodeURIComponent(faction)}`),
        fetch(`${API_BASE}/rules?faction=${encodeURIComponent(faction)}`),
        fetch(`${API_BASE}/stratagems?faction=${encodeURIComponent(faction)}`)
      ]);

      const books = await booksRes.json();
      const rules = await rulesRes.json();
      const stratagems = await stratsRes.json();

      factionDetails = { books, rules, stratagems };
    } catch (error) {
      console.error(`Error loading data for ${faction}:`, error);
    } finally {
      loading = false;
    }
  }

  function backToList() {
    selectedFaction = null;
    factionDetails = null;
  }

  onMount(() => {
    loadFactions();
  });
</script>

{#if !selectedFaction}
  <h3 style="text-align: center; margin-bottom: 30px; color: var(--accent-gold);">
    Browse by Faction
  </h3>

  <div class="faction-cards">
    {#each factions as faction}
      <button
        class="faction-card"
        on:click={() => selectFaction(faction)}
        role="button"
        tabindex="0"
        on:keypress={(e) => e.key === 'Enter' && selectFaction(faction)}
      >
        <div class="faction-name">{faction}</div>
        <div class="faction-hint">Click to view details</div>
      </button>
    {/each}
  </div>
{:else}
  <div class="faction-detail">
    <button class="back-button" on:click={backToList}>
      ← Back to Factions
    </button>

    <h2 class="faction-title">{selectedFaction}</h2>

    {#if FACTION_SUMMARIES[selectedFaction]}
      <div class="faction-summary">
        {FACTION_SUMMARIES[selectedFaction]}
      </div>
    {/if}

    {#if loading}
      <div class="loading">
        <div class="spinner"></div>
        <p>Loading faction data...</p>
      </div>
    {:else if factionDetails}
      <div class="faction-content">
        <!-- Books Section -->
        <div class="content-section">
          <h3>Books ({factionDetails.books.length})</h3>
          {#if factionDetails.books.length > 0}
            <div class="content-grid">
              {#each factionDetails.books as book}
                <div class="content-card">
                  <div class="content-card-title">{book.title}</div>
                  <div class="content-card-subtitle">by {book.author}</div>
                  {#if book.series}
                    <div class="content-card-meta">Series: {book.series}</div>
                  {/if}
                  {#if book.era}
                    <div class="content-card-meta">Era: {book.era}</div>
                  {/if}
                  {#if book.synopsis}
                    <div class="content-card-desc">{book.synopsis}</div>
                  {/if}
                </div>
              {/each}
            </div>
          {:else}
            <p class="no-content">No books available for this faction.</p>
          {/if}
        </div>

        <!-- Rules Section -->
        <div class="content-section">
          <h3>Rules ({factionDetails.rules.length})</h3>
          {#if factionDetails.rules.length > 0}
            <div class="content-grid">
              {#each factionDetails.rules as rule}
                <div class="content-card">
                  <div class="content-card-title">{rule.name}</div>
                  {#if rule.phase}
                    <div class="content-card-meta">Phase: {rule.phase}</div>
                  {/if}
                  <div class="content-card-desc">{rule.description}</div>
                </div>
              {/each}
            </div>
          {:else}
            <p class="no-content">No faction-specific rules available.</p>
          {/if}
        </div>

        <!-- Stratagems Section -->
        <div class="content-section">
          <h3>Stratagems ({factionDetails.stratagems.length})</h3>
          {#if factionDetails.stratagems.length > 0}
            <div class="content-grid">
              {#each factionDetails.stratagems as strat}
                <div class="content-card stratagem-card">
                  <div class="content-card-title">
                    {strat.name}
                    <span class="cp-cost">{strat.cost} CP</span>
                  </div>
                  <div class="content-card-meta">{strat.type}</div>
                  {#if strat.phase}
                    <div class="content-card-meta">Phase: {strat.phase}</div>
                  {/if}
                  <div class="stratagem-detail"><strong>When:</strong> {strat.when}</div>
                  <div class="stratagem-detail"><strong>Target:</strong> {strat.target}</div>
                  <div class="stratagem-detail"><strong>Effect:</strong> {strat.effect}</div>
                </div>
              {/each}
            </div>
          {:else}
            <p class="no-content">No stratagems available for this faction.</p>
          {/if}
        </div>
      </div>
    {/if}
  </div>
{/if}

<style>
  .faction-detail {
    max-width: 1200px;
    margin: 0 auto;
  }

  .back-button {
    background: var(--bg-medium);
    color: var(--accent-gold);
    border: 1px solid var(--border-color);
    padding: 10px 20px;
    cursor: pointer;
    margin-bottom: 20px;
    font-size: 16px;
    transition: all 0.2s;
  }

  .back-button:hover {
    background: var(--bg-dark);
    border-color: var(--accent-gold);
  }

  .faction-title {
    text-align: center;
    color: var(--accent-gold);
    font-size: 2.5em;
    margin: 20px 0;
    text-transform: uppercase;
    letter-spacing: 2px;
  }

  .faction-summary {
    background: var(--bg-medium);
    border-left: 4px solid var(--accent-gold);
    padding: 20px;
    margin: 20px 0;
    font-size: 1.1em;
    line-height: 1.6;
    font-style: italic;
  }

  .faction-content {
    margin-top: 30px;
  }

  .content-section {
    margin-bottom: 40px;
  }

  .content-section h3 {
    color: var(--accent-gold);
    font-size: 1.8em;
    margin-bottom: 15px;
    border-bottom: 2px solid var(--border-color);
    padding-bottom: 10px;
  }

  .content-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 15px;
  }

  .content-card {
    background: var(--bg-medium);
    border: 1px solid var(--border-color);
    padding: 15px;
    transition: all 0.3s;
  }

  .content-card:hover {
    border-color: var(--accent-gold);
    box-shadow: 0 0 15px rgba(184, 134, 11, 0.3);
  }

  .content-card-title {
    color: var(--accent-gold);
    font-size: 1.2em;
    font-weight: bold;
    margin-bottom: 8px;
  }

  .content-card-subtitle {
    color: var(--text-secondary);
    margin-bottom: 8px;
  }

  .content-card-meta {
    color: var(--text-secondary);
    font-size: 0.9em;
    margin-bottom: 5px;
  }

  .content-card-desc {
    color: var(--text-color);
    margin-top: 10px;
    line-height: 1.5;
  }

  .stratagem-card .cp-cost {
    float: right;
    background: var(--accent-gold);
    color: #000;
    padding: 3px 8px;
    font-size: 0.9em;
    font-weight: bold;
  }

  .stratagem-detail {
    margin-top: 8px;
    line-height: 1.5;
  }

  .no-content {
    color: var(--text-secondary);
    font-style: italic;
    text-align: center;
    padding: 20px;
  }

  .faction-hint {
    color: var(--text-secondary);
    font-size: 0.9em;
    margin-top: 5px;
  }

  .faction-card {
    cursor: pointer;
    background: none;
    border: none;
    width: 100%;
    text-align: left;
  }
</style>
