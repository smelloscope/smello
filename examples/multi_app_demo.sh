#!/usr/bin/env bash
# Demonstrate app and session tagging with multiple Python scripts.
#
# Each script runs under a different --app name but shares the same
# --session, so you can filter the dashboard to see just this run:
#
#   http://localhost:5110/api/events?session=demo-multi-app
#
# Prerequisites:
#   smello-server running on http://localhost:5110
#   pip install smello

set -euo pipefail

SESSION="demo-multi-app"

echo "Session: $SESSION"
echo "---"

echo "Running requests demo as 'requests-app'..."
uv run smello run --app requests-app --session "$SESSION" \
  python examples/python/basic_requests.py

echo "Running httpx demo as 'httpx-app'..."
uv run smello run --app httpx-app --session "$SESSION" \
  python examples/python/basic_httpx.py

echo "---"
echo "Done. Filter by session:"
echo "  curl 'http://localhost:5110/api/events?session=$SESSION'"
echo ""
echo "Or filter by a single app:"
echo "  curl 'http://localhost:5110/api/events?app=requests-app&session=$SESSION'"
