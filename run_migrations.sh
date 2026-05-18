#!/bin/bash
# run_migrations.sh
# Run this once after Railway Postgres is provisioned
# Usage: DATABASE_URL=postgresql://... bash run_migrations.sh

echo "Running lioMalau migrations..."
psql $DATABASE_URL -f panel-db/migrations/001_schema.sql
echo "Migration complete."
echo ""
echo "Now seed the precedents:"
echo "  cd ai-engine && pip install -r requirements.txt"
echo "  DATABASE_URL=... OPENAI_API_KEY=... python seed_precedents.py"
echo "  DATABASE_URL=... OPENAI_API_KEY=... python seed_comprehensive.py"
