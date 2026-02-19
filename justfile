# List available recipes
default:
    @just --list

# Bump smello client version (patch, minor, or major)
bump-client part:
    uv run --frozen bump-my-version bump {{ part }} --config-file clients/python/.bumpversion.toml

# Bump smello-server version (patch, minor, or major)
bump-server part:
    uv run --frozen bump-my-version bump {{ part }} --config-file server/.bumpversion.toml

# Serve docs site locally (http://localhost:8000)
docs:
    uv run zensical serve
