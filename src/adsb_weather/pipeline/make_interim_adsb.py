import argparse
import json
import sys
from pathlib import Path

import pandas as pd

# (champ_source, colonne_sortie)
FIELDS: list[tuple[str, str]] = [
    ("hex", "icao"),
    ("flight", "callsign"),
    ("alt_baro", "alt_baro_ft"),
    ("alt_geom", "alt_geom_ft"),
    ("lat", "lat"),
    ("lon", "lon"),
    ("gs", "gs_kt"),
    ("ias", "ias_kt"),
    ("tas", "tas_kt"),
    ("mach", "mach"),
    ("track", "track_deg"),
    ("mag_heading", "heading_deg"),
    ("baro_rate", "baro_rate_fpm"),
    ("geom_rate", "geom_rate_fpm"),
    ("nav_qnh", "nav_qnh_hpa"),
    ("seen_pos", "seen_pos_s"),
    ("rssi", "rssi_dbm"),
]

# REQUIRED_FIELDS = {"alt_baro"}


def extract_snapshot(snapshot: dict) -> list[dict]:

    timestamp = snapshot.get("_captured_at")
    rows = []

    for ac in snapshot.get("aircraft", []):
        # if not REQUIRED_FIELDS.issubset(ac):
        #     continue

        row: dict = {"timestamp": timestamp}

        for src, dst in FIELDS:
            val = ac.get(src)
            if dst == "callsign" and isinstance(val, str):
                val = val.strip() or None
            row[dst] = val

        row["has_ehs"] = (ac.get("tas") is not None) and (ac.get("mach") is not None)

        rows.append(row)

    return rows


def process_raw_dir(raw_dir: Path, out_dir: Path) -> None:
    jsonl_files = sorted(raw_dir.glob("*.jsonl"))
    if not jsonl_files:
        print(f"Aucun fichier .jsonl trouvé dans {raw_dir}", file=sys.stderr)
        sys.exit(1)

    all_rows: list[dict] = []

    for path in jsonl_files:
        print(f"[make_interim_adsb] Lecture : {path.name}")
        with path.open(encoding="utf-8") as f:
            for lineno, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    snapshot = json.loads(line)
                except json.JSONDecodeError as e:
                    print(
                        f"  [!] Ligne {lineno} invalide ({e}), ignorée.",
                        file=sys.stderr,
                    )
                    continue
                all_rows.extend(extract_snapshot(snapshot))

    if not all_rows:
        print("[make_interim_adsb] Aucune observation extraite.", file=sys.stderr)
        sys.exit(1)

    df = pd.DataFrame(all_rows)

    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    df["icao"] = df["icao"].astype("string")
    df["callsign"] = df["callsign"].astype("string")
    df["has_ehs"] = df["has_ehs"].astype(bool)

    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "observations.parquet"
    df.to_parquet(out_path, index=False)

    n_total = len(df)
    n_pos = df["lat"].notna().sum()
    n_ehs = df["has_ehs"].sum()
    print(f"[make_interim_adsb] {n_total} observations écrites dans {out_path}")
    print(f"  dont {n_pos} avec position lat/lon ({100 * n_pos / n_total:.1f} %)")
    print(f"  dont {n_ehs} avec EHS (tas+mach) ({100 * n_ehs / n_total:.1f} %)")


def main() -> None:
    parser = argparse.ArgumentParser(description="raw JSONL → interim parquet")
    parser.add_argument(
        "--raw",
        type=Path,
        default=Path("data/raw"),
        help="Dossier contenant les fichiers .jsonl (défaut: data/raw)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("data/interim"),
        help="Dossier de sortie (défaut: data/interim)",
    )
    args = parser.parse_args()
    process_raw_dir(args.raw, args.out)


if __name__ == "__main__":
    main()
