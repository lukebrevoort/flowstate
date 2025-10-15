#!/bin/bash
# Quick format check and fix script for flowstate backend

echo "🔍 Checking code formatting..."

cd "$(dirname "$0")"

# Check formatting
if python -m black --check backend/; then
    echo "✅ All files are properly formatted!"
else
    echo "❌ Files need formatting. Running black..."
    python -m black backend/
    echo "✅ Files formatted! Please commit the changes:"
    echo "   git add ."
    echo "   git commit -m 'Format code with black'"
    echo "   git push"
fi