import json
import urllib.request
import os
from pathlib import Path

def fetch_monsters():
    output_dir = Path("D&D Character Creator V3/src/cc_v3/data")
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / "monsters.json"
    
    # We will fetch SRD monsters from open5e
    url = "https://api.open5e.com/v1/monsters/?limit=2000"
    print(f"Fetching monsters from {url}...")
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
        
        results = data.get("results", [])
        
        # Clean up / prune fields we don't need if desired, but for now we keep the full SRD object
        # which has name, hp, ac, abilities, actions, etc.
        
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
            
        print(f"Generated successfully. Wrote {len(results)} monsters to {out_path}")
        
    except Exception as e:
        print(f"Failed to fetch monsters: {e}")

if __name__ == "__main__":
    fetch_monsters()
