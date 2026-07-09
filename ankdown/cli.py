#!/usr/bin/env python3
import json
import sys
import hashlib
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator
import genanki
import cyclopts

app = cyclopts.App()

import os

class Card(BaseModel):
    front: str
    back: str
    tags: List[str] = Field(default_factory=list)

    @field_validator('front', 'back')
    @classmethod
    def not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError('Field cannot be empty')
        return v

class DeckMeta(BaseModel):
    title: str = "Ankdown Deck"
    model: str = "Ankdown Model"
    tags: List[str] = Field(default_factory=list)

class DeckInput(BaseModel):
    meta: DeckMeta
    cards: List[Card]
    media: List[str] = Field(default_factory=list)
def simple_hash(text: str) -> int:
    """MD5 of text, mod 2^31."""
    h = hashlib.md5()
    h.update(text.encode("utf-8"))
    return int(h.hexdigest(), 16) % (1 << 31)

class AnkdownModel(genanki.Model):
    @classmethod
    def create(cls, model_name: str) -> "AnkdownModel":
        model_id = simple_hash(model_name)
        base_dir = os.path.dirname(__file__)
        
        # Load MathJax 3 config template. Macros themselves are bundled separately as the
        # media file _ankdown_macros.js (see compile()); this template loads them.
        mathjax_path = os.path.join(base_dir, "mathjax.html")
        with open(mathjax_path, "r") as f:
            mathjax_content = f.read()

        # Load CSS from external file
        try:
            css_path = os.path.join(base_dir, "card.css")
            with open(css_path, "r") as f:
                css = f.read()
        except Exception as e:
            print(f"Warning: Could not load card.css: {e}", file=sys.stderr)
            css = ".card { font-family: arial; font-size: 20px; text-align: left; }"

        return cls(
            model_id,
            model_name,
            fields=[
                {"name": "Question"},
                {"name": "Answer"},
                {"name": "Guid"},
            ],
            templates=[
                {
                    "name": "Ankdown Card",
                    "qfmt": "{{Question}}\n" + mathjax_content,
                    "afmt": "{{FrontSide}}<hr id='answer'>{{Answer}}\n" + mathjax_content,
                },
            ],
            css=css
        )

@app.command
def compile(output: str = "output.apkg"):
    """
    Compile cards from JSON stdin into an .apkg file.
    """
    try:
        raw_input = sys.stdin.read()
        if not raw_input:
            print("Error: No input received on stdin", file=sys.stderr)
            sys.exit(1)
            
        data = json.loads(raw_input)
        deck_input = DeckInput(**data)
    except Exception as e:
        print(f"Validation Error: {e}", file=sys.stderr)
        sys.exit(1)

    if not deck_input.cards:
        print("Error: No cards found in input", file=sys.stderr)
        sys.exit(1)

    deck_name = deck_input.meta.title
    deck_id = simple_hash(deck_name)
    deck = genanki.Deck(deck_id, deck_name)
    
    model = AnkdownModel.create(deck_input.meta.model)
    
    for card in deck_input.cards:
        all_tags = list(set(deck_input.meta.tags + card.tags))
        # Stable GUID based on front and back content
        note_id = simple_hash(card.front + card.back)
        
        note = genanki.Note(
            model=model,
            fields=[card.front, card.back, str(note_id)],
            tags=all_tags,
            guid=note_id
        )
        deck.add_note(note)

    # Media handling
    import tempfile
    import shutil
    
    media_files = []
    with tempfile.TemporaryDirectory() as tmpdir:
        # Bundle the generated MathJax macros as a protected media file. It carries "{{"
        # in macro bodies, so it must be an external file, not inline in the card template.
        base_dir = os.path.dirname(__file__)
        with open(os.path.join(base_dir, "mathjax-macros.json")) as f:
            macros_json = f.read().strip()
        macros_js_path = os.path.join(tmpdir, "_ankdown_macros.js")
        with open(macros_js_path, "w") as f:
            f.write("window.ANKDOWN_MACROS = " + macros_json + ";")
        media_files.append(macros_js_path)

        for m in set(deck_input.media):
            if ":" in m:
                abs_path, mangled_name = m.split(":", 1)
                if os.path.exists(abs_path):
                    tmp_path = os.path.join(tmpdir, mangled_name)
                    os.makedirs(os.path.dirname(tmp_path), exist_ok=True)
                    shutil.copy2(abs_path, tmp_path)
                    media_files.append(tmp_path)
                else:
                    print(f"Error: Media file not found: {abs_path}", file=sys.stderr)
                    sys.exit(1)
            else:
                if os.path.exists(m):
                    media_files.append(m)
                else:
                    print(f"Error: Media file not found: {m}", file=sys.stderr)
                    sys.exit(1)

        package = genanki.Package(deck)
        package.media_files = media_files
        package.write_to_file(output)
        print(f"Successfully created {output} with {len(deck_input.cards)} cards and {len(media_files)} media files.")

if __name__ == "__main__":
    app()
