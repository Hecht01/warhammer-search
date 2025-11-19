<script>
  import { onMount } from 'svelte';

  const API_BASE = window.location.origin;

  // Rules state
  let rulesQuery = '';
  let rulesFaction = '';
  let rulesCategory = '';
  let rulesPhase = '';
  let rules = [];
  let factions = [];

  // Stratagems state
  let stratsQuery = '';
  let stratsFaction = '';
  let stratsType = '';
  let stratsCost = '';
  let stratagems = [];

  async function loadRules() {
    try {
      const params = new URLSearchParams();
      if (rulesQuery) params.append('q', rulesQuery);
      if (rulesFaction) params.append('faction', rulesFaction);
      if (rulesCategory) params.append('category', rulesCategory);
      if (rulesPhase) params.append('phase', rulesPhase);

      const response = await fetch(`${API_BASE}/rules?${params.toString()}`);
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);

      rules = await response.json();
    } catch (error) {
      console.error('Rules search error:', error);
      rules = [];
    }
  }

  async function loadStratagems() {
    try {
      const params = new URLSearchParams();
      if (stratsQuery) params.append('q', stratsQuery);
      if (stratsFaction) params.append('faction', stratsFaction);
      if (stratsType) params.append('type', stratsType);
      if (stratsCost) params.append('max_cost', stratsCost);

      const response = await fetch(`${API_BASE}/stratagems?${params.toString()}`);
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);

      stratagems = await response.json();
    } catch (error) {
      console.error('Stratagems search error:', error);
      stratagems = [];
    }
  }

  async function loadFactions() {
    try {
      const response = await fetch(`${API_BASE}/factions`);
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);

      factions = await response.json();
    } catch (error) {
      console.error('Error loading factions:', error);
    }
  }

  function handleRulesKeyPress(event) {
    if (event.key === 'Enter') loadRules();
  }

  function handleStratsKeyPress(event) {
    if (event.key === 'Enter') loadStratagems();
  }

  onMount(() => {
    loadFactions();
    loadRules();
    loadStratagems();
  });

  $: if (rulesFaction || rulesCategory || rulesPhase) loadRules();
  $: if (stratsFaction || stratsType || stratsCost) loadStratagems();
</script>

<div class="rules-sections">
  <!-- Rules Section -->
  <div class="rules-section">
    <h3>Game Rules</h3>
    <div class="search-box">
      <input
        type="text"
        bind:value={rulesQuery}
        on:keypress={handleRulesKeyPress}
        placeholder="Search rules..."
        autocomplete="off"
      />
      <button on:click={loadRules}>Search</button>
    </div>

    <div class="filters">
      <label for="rules-faction-filter">Faction:</label>
      <select id="rules-faction-filter" bind:value={rulesFaction}>
        <option value="">All (Core + Faction Rules)</option>
        {#each factions as faction}
          <option value={faction}>{faction}</option>
        {/each}
      </select>

      <label for="rules-category-filter">Category:</label>
      <select id="rules-category-filter" bind:value={rulesCategory}>
        <option value="">All Categories</option>
        <option value="Core Rules">Core Rules</option>
        <option value="Faction">Faction Rules</option>
      </select>

      <label for="rules-phase-filter">Phase:</label>
      <select id="rules-phase-filter" bind:value={rulesPhase}>
        <option value="">All Phases</option>
        <option value="Command">Command</option>
        <option value="Movement">Movement</option>
        <option value="Shooting">Shooting</option>
        <option value="Charge">Charge</option>
        <option value="Fight">Fight</option>
        <option value="Morale">Morale</option>
      </select>
    </div>

    <div class="rules-results">
      {#if rules.length === 0}
        <div class="no-results">No rules found.</div>
      {:else}
        {#each rules as rule}
          <div class="rule-card">
            <div class="rule-name">{rule.name}</div>
            <span class="rule-category">{rule.category}</span>
            {#if rule.phase}
              <span class="rule-phase">{rule.phase} Phase</span>
            {/if}
            {#if rule.faction}
              <div class="rule-faction">Faction: {rule.faction}</div>
            {/if}
            <div class="rule-description">{rule.description}</div>
          </div>
        {/each}
      {/if}
    </div>
  </div>

  <!-- Stratagems Section -->
  <div class="rules-section">
    <h3>Stratagems</h3>
    <div class="search-box">
      <input
        type="text"
        bind:value={stratsQuery}
        on:keypress={handleStratsKeyPress}
        placeholder="Search stratagems..."
        autocomplete="off"
      />
      <button on:click={loadStratagems}>Search</button>
    </div>

    <div class="filters">
      <label for="strats-faction-filter">Faction:</label>
      <select id="strats-faction-filter" bind:value={stratsFaction}>
        <option value="">All Factions</option>
        {#each factions as faction}
          <option value={faction}>{faction}</option>
        {/each}
      </select>

      <label for="strats-type-filter">Type:</label>
      <select id="strats-type-filter" bind:value={stratsType}>
        <option value="">All Types</option>
        <option value="Battle Tactic">Battle Tactic</option>
        <option value="Strategic Ploy">Strategic Ploy</option>
        <option value="Epic Deed">Epic Deed</option>
        <option value="Wargear">Wargear</option>
      </select>

      <label for="strats-cost-filter">Max CP:</label>
      <select id="strats-cost-filter" bind:value={stratsCost}>
        <option value="">Any Cost</option>
        <option value="1">1 CP</option>
        <option value="2">2 CP</option>
        <option value="3">3 CP</option>
      </select>
    </div>

    <div class="strats-results">
      {#if stratagems.length === 0}
        <div class="no-results">No stratagems found.</div>
      {:else}
        {#each stratagems as strat}
          <div class="strat-card">
            <div class="strat-name">{strat.name}</div>
            <span class="strat-cost">{strat.cost} CP</span>
            <span class="strat-type">{strat.type}</span>
            {#if strat.phase}
              <span class="strat-phase">{strat.phase} Phase</span>
            {/if}
            <div class="strat-faction">Faction: {strat.faction}</div>
            <div class="strat-when"><strong>When:</strong> {strat.when}</div>
            <div class="strat-target"><strong>Target:</strong> {strat.target}</div>
            <div class="strat-effect"><strong>Effect:</strong> {strat.effect}</div>
          </div>
        {/each}
      {/if}
    </div>
  </div>
</div>
