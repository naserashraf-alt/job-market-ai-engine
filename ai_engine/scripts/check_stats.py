import json
import os
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

dataset_path = os.path.join(os.path.dirname(__file__), "..", "data", "processed", "jobs_dataset.json")

if os.path.exists(dataset_path):
    with open(dataset_path, "r", encoding="utf-8") as f:
        jobs = json.load(f)
        
    print(f"📊 Dataset Statistics:")
    print(f"  ├ Total Unique Jobs Saved: {len(jobs)}")
    
    # Sources breakdown
    sources = {}
    egypt_count = 0
    categories = {}
    
    for j in jobs:
        src = j.get("source_api", "Unknown")
        sources[src] = sources.get(src, 0) + 1
        
        cat = j.get("category", "General")
        categories[cat] = categories.get(cat, 0) + 1
        
        if "Egypt" in j.get("location", "") or j.get("country") == "Egypt":
            egypt_count += 1
            
    print(f"  ├ Jobs in Egypt 🇪🇬: {egypt_count}")
    print("\n📌 Sources Breakdown:")
    for s, c in sources.items():
        print(f"  ├ {s}: {c} jobs")
        
    print("\n📌 Categories Sample:")
    for cat, count in list(categories.items())[:10]:
        print(f"  ├ {cat}: {count} jobs")
else:
    print("Dataset file not found.")
