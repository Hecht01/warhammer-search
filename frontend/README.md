# Warhammer 40K Search - Frontend

This is the Svelte-based frontend for the Warhammer 40K Search Engine.

## Development

```bash
# Install dependencies
npm install

# Run development server
npm run dev
```

## Build for Production

```bash
# Build the app (outputs to ../static/)
npm run build
```

The build process automatically outputs to the `static/` directory at the project root, which is served by the FastAPI backend.

## Project Structure

- `src/App.svelte` - Main application component
- `src/components/` - Individual tab components
  - `LoreSearch.svelte` - Semantic lore search
  - `Books.svelte` - Books database browser
  - `Rules.svelte` - Rules & Stratagems reference
  - `Factions.svelte` - Faction navigation
- `src/app.css` - Global styles
