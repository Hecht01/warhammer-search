<script>
  import { onMount } from 'svelte';

  export let activeTab;

  const API_BASE = window.location.origin;

  let factions = [];
  let factionData = {};

  async function loadFactions() {
    try {
      const response = await fetch(`${API_BASE}/factions`);
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);

      factions = await response.json();

      // Load data for each faction
      for (const faction of factions) {
        await loadFactionData(faction);
      }
    } catch (error) {
      console.error('Error loading factions:', error);
    }
  }

  async function loadFactionData(faction) {
    try {
      const [booksRes, rulesRes, stratsRes] = await Promise.all([
        fetch(`${API_BASE}/books?faction=${encodeURIComponent(faction)}`),
        fetch(`${API_BASE}/rules?faction=${encodeURIComponent(faction)}`),
        fetch(`${API_BASE}/stratagems?faction=${encodeURIComponent(faction)}`)
      ]);

      const books = await booksRes.json();
      const rules = await rulesRes.json();
      const stratagems = await stratsRes.json();

      factionData[faction] = { books, rules, stratagems };
      factionData = factionData; // Trigger reactivity
    } catch (error) {
      console.error(`Error loading data for ${faction}:`, error);
    }
  }

  function selectFaction(faction) {
    activeTab = 'rules';
    // Give the UI time to switch tabs, then dispatch custom event
    setTimeout(() => {
      window.dispatchEvent(new CustomEvent('selectFaction', { detail: faction }));
    }, 100);
  }

  onMount(() => {
    loadFactions();
  });
</script>

<h3 style="text-align: center; margin-bottom: 30px; color: var(--accent-gold);">
  Browse by Faction
</h3>

<div class="faction-cards">
  {#each factions as faction}
    <div class="faction-card" on:click={() => selectFaction(faction)}>
      <div class="faction-name">{faction}</div>
      {#if factionData[faction]}
        <div class="faction-counts">
          <div class="faction-count-item">Books: {factionData[faction].books.length}</div>
          <div class="faction-count-item">Rules: {factionData[faction].rules.length}</div>
          <div class="faction-count-item">Stratagems: {factionData[faction].stratagems.length}</div>
        </div>
      {:else}
        <div class="faction-counts">
          <div class="faction-count-item">Loading...</div>
        </div>
      {/if}
    </div>
  {/each}
</div>
