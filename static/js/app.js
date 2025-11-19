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
    loadFactions();
    loadRules();
    loadStratagems();
});

// ========== RULES & STRATAGEMS ==========

// Rules functionality
const rulesSearchInput = document.getElementById('rules-search-input');
const rulesSearchButton = document.getElementById('rules-search-button');
const rulesResultsDiv = document.getElementById('rules-results');
const rulesFactionFilter = document.getElementById('rules-faction-filter');
const rulesCategoryFilter = document.getElementById('rules-category-filter');
const rulesPhaseFilter = document.getElementById('rules-phase-filter');

async function performRulesSearch() {
    const query = rulesSearchInput.value.trim();
    const faction = rulesFactionFilter.value;
    const category = rulesCategoryFilter.value;
    const phase = rulesPhaseFilter.value;

    try {
        const params = new URLSearchParams();
        if (query) params.append('q', query);
        if (faction) params.append('faction', faction);
        if (category) params.append('category', category);
        if (phase) params.append('phase', phase);

        const response = await fetch(`${API_BASE}/rules?${params.toString()}`);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);

        const rules = await response.json();
        displayRules(rules);
    } catch (error) {
        rulesResultsDiv.innerHTML = `<div class="no-results">Error: ${error.message}</div>`;
        console.error('Rules search error:', error);
    }
}

function displayRules(rules) {
    rulesResultsDiv.innerHTML = '';

    if (rules.length === 0) {
        rulesResultsDiv.innerHTML = '<div class="no-results">No rules found.</div>';
        return;
    }

    rules.forEach(rule => {
        const card = document.createElement('div');
        card.className = 'rule-card';

        card.innerHTML = `
            <div class="rule-name">${rule.name}</div>
            <span class="rule-category">${rule.category}</span>
            ${rule.phase ? `<span class="rule-phase">${rule.phase} Phase</span>` : ''}
            ${rule.faction ? `<div class="rule-faction">Faction: ${rule.faction}</div>` : ''}
            <div class="rule-description">${rule.description}</div>
        `;

        rulesResultsDiv.appendChild(card);
    });
}

// Stratagems functionality
const stratsSearchInput = document.getElementById('strats-search-input');
const stratsSearchButton = document.getElementById('strats-search-button');
const stratsResultsDiv = document.getElementById('strats-results');
const stratsFactionFilter = document.getElementById('strats-faction-filter');
const stratsTypeFilter = document.getElementById('strats-type-filter');
const stratsCostFilter = document.getElementById('strats-cost-filter');

async function performStratagemSearch() {
    const query = stratsSearchInput.value.trim();
    const faction = stratsFactionFilter.value;
    const type = stratsTypeFilter.value;
    const maxCost = stratsCostFilter.value;

    try {
        const params = new URLSearchParams();
        if (query) params.append('q', query);
        if (faction) params.append('faction', faction);
        if (type) params.append('type', type);
        if (maxCost) params.append('max_cost', maxCost);

        const response = await fetch(`${API_BASE}/stratagems?${params.toString()}`);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);

        const stratagems = await response.json();
        displayStratagems(stratagems);
    } catch (error) {
        stratsResultsDiv.innerHTML = `<div class="no-results">Error: ${error.message}</div>`;
        console.error('Stratagems search error:', error);
    }
}

function displayStratagems(stratagems) {
    stratsResultsDiv.innerHTML = '';

    if (stratagems.length === 0) {
        stratsResultsDiv.innerHTML = '<div class="no-results">No stratagems found.</div>';
        return;
    }

    stratagems.forEach(strat => {
        const card = document.createElement('div');
        card.className = 'strat-card';

        card.innerHTML = `
            <div class="strat-name">${strat.name}</div>
            <span class="strat-cost">${strat.cost} CP</span>
            <span class="strat-type">${strat.type}</span>
            ${strat.phase ? `<span class="strat-phase">${strat.phase} Phase</span>` : ''}
            <div class="strat-faction">Faction: ${strat.faction}</div>
            <div class="strat-when"><strong>When:</strong> ${strat.when}</div>
            <div class="strat-target"><strong>Target:</strong> ${strat.target}</div>
            <div class="strat-effect"><strong>Effect:</strong> ${strat.effect}</div>
        `;

        stratsResultsDiv.appendChild(card);
    });
}

// Event listeners for rules
rulesSearchButton.addEventListener('click', performRulesSearch);
rulesSearchInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') performRulesSearch();
});
rulesFactionFilter.addEventListener('change', performRulesSearch);
rulesCategoryFilter.addEventListener('change', performRulesSearch);
rulesPhaseFilter.addEventListener('change', performRulesSearch);

// Event listeners for stratagems
stratsSearchButton.addEventListener('click', performStratagemSearch);
stratsSearchInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') performStratagemSearch();
});
stratsFactionFilter.addEventListener('change', performStratagemSearch);
stratsTypeFilter.addEventListener('change', performStratagemSearch);
stratsCostFilter.addEventListener('change', performStratagemSearch);

// ========== FACTIONS ==========

// Faction icons mapping
const FACTION_ICONS = {
    'Space Marines': '🛡️',
    'Chaos Space Marines': '☠️',
    'Chaos': '👹',
    'Necrons': '💀',
    'Orks': '🔨',
    'Tyranids': '🦂',
    'Aeldari': '✨',
    'Tau': '🎯',
    'Astra Militarum': '⚔️',
    'Adeptus Mechanicus': '⚙️',
    'Imperium': '🦅',
    'Genestealer Cults': '👾',
    'Drukhari': '🗡️'
};

async function loadFactions() {
    try {
        // Load factions list
        const response = await fetch(`${API_BASE}/factions`);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);

        const factions = await response.json();

        // Populate faction dropdowns
        populateFactionDropdowns(factions);

        // Load faction counts and display cards
        await displayFactionCards(factions);
    } catch (error) {
        console.error('Error loading factions:', error);
    }
}

function populateFactionDropdowns(factions) {
    // Populate rules faction filter
    factions.forEach(faction => {
        const option = document.createElement('option');
        option.value = faction;
        option.textContent = faction;
        rulesFactionFilter.appendChild(option.cloneNode(true));
        stratsFactionFilter.appendChild(option);
    });
}

async function displayFactionCards(factions) {
    const factionCardsDiv = document.getElementById('faction-cards');
    factionCardsDiv.innerHTML = '';

    for (const faction of factions) {
        try {
            // Get counts for this faction
            const [booksRes, rulesRes, stratsRes] = await Promise.all([
                fetch(`${API_BASE}/books?faction=${encodeURIComponent(faction)}`),
                fetch(`${API_BASE}/rules?faction=${encodeURIComponent(faction)}`),
                fetch(`${API_BASE}/stratagems?faction=${encodeURIComponent(faction)}`)
            ]);

            const books = await booksRes.json();
            const rules = await rulesRes.json();
            const stratagems = await stratsRes.json();

            const card = document.createElement('div');
            card.className = 'faction-card';
            card.onclick = () => selectFaction(faction);

            const icon = FACTION_ICONS[faction] || '⚡';

            card.innerHTML = `
                <div class="faction-icon">${icon}</div>
                <div class="faction-name">${faction}</div>
                <div class="faction-counts">
                    <div class="faction-count-item">📚 ${books.length} Books</div>
                    <div class="faction-count-item">📋 ${rules.length} Rules</div>
                    <div class="faction-count-item">⚡ ${stratagems.length} Stratagems</div>
                </div>
            `;

            factionCardsDiv.appendChild(card);
        } catch (error) {
            console.error(`Error loading data for ${faction}:`, error);
        }
    }
}

function selectFaction(faction) {
    // Switch to rules tab and filter by faction
    document.querySelectorAll('.tab-button').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));

    const rulesTabButton = document.querySelector('[data-tab="rules"]');
    rulesTabButton.classList.add('active');
    document.getElementById('rules-tab').classList.add('active');

    // Set filters and search
    rulesFactionFilter.value = faction;
    stratsFactionFilter.value = faction;

    performRulesSearch();
    performStratagemSearch();
}

// Initial load of rules and stratagems
function loadRules() {
    performRulesSearch();
}

function loadStratagems() {
    performStratagemSearch();
}
