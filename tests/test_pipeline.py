import json
import subprocess
import os
import pytest
import zipfile
import sqlite3
import tempfile
from ankdown.cli import DeckInput

def test_pydantic_validation():
    # Valid data
    data = {
        "meta": {"title": "Test", "model": "Test", "tags": ["t1"]},
        "cards": [{"front": "Q", "back": "A", "tags": ["t2"]}],
        "media": []
    }
    deck = DeckInput(**data)
    assert deck.meta.title == "Test"
    assert len(deck.cards) == 1

def test_per_card_tags():
    """A per-card 'tags:' line is extracted into that card's tags and removed from the back."""
    cmd = ["pandoc", "--lua-filter", "ankdown/ankdown.lua",
           "tests/fixtures/per_card_tags.md", "-t", "plain"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode == 0
    cards = json.loads(result.stdout)["cards"]
    tagged = next(c for c in cards if "Simple group" in c["front"])
    assert tagged.get("tags") == ["definition", "important"]
    assert "tags:" not in tagged["back"]  # marker line stripped from the answer
    untagged = next(c for c in cards if "Untagged card" in c["front"])
    assert not untagged.get("tags")       # cards without the marker get no card-level tags


def inspect_apkg(apkg_path):
    """Extract and return notes from an .apkg file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with zipfile.ZipFile(apkg_path, 'r') as zip_ref:
            zip_ref.extract('collection.anki2', tmpdir)
        
        conn = sqlite3.connect(os.path.join(tmpdir, 'collection.anki2'))
        cursor = conn.cursor()
        cursor.execute("SELECT flds FROM notes")
        notes = [row[0].split('\x1f') for row in cursor.fetchall()]
        conn.close()
    return notes

@pytest.mark.parametrize("fixture_name", [f for f in os.listdir("tests/fixtures") if f.endswith(".md")])
def test_lua_filter_fixtures(fixture_name):
    fixture_path = os.path.join("tests/fixtures", fixture_name)
    cmd = ["pandoc", "--lua-filter", "ankdown/ankdown.lua", fixture_path, "-t", "plain"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode == 0
    
    data = json.loads(result.stdout)
    assert "cards" in data
    assert len(data["cards"]) > 0
    
    # Check for specific content markers based on fixture name
    if "tikzcd" in fixture_name:
        assert "tikzcd" in result.stdout
    if "align" in fixture_name:
        assert "align*" in result.stdout
    if "matrix" in fixture_name:
        assert "pmatrix" in result.stdout or "bmatrix" in result.stdout
    if "mathbb" in fixture_name:
        assert "mathbb" in result.stdout

def test_apkg_content_fidelity():
    fixture_path = "tests/fixtures/complex_physics.md"
    apkg_target = "physics_test.apkg"
    
    # Run pipeline
    pandoc_cmd = ["pandoc", "--lua-filter", "ankdown/ankdown.lua", fixture_path, "-t", "plain"]
    cli_cmd = ["python3", "ankdown/cli.py", "compile", "--output", apkg_target]
    
    p1 = subprocess.Popen(pandoc_cmd, stdout=subprocess.PIPE)
    p2 = subprocess.run(cli_cmd, stdin=p1.stdout, capture_output=True, text=True)
    p1.stdout.close()
    
    assert p2.returncode == 0
    assert os.path.exists(apkg_target)
    
    # Inspect internal DB
    notes = inspect_apkg(apkg_target)
    assert len(notes) == 3
    
    # Verify first card content
    # Front should be "What is Schrödinger's Cat?" (formatted as <strong>)
    # Actually my fixture had: - **Schrödinger's Cat**
    assert "Schrödinger’s Cat" in notes[0][0]
    assert "paradox of quantum superposition" in notes[0][1]
    
    # Verify math content in second card
    assert "\\[\\iint_\\Sigma (\\nabla \\times \\mathbf{F}) \\cdot d\\mathbf{a}" in notes[1][1]
    
    print(f"\nTest APKG preserved at: {os.path.abspath(apkg_target)}")
