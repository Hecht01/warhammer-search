<script>
  import { onMount } from 'svelte';

  const API_BASE = window.location.origin;

  let query = '';
  let factionFilter = '';
  let eraFilter = '';
  let books = [];

  async function loadBooks() {
    try {
      const params = new URLSearchParams();
      if (query) params.append('q', query);
      if (factionFilter) params.append('faction', factionFilter);
      if (eraFilter) params.append('era', eraFilter);

      const response = await fetch(`${API_BASE}/books?${params.toString()}`);
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);

      books = await response.json();
    } catch (error) {
      console.error('Books search error:', error);
      books = [];
    }
  }

  function handleKeyPress(event) {
    if (event.key === 'Enter') {
      loadBooks();
    }
  }

  onMount(() => {
    loadBooks();
  });

  $: if (factionFilter || eraFilter) loadBooks();
</script>

<div class="search-box">
  <input
    type="text"
    bind:value={query}
    on:keypress={handleKeyPress}
    placeholder="Search books by title, author, or faction..."
    autocomplete="off"
  />
  <button on:click={loadBooks}>Search Books</button>
</div>

<div class="filters">
  <label for="faction-filter">Faction:</label>
  <select id="faction-filter" bind:value={factionFilter}>
    <option value="">All Factions</option>
    <option value="Space Marines">Space Marines</option>
    <option value="Imperium">Imperium</option>
    <option value="Chaos">Chaos</option>
    <option value="Chaos Space Marines">Chaos Space Marines</option>
    <option value="Necrons">Necrons</option>
    <option value="Aeldari">Aeldari</option>
    <option value="Tau">T'au Empire</option>
    <option value="Orks">Orks</option>
    <option value="Tyranids">Tyranids</option>
    <option value="Genestealer Cults">Genestealer Cults</option>
    <option value="Adeptus Mechanicus">Adeptus Mechanicus</option>
    <option value="Astra Militarum">Astra Militarum</option>
  </select>

  <label for="era-filter">Era:</label>
  <select id="era-filter" bind:value={eraFilter}>
    <option value="">All Eras</option>
    <option value="30K">Horus Heresy (30K)</option>
    <option value="40K">40K</option>
    <option value="41K">Era Indomitus (41K+)</option>
  </select>
</div>

<div class="books-results">
  {#if books.length === 0}
    <div class="no-results">No books found matching your criteria.</div>
  {:else}
    {#each books as book}
      <div class="book-card">
        <div class="book-title">{book.title}</div>
        <div class="book-author">by {book.author}</div>
        {#if book.series}
          <div class="book-series">Series: {book.series}</div>
        {/if}
        <div class="book-factions">
          {#each book.factions as faction}
            <span class="faction-tag">{faction}</span>
          {/each}
        </div>
        {#if book.era}
          <div class="book-era">Era: {book.era}</div>
        {/if}
        {#if book.synopsis}
          <div class="book-synopsis">{book.synopsis}</div>
        {/if}
      </div>
    {/each}
  {/if}
</div>
