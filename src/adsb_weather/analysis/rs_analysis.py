import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

_VARS = [
    ("altitude", "Altitude", "m"),
    ("p_niv", "Pression", "Pa"),
    ("t", "Température", "K"),
    ("ff", "Vitesse du vent", "m/s"),
    ("dep_lat", "Dérive latitude", "°"),
    ("dep_lon", "Dérive longitude", "°"),
]


def analyse(
    parquet: str | Path,
    station: str | None = None,
    out: str | Path = "distribution_radiosondages.png",
) -> None:
    df = pd.read_parquet(parquet)
    if station:
        df = df[df["numer_sta"] == station]
        if df.empty:
            raise SystemExit(f"aucune donnée pour la station {station}")

    print(
        f"{len(df)} niveaux | stations : "
        f"{', '.join(df['numer_sta'].value_counts().index.astype(str))}"
    )
    print(f"période : {df['date_heure'].min()} -> {df['date_heure'].max()}\n")
    print(df[[c for c, _, _ in _VARS] + ["dd"]].describe().round(2).to_string())

    fig = plt.figure(figsize=(14, 8))
    for i, (col, label, unit) in enumerate(_VARS, start=1):
        ax = fig.add_subplot(2, 4, i)
        ax.hist(df[col].dropna(), bins=60, color="#3a6ea5", edgecolor="none")
        ax.set_title(f"{label} ({unit})", fontsize=10)
        ax.set_ylabel("nb de niveaux", fontsize=8)
        ax.tick_params(labelsize=7)

    import numpy as np

    ax = fig.add_subplot(2, 4, 7, projection="polar")
    dd = df["dd"].dropna().to_numpy()
    bins = np.arange(0, 361, 15)
    counts, edges = np.histogram(dd, bins=bins)
    theta = np.deg2rad(edges[:-1] + 7.5)
    ax.bar(
        theta,
        counts,
        width=np.deg2rad(15),
        color="#c1666b",
        edgecolor="white",
        linewidth=0.3,
    )
    ax.set_theta_zero_location("N")
    ax.set_theta_direction(-1)
    ax.set_title("Direction du vent (°)", fontsize=10)
    ax.tick_params(labelsize=6)

    ax = fig.add_subplot(2, 4, 8)
    ax.hist(df["date_heure"], bins=40, color="#6b9080", edgecolor="none")
    ax.set_title("Couverture temporelle", fontsize=10)
    ax.set_ylabel("nb de niveaux", fontsize=8)
    ax.tick_params(labelsize=6, rotation=30)

    title = "Répartition des valeurs - radiosondages"
    if station:
        title += f" (station {station})"
    fig.suptitle(title, fontsize=13, y=1.0)
    fig.tight_layout()
    fig.savefig(out, dpi=130, bbox_inches="tight")
    print(f"\nfigure -> {out}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("parquet", default="data/interim/rs_complets.parquet")
    p.add_argument("--station", default=None)
    p.add_argument("--out", default="reports/distribution_radiosondages.png")
    a = p.parse_args()
    analyse(a.parquet, a.station, a.out)
