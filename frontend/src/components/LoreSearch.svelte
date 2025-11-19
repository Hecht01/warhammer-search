<script>
  const API_BASE = window.location.origin;

  let query = '';
  let limit = 10;
  let loading = false;
  let results = [];

  async function performSearch() {
    if (!query.trim()) {
      results = [];
      return;
    }

    loading = true;
    try {
      const response = await fetch(`${API_BASE}/search?q=${encodeURIComponent(query)}&limit=${limit}`);
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);

      results = await response.json();
    } catch (error) {
      console.error('Search error:', error);
      results = [];
    } finally {
      loading = false;
    }
  }

  function handleKeyPress(event) {
    if (event.key === 'Enter') {
      performSearch();
    }
  }

  function highlightQuery(text) {
    if (!query) return text;

    const words = query.split(/\s+/).filter(w => w.length > 2);
    let highlighted = text;

    words.forEach(word => {
      const regex = new RegExp(`(${word.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
      highlighted = highlighted.replace(regex, '<span class="highlight">$1</span>');
    });

    return highlighted;
  }
</script>

<div class="search-box">
  <input
    type="text"
    bind:value={query}
    on:keypress={handleKeyPress}
    placeholder="Search the grimdark lore... (e.g., Emperor, Necrons, Horus Heresy)"
    autocomplete="off"
  />
  <button on:click={performSearch}>Search</button>
</div>

<div class="filters">
  <label for="result-limit">Results:</label>
  <select id="result-limit" bind:value={limit}>
    <option value={5}>5</option>
    <option value={10}>10</option>
    <option value={20}>20</option>
    <option value={50}>50</option>
  </select>
</div>

{#if loading}
  <div class="loading">
    <div class="spinner"></div>
    <p>Consulting the Emperor's Tarot...</p>
  </div>
{/if}

<div class="results">
  {#if !loading && results.length === 0 && query}
    <div class="no-results">No results found. The Emperor protects... but not your search query.</div>
  {:else}
    {#each results as result, index}
      <div class="result-card">
        <div class="result-header">
          <span style="color: var(--text-secondary);">Result {index + 1}</span>
          <span class="result-score">{(result.score * 100).toFixed(1)}% match</span>
        </div>
        <div class="result-text">{@html highlightQuery(result.text)}</div>
      </div>
    {/each}
  {/if}
</div>
