#!/usr/bin/env python3
"""
AI Prabhupada RAG - Scripture Embedding Script WITH RESUME SUPPORT
Saves progress incrementally - no more losing work!
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

CHECKPOINT_INTERVAL = 50  # Save every 50 batches


def create_embeddings_batch(texts: list) -> list:
    """Create embeddings for multiple texts using Voyage AI (batch)"""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {VOYAGE_API_KEY}"
    }
    
    # Voyage AI has a max input limit - truncate very long chunks
    cleaned_texts = []
    for text in texts:
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
        raise


def chunk_text(text: str, max_tokens: int = 400, overlap: int = 50) -> list:
    """Split text into overlapping chunks"""
    sentences = text.split(". ")
    chunks = []
    current_chunk = []
    current_length = 0
    
    for sentence in sentences:
        sentence_length = len(sentence.split())
        
        if current_length + sentence_length > max_tokens and current_chunk:
            chunks.append(". ".join(current_chunk) + ".")
            current_chunk = current_chunk[-overlap//20:] if overlap else []
            current_length = sum(len(s.split()) for s in current_chunk)
        
        current_chunk.append(sentence)
        current_length += sentence_length
    
    if current_chunk:
        chunks.append(". ".join(current_chunk) + ".")
    
    return chunks


def save_embeddings(scripture_name: str, embeddings_data: list, final: bool = False):
    """Save embeddings to file"""
    output_file = EMBEDDINGS_DIR / f"{scripture_name}_embeddings.json"
    
    data = {
        "scripture": scripture_name,
        "model": EMBEDDING_MODEL,
        "total_chunks": len(embeddings_data),
        "complete": final,
        "chunks": embeddings_data
    }
    
    # Write to temp file first, then rename (atomic operation)
    temp_file = output_file.with_suffix('.json.tmp')
    with open(temp_file, "w") as f:
        json.dump(data, f, indent=2)
    temp_file.replace(output_file)
    
    return output_file


def load_existing_embeddings(scripture_name: str):
    """Load existing embeddings if they exist"""
    output_file = EMBEDDINGS_DIR / f"{scripture_name}_embeddings.json"
    
    if not output_file.exists():
        return None, 0
    
    try:
        with open(output_file, "r") as f:
            data = json.load(f)
        
        if data.get("complete", False):
            print(f"  ✓ Already complete ({len(data['chunks'])} chunks)")
            return None, -1  # Signal: skip entirely
        
        embeddings = data.get("chunks", [])
        print(f"  🔄 Resuming from chunk {len(embeddings)}")
        return embeddings, len(embeddings)
    except Exception as e:
        print(f"  ⚠️  Error loading existing embeddings: {e}")
        return None, 0


def embed_scripture(scripture_name: str, text_content: str):
    """Embed a scripture text and save incrementally"""
    print(f"\nProcessing {scripture_name}...")
    
    # Check for existing progress
    existing_embeddings, start_chunk = load_existing_embeddings(scripture_name)
    
    if start_chunk == -1:
        # Already complete
        return 0
    
    # Create all chunks
    all_chunks = chunk_text(text_content)
    total_chunks = len(all_chunks)
    print(f"  Total chunks: {total_chunks}")
    
    # Initialize embeddings list
    if existing_embeddings:
        embeddings_data = existing_embeddings
        chunks_to_process = all_chunks[start_chunk:]
    else:
        embeddings_data = []
        chunks_to_process = all_chunks
        start_chunk = 0
    
    if not chunks_to_process:
        print(f"  ✓ Nothing to process!")
        return 0
    
    print(f"  Processing {len(chunks_to_process)} chunks (starting from {start_chunk+1})")
    
    # Batch embedding
    BATCH_SIZE = 50
    total_batches = (len(chunks_to_process) - 1) // BATCH_SIZE + 1
    
    for batch_idx in range(0, len(chunks_to_process), BATCH_SIZE):
        batch_num = batch_idx // BATCH_SIZE + 1
        batch_end = min(batch_idx + BATCH_SIZE, len(chunks_to_process))
        batch_chunks = chunks_to_process[batch_idx:batch_end]
        
        actual_chunk_start = start_chunk + batch_idx
        actual_chunk_end = start_chunk + batch_end
        
        print(f"  Batch {batch_num}/{total_batches} (chunks {actual_chunk_start+1}-{actual_chunk_end}/{total_chunks})...", end="", flush=True)
        
        try:
            batch_embeddings = create_embeddings_batch(batch_chunks)
            
            for i, (chunk, embedding) in enumerate(zip(batch_chunks, batch_embeddings)):
                embeddings_data.append({
                    "chunk_id": actual_chunk_start + i,
                    "text": chunk,
                    "embedding": embedding
                })
            
            print(" ✓")
            
            # Save checkpoint every N batches
            if batch_num % CHECKPOINT_INTERVAL == 0 or batch_num == total_batches:
                save_embeddings(scripture_name, embeddings_data, final=False)
                print(f"  💾 Checkpoint saved ({len(embeddings_data)} chunks)")
        
        except Exception as e:
            print(f" ❌ Error: {e}")
            # Save what we have so far
            save_embeddings(scripture_name, embeddings_data, final=False)
            print(f"  💾 Progress saved before error!")
            raise
    
    # Mark as complete
    output_file = save_embeddings(scripture_name, embeddings_data, final=True)
    print(f"  ✅ Complete! Saved to {output_file.name}")
    
    return len(chunks_to_process)


def main():
    """Main embedding pipeline"""
    import sys

    print("━" * 70)
    print("🔄 AI Prabhupada RAG - RESUMABLE Scripture Embedding")
    print("━" * 70)
    print()

    # Accept specific file from command line
    if len(sys.argv) > 1:
        scripture_file = Path(sys.argv[1])
        if not scripture_file.exists():
            print(f"⚠️  File not found: {scripture_file}")
            return
        scripture_files = [scripture_file]
        print(f"Processing specific file: {scripture_file.name}\n")
    else:
        scripture_files = list(DATA_DIR.glob("*.txt"))
        if not scripture_files:
            print("⚠️  No scripture files found")
            return
        print(f"Found {len(scripture_files)} scripture files\n")
    
    total_processed = 0
    for scripture_file in scripture_files:
        scripture_name = scripture_file.stem
        
        with open(scripture_file, "r", encoding="utf-8") as f:
            text_content = f.read()
        
        chunks = embed_scripture(scripture_name, text_content)
        total_processed += chunks
    
    print()
    print("━" * 70)
    print(f"✅ Embedding complete! Processed {total_processed} new chunks")
    print("━" * 70)


if __name__ == "__main__":
    main()
