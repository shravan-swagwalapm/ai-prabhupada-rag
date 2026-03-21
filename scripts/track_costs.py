#!/usr/bin/env python3
"""Cost tracking for Voyage AI embeddings"""
import json
import os
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
COST_LOG = PROJECT_ROOT / "cost_log.json"
COST_CSV = PROJECT_ROOT / "cost_log.csv"

# Voyage AI pricing
VOYAGE_3_LARGE_COST_PER_1M_TOKENS = 0.12  # $0.12 per 1M tokens

def estimate_tokens(text: str) -> int:
    """Rough token estimate (1 token ≈ 4 characters)"""
    return len(text) // 4

def log_embedding_cost(scripture_name: str, text: str, actual_cost: float = None):
    """Log embedding cost for tracking"""
    tokens = estimate_tokens(text)
    estimated_cost = (tokens / 1_000_000) * VOYAGE_3_LARGE_COST_PER_1M_TOKENS
    
    entry = {
        "date": datetime.now().isoformat(),
        "scripture": scripture_name,
        "tokens": tokens,
        "estimated_cost_usd": round(estimated_cost, 4),
        "actual_cost_usd": actual_cost if actual_cost else round(estimated_cost, 4)
    }
    
    # Load existing log
    if COST_LOG.exists():
        with open(COST_LOG, "r") as f:
            log_data = json.load(f)
    else:
        log_data = {"entries": [], "total_cost": 0.0, "budget": 10.0}
    
    # Add entry
    log_data["entries"].append(entry)
    log_data["total_cost"] = round(log_data["total_cost"] + entry["actual_cost_usd"], 4)
    
    # Save JSON log
    with open(COST_LOG, "w") as f:
        json.dump(log_data, f, indent=2)
    
    # Save CSV log (append)
    csv_exists = COST_CSV.exists()
    with open(COST_CSV, "a") as f:
        if not csv_exists:
            f.write("Date,Scripture,Tokens,Estimated_Cost_USD,Actual_Cost_USD\\n")
        f.write(f"{entry['date']},{entry['scripture']},{entry['tokens']},"
                f"{entry['estimated_cost_usd']},{entry['actual_cost_usd']}\\n")
    
    # Print summary
    remaining = log_data["budget"] - log_data["total_cost"]
    print(f"\\n💰 Cost Tracking:")
    print(f"   Scripture: {scripture_name}")
    print(f"   Tokens: {tokens:,}")
    print(f"   Cost: ${entry['actual_cost_usd']:.4f}")
    print(f"   Total spent: ${log_data['total_cost']:.4f}")
    print(f"   Budget remaining: ${remaining:.2f}")
    
    if remaining < 1.0:
        print(f"   ⚠️  WARNING: Low budget (<$1 remaining)")
    
    return entry

def show_summary():
    """Show cost summary"""
    if not COST_LOG.exists():
        print("No cost log found. Run embeddings first.")
        return
    
    with open(COST_LOG, "r") as f:
        log_data = json.load(f)
    
    print("\\n" + "="*50)
    print("COST SUMMARY")
    print("="*50)
    print(f"Budget: ${log_data['budget']:.2f}")
    print(f"Total Spent: ${log_data['total_cost']:.4f}")
    print(f"Remaining: ${log_data['budget'] - log_data['total_cost']:.2f}")
    print(f"\\nEmbeddings: {len(log_data['entries'])}")
    print("\\nRecent entries:")
    for entry in log_data["entries"][-5:]:
        print(f"  {entry['date'][:10]} | {entry['scripture']:30s} | "
              f"{entry['tokens']:8,} tokens | ${entry['actual_cost_usd']:.4f}")

if __name__ == "__main__":
    show_summary()
