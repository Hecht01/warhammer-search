<script>
  import { onMount } from 'svelte';
  import LoreSearch from './components/LoreSearch.svelte';
  import Books from './components/Books.svelte';
  import Rules from './components/Rules.svelte';
  import Factions from './components/Factions.svelte';

  let activeTab = 'lore';

  function setActiveTab(tab) {
    activeTab = tab;
  }
</script>

<div class="container">
  <header>
    <h1>WARHAMMER 40,000</h1>
    <h2>SEMANTIC SEARCH ENGINE</h2>
    <p class="tagline">In the grim darkness of the far future, there is only search...</p>
  </header>

  <nav class="tabs">
    <button
      class="tab-button"
      class:active={activeTab === 'lore'}
      on:click={() => setActiveTab('lore')}
    >
      Lore Search
    </button>
    <button
      class="tab-button"
      class:active={activeTab === 'books'}
      on:click={() => setActiveTab('books')}
    >
      Books
    </button>
    <button
      class="tab-button"
      class:active={activeTab === 'rules'}
      on:click={() => setActiveTab('rules')}
    >
      Rules & Stratagems
    </button>
    <button
      class="tab-button"
      class:active={activeTab === 'factions'}
      on:click={() => setActiveTab('factions')}
    >
      Factions
    </button>
  </nav>

  {#if activeTab === 'lore'}
    <LoreSearch />
  {:else if activeTab === 'books'}
    <Books />
  {:else if activeTab === 'rules'}
    <Rules />
  {:else if activeTab === 'factions'}
    <Factions bind:activeTab />
  {/if}

  <footer>
    <p>Powered by Sentence Transformers + Qdrant Vector Database</p>
    <p>Data sourced from Warhammer 40K Fandom Wiki</p>
  </footer>
</div>
