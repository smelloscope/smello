# Stage 1: Build React frontend
FROM node:22-slim AS frontend-build
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
# `frontend/src/api/schema.ts` is committed; skip the prebuild
# `openapi-typescript` regen step at image build time.
RUN npm run build --ignore-scripts

# Stage 2: Python server
FROM python:3.14-slim
WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY server/ server/
COPY clients/python/ clients/python/
COPY pyproject.toml uv.lock* ./

RUN uv sync --package smello-server --no-dev --frozen

COPY --from=frontend-build /frontend/dist /app/frontend-dist

EXPOSE 5110

ENV SMELLO_DB_PATH=/data/smello.db
ENV SMELLO_FRONTEND_DIR=/app/frontend-dist

CMD ["uv", "run", "--package", "smello-server", "smello-server", "--no-open"]
