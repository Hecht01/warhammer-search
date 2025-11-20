<script>
  export let value = '';
  export let placeholder = 'Search...';
  export let onSearch = () => {};

  function handleKeyPress(event) {
    if (event.key === 'Enter') {
      onSearch();
    }
  }
</script>

<div class="search-bar-container">
  <input
    type="text"
    class="search-input"
    bind:value={value}
    on:keypress={handleKeyPress}
    {placeholder}
    autocomplete="off"
  />
  <button class="search-button" on:click={onSearch}>
    <span class="search-icon">⚔</span>
    Search
  </button>
</div>

<style>
  .search-bar-container {
    display: flex;
    gap: 10px;
    margin-bottom: 20px;
  }

  .search-input {
    flex: 1;
    background: var(--bg-medium);
    border: 2px solid var(--border-color);
    color: var(--text-color);
    padding: 15px 20px;
    font-size: 16px;
    font-family: inherit;
    transition: all 0.3s;
  }

  .search-input:focus {
    outline: none;
    border-color: var(--accent-gold);
    box-shadow: 0 0 15px rgba(184, 134, 11, 0.3);
  }

  .search-input::placeholder {
    color: var(--text-secondary);
  }

  .search-button {
    background: linear-gradient(135deg, var(--accent-gold) 0%, #d4a017 100%);
    color: var(--bg-dark);
    border: none;
    padding: 15px 30px;
    font-size: 16px;
    font-weight: bold;
    cursor: pointer;
    transition: all 0.3s;
    text-transform: uppercase;
    letter-spacing: 1px;
  }

  .search-button:hover {
    background: linear-gradient(135deg, #d4a017 0%, var(--accent-gold) 100%);
    box-shadow: 0 0 20px rgba(184, 134, 11, 0.5);
    transform: translateY(-2px);
  }

  .search-button:active {
    transform: translateY(0);
  }

  .search-icon {
    margin-right: 8px;
    font-size: 18px;
  }
</style>
