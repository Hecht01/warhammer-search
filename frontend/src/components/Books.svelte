<script>
  import { onMount } from 'svelte';
  import SearchBar from './SearchBar.svelte';

  const API_BASE = window.location.origin;

  let query = '';
  let factionFilter = '';
  let eraFilter = '';
  let books = [];
  let selectedBook = null;

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

  function selectBook(book) {
    selectedBook = book;
  }

  function closeModal() {
    selectedBook = null;
  }

  onMount(() => {
    loadBooks();
  });

  $: if (factionFilter || eraFilter) loadBooks();
</script>

<SearchBar
  bind:value={query}
  placeholder="Search books by title, author, or series..."
  onSearch={loadBooks}
/>

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
  <div class="books-count">{books.length} {books.length === 1 ? 'book' : 'books'} found</div>
  {#if books.length === 0}
    <div class="no-results">No books found matching your criteria.</div>
  {:else}
    {#each books as book}
      <div class="book-card" on:click={() => selectBook(book)} role="button" tabindex="0" on:keypress={(e) => e.key === 'Enter' && selectBook(book)}>
        <div class="book-title">{book.title}</div>
        <div class="book-author">by {book.author}</div>
        {#if book.series}
          <div class="book-series">Series: {book.series}</div>
        {/if}
        <div class="book-meta">
          <div class="book-factions">
            {#each book.factions as faction}
              <span class="faction-tag">{faction}</span>
            {/each}
          </div>
          {#if book.page_count}
            <div class="book-pages">{book.page_count} pages</div>
          {/if}
        </div>
        {#if book.era}
          <div class="book-era">Era: {book.era}</div>
        {/if}
        <div class="click-hint">Click for details</div>
      </div>
    {/each}
  {/if}
</div>

{#if selectedBook}
  <div class="modal-overlay" on:click={closeModal} role="presentation">
    <div class="modal-content" on:click|stopPropagation role="dialog" aria-modal="true">
      <button class="modal-close" on:click={closeModal}>&times;</button>
      <h2 class="modal-title">{selectedBook.title}</h2>
      <div class="modal-author">by {selectedBook.author}</div>
      {#if selectedBook.series}
        <div class="modal-series">Part of the {selectedBook.series} series</div>
      {/if}
      <div class="modal-meta">
        {#if selectedBook.page_count}
          <div class="meta-item">
            <strong>Pages:</strong> {selectedBook.page_count}
          </div>
        {/if}
        {#if selectedBook.era}
          <div class="meta-item">
            <strong>Era:</strong> {selectedBook.era}
          </div>
        {/if}
        <div class="meta-item">
          <strong>Factions:</strong> {selectedBook.factions.join(', ')}
        </div>
      </div>
      {#if selectedBook.synopsis}
        <div class="modal-synopsis">
          <h3>Synopsis</h3>
          <p>{selectedBook.synopsis}</p>
        </div>
      {/if}
    </div>
  </div>
{/if}

<style>
  .books-count {
    text-align: center;
    color: var(--accent-gold);
    margin-bottom: 15px;
    font-size: 1.1em;
  }

  .book-card {
    cursor: pointer;
    transition: all 0.3s;
  }

  .book-card:hover {
    transform: translateY(-2px);
  }

  .book-meta {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 10px;
  }

  .book-pages {
    color: var(--text-secondary);
    font-size: 0.9em;
    font-style: italic;
  }

  .click-hint {
    text-align: center;
    color: var(--text-secondary);
    font-size: 0.85em;
    margin-top: 10px;
    opacity: 0.7;
  }

  .modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.85);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
    padding: 20px;
  }

  .modal-content {
    background: var(--bg-dark);
    border: 2px solid var(--accent-gold);
    max-width: 600px;
    max-height: 90vh;
    overflow-y: auto;
    padding: 30px;
    position: relative;
    box-shadow: 0 0 30px rgba(184, 134, 11, 0.5);
  }

  .modal-close {
    position: absolute;
    top: 10px;
    right: 15px;
    background: none;
    border: none;
    color: var(--accent-gold);
    font-size: 30px;
    cursor: pointer;
    padding: 0;
    width: 30px;
    height: 30px;
    line-height: 1;
  }

  .modal-close:hover {
    color: var(--text-color);
  }

  .modal-title {
    color: var(--accent-gold);
    font-size: 2em;
    margin: 0 0 10px 0;
  }

  .modal-author {
    color: var(--text-secondary);
    font-size: 1.2em;
    margin-bottom: 15px;
  }

  .modal-series {
    color: var(--accent-gold);
    font-style: italic;
    margin-bottom: 20px;
  }

  .modal-meta {
    background: var(--bg-medium);
    border-left: 3px solid var(--accent-gold);
    padding: 15px;
    margin: 20px 0;
  }

  .meta-item {
    margin-bottom: 10px;
  }

  .meta-item:last-child {
    margin-bottom: 0;
  }

  .meta-item strong {
    color: var(--accent-gold);
  }

  .modal-synopsis {
    margin-top: 20px;
  }

  .modal-synopsis h3 {
    color: var(--accent-gold);
    margin-bottom: 10px;
  }

  .modal-synopsis p {
    line-height: 1.6;
    color: var(--text-color);
  }
</style>
