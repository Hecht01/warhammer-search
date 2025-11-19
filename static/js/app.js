// API base URL - adjust if needed
const API_BASE = window.location.origin;

// Tab switching
document.querySelectorAll('.tab-button').forEach(button => {
    button.addEventListener('click', () => {
        const tabName = button.getAttribute('data-tab');

        // Update active tab button
        document.querySelectorAll('.tab-button').forEach(btn => btn.classList.remove('active'));
        button.classList.add('active');

        // Update active tab content
        document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
        document.getElementById(`${tabName}-tab`).classList.add('active');
    });
});

// Lore Search functionality
const searchInput = document.getElementById('search-input');
const searchButton = document.getElementById('search-button');
const resultsDiv = document.getElementById('results');
const loadingDiv = document.getElementById('loading');
const limitSelect = document.getElementById('result-limit');

async function performSearch() {
    const query = searchInput.value.trim();

    if (!query) {
        resultsDiv.innerHTML = '<div class="no-results">Please enter a search query.</div>';
        return;
    }

    // Show loading
    loadingDiv.classList.remove('hidden');
    resultsDiv.innerHTML = '';

    try {
        const limit = limitSelect.value;
        const response = await fetch(`${API_BASE}/search?q=${encodeURIComponent(query)}&limit=${limit}`);

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const results = await response.json();

        // Hide loading
        loadingDiv.classList.add('hidden');

        if (results.length === 0) {
            resultsDiv.innerHTML = '<div class="no-results">No results found. The Emperor protects... but not your search query.</div>';
            return;
        }

        // Display results
        displayLoreResults(results, query);

    } catch (error) {
        loadingDiv.classList.add('hidden');
        resultsDiv.innerHTML = `<div class="no-results">Error: ${error.message}</div>`;
        console.error('Search error:', error);
    }
}

function displayLoreResults(results, query) {
    resultsDiv.innerHTML = '';

    results.forEach((result, index) => {
        const card = document.createElement('div');
        card.className = 'result-card';

        const scorePercent = (result.score * 100).toFixed(1);
        const highlightedText = highlightQuery(result.text, query);

        card.innerHTML = `
            <div class="result-header">
                <span style="color: var(--text-secondary);">Result ${index + 1}</span>
                <span class="result-score">${scorePercent}% match</span>
            </div>
            <div class="result-text">${highlightedText}</div>
        `;

        resultsDiv.appendChild(card);
    });
}

function highlightQuery(text, query) {
    // Simple highlighting - case insensitive
    const words = query.split(/\s+/).filter(w => w.length > 2);
    let highlighted = text;

    words.forEach(word => {
        const regex = new RegExp(`(${escapeRegex(word)})`, 'gi');
        highlighted = highlighted.replace(regex, '<span class="highlight">$1</span>');
    });

    return highlighted;
}

function escapeRegex(string) {
    return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

// Event listeners for lore search
searchButton.addEventListener('click', performSearch);
searchInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        performSearch();
    }
});

// Books Search functionality
const booksSearchInput = document.getElementById('books-search-input');
const booksSearchButton = document.getElementById('books-search-button');
const booksResultsDiv = document.getElementById('books-results');
const factionFilter = document.getElementById('faction-filter');
const eraFilter = document.getElementById('era-filter');

async function performBooksSearch() {
    const query = booksSearchInput.value.trim();
    const faction = factionFilter.value;
    const era = eraFilter.value;

    try {
        let url = `${API_BASE}/books?`;
        const params = new URLSearchParams();

        if (query) params.append('q', query);
        if (faction) params.append('faction', faction);
        if (era) params.append('era', era);

        const response = await fetch(`${API_BASE}/books?${params.toString()}`);

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const books = await response.json();

        if (books.length === 0) {
            booksResultsDiv.innerHTML = '<div class="no-results">No books found matching your criteria.</div>';
            return;
        }

        displayBooksResults(books);

    } catch (error) {
        booksResultsDiv.innerHTML = `<div class="no-results">Error: ${error.message}</div>`;
        console.error('Books search error:', error);
    }
}

function displayBooksResults(books) {
    booksResultsDiv.innerHTML = '';

    books.forEach(book => {
        const card = document.createElement('div');
        card.className = 'book-card';

        const factionsHTML = book.factions.map(f =>
            `<span class="faction-tag">${f}</span>`
        ).join('');

        card.innerHTML = `
            <div class="book-title">${book.title}</div>
            <div class="book-author">by ${book.author}</div>
            ${book.series ? `<div class="book-series">📚 ${book.series}</div>` : ''}
            <div class="book-factions">${factionsHTML}</div>
            ${book.era ? `<div class="book-era">Era: ${book.era}</div>` : ''}
            ${book.synopsis ? `<div class="book-synopsis">${book.synopsis}</div>` : ''}
        `;

        booksResultsDiv.appendChild(card);
    });
}

// Event listeners for books search
booksSearchButton.addEventListener('click', performBooksSearch);
booksSearchInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        performBooksSearch();
    }
});

// Trigger search when filters change
factionFilter.addEventListener('change', () => {
    if (booksResultsDiv.innerHTML) {
        performBooksSearch();
    }
});

eraFilter.addEventListener('change', () => {
    if (booksResultsDiv.innerHTML) {
        performBooksSearch();
    }
});

// Load all books on page load
window.addEventListener('load', () => {
    performBooksSearch();
});
