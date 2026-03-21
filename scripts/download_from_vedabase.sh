#!/bin/bash
# Download scriptures from Vedabase for AI Prabhupada RAG
# Phase 1: Bhagavad Gita only

set -e

DATA_DIR="$(dirname "$0")/../data"
mkdir -p "$DATA_DIR"

echo "==================================="
echo "PHASE 1: Bhagavad Gita Download"
echo "==================================="
echo ""
echo "Manual download instructions:"
echo ""
echo "Option 1: Vedabase Website"
echo "  1. Visit: https://vedabase.io/en/library/bg/"
echo "  2. Open each chapter (1-18)"
echo "  3. Copy verse text (skip purports for now)"
echo "  4. Paste into: $DATA_DIR/bhagavad_gita_verses.txt"
echo ""
echo "Option 2: Use existing text files"
echo "  If you have Bhagavad Gita text files, place them in:"
echo "  $DATA_DIR/"
echo ""
echo "Option 3: API Download (if available)"
echo "  Run: python3 scripts/vedabase_api_downloader.py"
echo ""
echo "Expected file structure:"
echo "  bhagavad_gita_verses.txt - All verses (18 chapters)"
echo "  ~50KB, est. cost: $0.01"
echo ""
echo "Press Enter when you've added the text files..."
read

# Check if files exist
if ls "$DATA_DIR"/*.txt 1> /dev/null 2>&1; then
    echo "✓ Found text files in $DATA_DIR"
    ls -lh "$DATA_DIR"/*.txt
    echo ""
    echo "Ready to proceed with embedding!"
    echo "Run: python3 scripts/embed_scriptures.py"
else
    echo "⚠️  No .txt files found in $DATA_DIR"
    echo "Please add scripture texts and run this script again."
    exit 1
fi
