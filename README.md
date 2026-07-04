# Ankdown

A simple way to write Anki decks in Markdown using Pandoc.

## What This Is

Ankdown converts Markdown lists into Anki decks (`.apkg`). It uses **Pandoc** for semantic parsing, ensuring perfect LaTeX math support and robust Markdown handling.

## How to use it

### 1. Requirements
- **Pandoc**: Must be installed on your system.
- **Python 3**: With `genanki`, `cyclopts`, and `pydantic`.

### 2. Writing Cards
Cards are written as nested lists. The top-level item is the **Front**, and sub-items are the **Back**.

```markdown
---
title: "Sample Deck"
---

- **Euler's Identity**
    - $e^{i\pi} + 1 = 0$
    - This equation is remarkably beautiful.
- **Newton's Second Law**
    - $F = ma$
```

### 3. Compiling
Run the following command to generate your deck:

```bash
pandoc --lua-filter ankdown/ankdown.lua my_cards.md -t plain | ankdown compile --output my_deck.apkg
```

## Installing

1. Clone the repository.
2. Install dependencies: `pip install .` (or use a virtual environment).

## Features
- **Semantic Lists**: No custom separators (`%`, `---`) required.
- **Math Support**: Full Pandoc/LaTeX math integration.
- **Validation**: Fail-early validation of card structure and fields.
- **Media**: Automated image inclusion from Markdown source.