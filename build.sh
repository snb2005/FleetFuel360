#!/usr/bin/env bash
# Build hook for Render deployment

echo "🚀 Starting FleetFuel360 build process..."

# Install dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Set Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Initialize database if needed
echo "🗄️ Initializing database..."
python -c "
import sys
import os
sys.path.insert(0, os.getcwd())

try:
    from backend.db.init_db import initialize_database
    initialize_database()
    print('✅ Database initialized successfully')
except Exception as e:
    print(f'⚠️ Database initialization: {e}')
    # Don't fail build if DB already exists
"

# Create necessary directories
mkdir -p ml/models
mkdir -p logs

echo "✅ Build completed successfully!"
