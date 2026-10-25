import json
import sys
import hashlib
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, field_validator
from pathlib import Path
import genanki
import cyclopts

app = cyclopts.App()

import os
import urllib.request

# pandoc-config main is the source of truth for the macro set and for the
# MathJax 4 TeX package "stmaryrd" that the macros use. Each build reads both.
PANDOC_CONFIG_URL = (
    "https://raw.githubusercontent.com/dzackgarza/pandoc-config/main/templates"
)
MACROS_URL = PANDOC_CONFIG_URL + "/css/mathjax-macros.json"
STMARYRD_URL = PANDOC_CONFIG_URL + "/js/mathjax-stmaryrd.js"


def fetch(url: str) -> str:
    with urllib.request.urlopen(url, timeout=30) as response:
        return response.read().decode("utf-8").strip()


def fetch_macros() -> str:
    """The JSON macro set from pandoc-config main."""
    return fetch(MACROS_URL)


def fetch_stmaryrd() -> str:
    """The script that defines registerStmaryrd, from pandoc-config main."""
    return fetch(STMARYRD_URL)


MacroDefinition = str | tuple[str, int] | tuple[str, int, str]


class RendererAssets(BaseModel):
    """The macro set and TeX package bundled together in an Anki package."""

    model_config = ConfigDict(extra="forbid")
    macros: dict[str, MacroDefinition]
    stmaryrd: str = Field(min_length=1)


def load_renderer_assets(path: Path | None) -> RendererAssets:
    if path is not None:
        return RendererAssets.model_validate_json(path.read_bytes())
    return RendererAssets(
        macros=TypeAdapter(dict[str, MacroDefinition]).validate_json(fetch_macros()),
        stmaryrd=fetch_stmaryrd(),
    )


class Card(BaseModel):
    front: str
    back: str
    tags: List[str] = Field(default_factory=list)

    @field_validator("front", "back")
    @classmethod
    def not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Field cannot be empty")
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

        # Load MathJax 4 config template. The macros and the stmaryrd package are bundled
        # separately as the media file _ankdown_macros.js (see compile()); this template
        # loads them.
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
                    "afmt": "{{FrontSide}}<hr id='answer'>{{Answer}}\n"
                    + mathjax_content,
                },
            ],
            css=css,
        )


def _compile_json(raw_input: str, output: str, assets: RendererAssets):
    """Build an .apkg from ankdown JSON (the lua filter's output)."""
    try:
        if not raw_input.strip():
            print("Error: No input received", file=sys.stderr)
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
            guid=note_id,
        )
        deck.add_note(note)

    # Media handling
    import tempfile
    import shutil

    media_files = []
    with tempfile.TemporaryDirectory() as tmpdir:
        # Bundle the generated MathJax macros and the stmaryrd package as a protected
        # media file. It carries "{{" in macro bodies, so it must be an external file,
        # not inline in the card template.
        macros_js_path = os.path.join(tmpdir, "_ankdown_macros.js")
        with open(macros_js_path, "w") as f:
            f.write(
                assets.stmaryrd
                + "\nwindow.ANKDOWN_MACROS = "
                + json.dumps(assets.macros)
                + ";"
            )
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
        print(
            f"Successfully created {output} with {len(deck_input.cards)} cards and {len(media_files)} media files."
        )


@app.command
def compile(output: str = "output.apkg", renderer_assets: Path | None = None):
    """Compile ankdown JSON from stdin into an .apkg file."""
    _compile_json(sys.stdin.read(), output, load_renderer_assets(renderer_assets))


@app.command
def build(
    input: str,
    output: str = "output.apkg",
    output_dir: Optional[str] = None,
    renderer_assets: Path | None = None,
):
    """Build .apkg(s) straight from Markdown deck file(s), using the bundled lua filter.

    INPUT is a single .md file (-> --output) or a directory built recursively
    (-> --output-dir, one .apkg per deck). Requires pandoc on PATH.
    """
    import subprocess
    import glob

    lua = os.path.join(os.path.dirname(__file__), "ankdown.lua")
    assets = load_renderer_assets(renderer_assets)

    def run(md_path, out_path):
        proc = subprocess.run(
            ["pandoc", "--lua-filter", lua, md_path, "-t", "plain"],
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0:
            print(f"pandoc failed for {md_path}:\n{proc.stderr}", file=sys.stderr)
            sys.exit(1)
        _compile_json(proc.stdout, out_path, assets)

    if os.path.isdir(input):
        if not output_dir:
            print(
                "Error: --output-dir is required when INPUT is a directory",
                file=sys.stderr,
            )
            sys.exit(1)
        os.makedirs(output_dir, exist_ok=True)
        mds = sorted(glob.glob(os.path.join(input, "**", "*.md"), recursive=True))
        if not mds:
            print(f"Error: no .md files found under {input}", file=sys.stderr)
            sys.exit(1)
        for md in mds:
            name = os.path.relpath(md, input)[:-3].replace(os.sep, "__")
            run(md, os.path.join(output_dir, name + ".apkg"))
    else:
        run(input, output)


if __name__ == "__main__":
    app()
