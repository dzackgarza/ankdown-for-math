[private]
default:
    @just --list

# Run the test suite
test:
    python3 -m pytest -q

# CI entry point (used by the pre-push hook)
test-ci: test

# Regenerate the vendored MathJax macros from the pandoc-config generator (source of truth)
regen-macros:
    python3 ~/.pandoc/bin/generate-mathjax-config.py --json ankdown/mathjax-macros.json
