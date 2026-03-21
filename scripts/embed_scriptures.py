#!/usr/bin/env python3
"""
AI Prabhupada RAG - Scripture Embedding Script
Uses Voyage AI for embeddings and vector search
"""
import os
import json
import requests
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Voyage AI configuration
VOYAGE_API_KEY = os.getenv("VOYAGE_API_KEY")
if not VOYAGE_API_KEY:
    raise ValueError("VOYAGE_API_KEY not found in environment variables")
VOYAGE_API_URL = "https://api.voyageai.com/v1/embeddings"
EMBEDDING_MODEL = "voyage-3-large"

# Data paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
EMBEDDINGS_DIR = PROJECT_ROOT / "embeddings"
EMBEDDINGS_DIR.mkdir(exist_ok=True)


def create_embeddings_batch(texts: list) -> list:
    """Create embeddings for multiple texts using Voyage AI (batch)"""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {VOYAGE_API_KEY}"
    }
    
    # Voyage AI has a max input limit - truncate very long chunks
    cleaned_texts = []
    for text in texts:
        # Max ~4000 tokens per chunk (safe limit)
        words = text.split()
        if len(words) > 3000:
            text = " ".join(words[:3000]) + "..."
        cleaned_texts.append(text)
    
    payload = {
        "input": cleaned_texts,
        "model": EMBEDDING_MODEL
    }
    
    try:
        response = requests.post(VOYAGE_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        return [item["embedding"] for item in response.json()["data"]]
    except requests.exceptions.HTTPError as e:
        print(f"\n⚠️  API Error: {e}")
        print(f"Batch size: {len(texts)}, Max chunk words: {max(len(t.split()) for t in texts)}")
        raise


def chunk_text(text: str, max_tokens: int = 400, overlap: int = 50) -> list:
    """Split text into overlapping chunks"""
    # Simple sentence-based chunking (can be improved)
    sentences = text.split(". ")
    chunks = []
    current_chunk = []
    current_length = 0
    
    for sentence in sentences:
        sentence_length = len(sentence.split())
        
        if current_length + sentence_length > max_tokens and current_chunk:
            chunks.append(". ".join(current_chunk) + ".")
            # Keep last few sentences for overlap
            current_chunk = current_chunk[-overlap//20:] if overlap else []
            current_length = sum(len(s.split()) for s in current_chunk)
        
        current_chunk.append(sentence)
        current_length += sentence_length
    
    if current_chunk:
        chunks.append(". ".join(current_chunk) + ".")
    
    return chunks


def embed_scripture(scripture_name: str, text_content: str):
    """Embed a scripture text and save to JSON"""
    print(f"Processing {scripture_name}...")
    
    chunks = chunk_text(text_content)
    print(f"Created {len(chunks)} chunks")
    
    # Batch embedding for speed
    BATCH_SIZE = 50  # Process 50 chunks at a time (safer for API limits)
    embeddings_data = []
    
    for batch_start in range(0, len(chunks), BATCH_SIZE):
        batch_end = min(batch_start + BATCH_SIZE, len(chunks))
        batch_chunks = chunks[batch_start:batch_end]
        
        print(f"Embedding batch {batch_start//BATCH_SIZE + 1}/{(len(chunks)-1)//BATCH_SIZE + 1} "
              f"(chunks {batch_start+1}-{batch_end}/{len(chunks)})...", end="\r")
        
        batch_embeddings = create_embeddings_batch(batch_chunks)
        
        for i, (chunk, embedding) in enumerate(zip(batch_chunks, batch_embeddings)):
            embeddings_data.append({
                "chunk_id": batch_start + i,
                "text": chunk,
                "embedding": embedding
            })
    
    # Save to JSON
    output_file = EMBEDDINGS_DIR / f"{scripture_name}_embeddings.json"
    with open(output_file, "w") as f:
        json.dump({
            "scripture": scripture_name,
            "model": EMBEDDING_MODEL,
            "chunks": embeddings_data
        }, f, indent=2)
    
    print(f"\n✓ Saved embeddings to {output_file}")
    return len(chunks)


def main():
    """Main embedding pipeline"""
    print("AI Prabhupada RAG - Scripture Embedding")
    print("=" * 50)
    
    # Check if data directory has scripture files
    if not DATA_DIR.exists():
        print(f"Creating data directory: {DATA_DIR}")
        DATA_DIR.mkdir(exist_ok=True)
        print("\nPlease add scripture text files to the data/ directory")
        print("Expected format: bhagavad_gita.txt, srimad_bhagavatam.txt, etc.")
        return
    
    scripture_files = list(DATA_DIR.glob("*.txt"))
    if not scripture_files:
        print("\n ⚠️  No scripture files found in data/ directory")
        print("Please add .txt files with scripture content")
        return
    
    print(f"\nFound {len(scripture_files)} scripture files:")
    for f in scripture_files:
        print(f"  - {f.name}")
    
    print("\nStarting embedding process...")
    
    total_chunks = 0
    for scripture_file in scripture_files:
        scripture_name = scripture_file.stem
        
        # Skip if already embedded
        output_file = EMBEDDINGS_DIR / f"{scripture_name}_embeddings.json"
        if output_file.exists():
            print(f"⏭️  Skipping {scripture_name} (already embedded)")
            continue
        
        with open(scripture_file, "r", encoding="utf-8") as f:
            text_content = f.read()
        
        chunks = embed_scripture(scripture_name, text_content)
        total_chunks += chunks
    
    print(f"\n{'=' * 50}")
    print(f"✓ Embedding complete!")
    print(f"  Total scriptures: {len(scripture_files)}")
    print(f"  Total chunks: {total_chunks}")
    print(f"  Embeddings saved to: {EMBEDDINGS_DIR}")


if __name__ == "__main__":
    main()
