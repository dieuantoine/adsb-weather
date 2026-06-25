import json
import time
from datetime import UTC, datetime
from pathlib import Path

AIRCRAFT_JSON = Path("/run/dump1090-fa/aircraft.json")
OUTPUT_PATH = Path("data/raw/aircraft_snapshots.jsonl")
INTERVAL_S = 10

OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

with OUTPUT_PATH.open("a", encoding="utf-8") as out:
    while True:
        with AIRCRAFT_JSON.open(encoding="utf-8") as f:
            snapshot = json.load(f)
        snapshot["_captured_at"] = datetime.now(UTC).isoformat()
        out.write(json.dumps(snapshot, ensure_ascii=False) + "\n")
        out.flush()
        print(snapshot["_captured_at"], len(snapshot.get("aircraft", [])), "avions")
        time.sleep(INTERVAL_S)
