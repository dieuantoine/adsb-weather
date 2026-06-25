from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

_MISSING = 999999.0


def _split(line: str) -> list[str]:
    return line.rstrip("\n").rstrip(",").split(",")


def _read_ascent(path: Path) -> pd.DataFrame:

    lines = Path(path).read_text(encoding="utf-8", errors="replace").splitlines()

    h = next(i for i, line in enumerate(lines) if line.startswith("numer_sta"))

    meta = dict(zip(_split(lines[h]), _split(lines[h + 1]), strict=False))
    nb_niv = int(meta["nb_niv"])
    cols = _split(lines[h + 2])
    rows = [_split(lines[h + 3 + k]) for k in range(nb_niv)]

    df = pd.DataFrame(rows, columns=cols).apply(pd.to_numeric, errors="coerce")
    df = df.mask(df >= _MISSING)

    launch = datetime.strptime(meta["date"], "%Y%m%d%H%M%S").replace(tzinfo=UTC)
    date_heure = pd.to_datetime(launch) + pd.to_timedelta(df["dur_dep"], unit="s")

    return pd.DataFrame(
        {
            "numer_sta": meta["numer_sta"],
            "dep_lat": df["dep_lat"],
            "dep_lon": df["dep_lon"],
            "altitude": df["altitude"],
            "date_heure": date_heure,
            "p_niv": df["p_niv"],
            "t": df["t"],
            "ff": df["ff"],
            "dd": df["dd"],
        }
    )


def build_parquet(
    input_dir: str | Path, output_path: str | Path = "radiosondages.parquet"
) -> pd.DataFrame:
    files = sorted(Path(input_dir).glob("*HR_complet.csv"))
    if not files:
        raise FileNotFoundError(f"aucun *_HR_complet.csv dans {input_dir}")
    df = pd.concat((_read_ascent(f) for f in files), ignore_index=True)
    df.to_parquet(output_path, index=False)
    return df


if __name__ == "__main__":
    in_dir = "data/raw/rs"
    out = "data/interim/rs_complets.parquet"
    df = build_parquet(in_dir, out)
    print(f"{len(df)} lignes | {df['numer_sta'].nunique()} station(s) -> {out}\n")
    print(df.head(), "\n")
    print(df.dtypes)
