# List available recipes
default:
    @just --list

# Bump smello client version (patch, minor, or major)
bump-client part:
    uv run --frozen bump-my-version bump {{ part }} --config-file clients/python/.bumpversion.toml

# Bump smello-server version (patch, minor, or major)
bump-server part:
    uv run --frozen bump-my-version bump {{ part }} --config-file server/.bumpversion.toml

# Run smello server locally with auto-reload (http://localhost:5110)
server:
    uv run smello-server run --reload

# Install frontend dependencies
frontend-install:
    cd frontend && npm install

# Run frontend dev server (http://localhost:5111, proxies /api to :5110)
frontend-dev:
    cd frontend && npm run dev

# Build frontend for production
frontend-build:
    cd frontend && npm run build

# Bundle built frontend into server package (for wheel builds)
frontend-bundle: frontend-build
    rm -rf server/src/smello_server/_frontend
    cp -r frontend/dist server/src/smello_server/_frontend

# Run frontend tests
frontend-test:
    cd frontend && npm test

# Run server + frontend dev server (two terminals recommended instead)
dev:
    just server & just frontend-dev

# Serve docs site locally (http://localhost:8000)
docs:
    uv run zensical serve
