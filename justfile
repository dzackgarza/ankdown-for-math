[private]
default:
    @just --list

# Run the test suite
test:
    uv run --no-project --with-requirements requirements.txt --with pytest python -m pytest -q

# CI entry point (used by the pre-push hook)
test-ci: test
