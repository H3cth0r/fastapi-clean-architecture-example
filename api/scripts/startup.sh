#!/bin/bash
set -e

echo "🚀 Starting application setup..."

echo "🌱 Setting up database and seeding default data..."
# The seed script will create schemas if needed
python -m api.scripts.seed

echo "✅ Setup complete! Starting application..."
python -m api.app
