import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import pandas as pd


def section(title: str) -> str:
    bar = "=" * 60
    return f"\n{bar}\n{title}\n{bar}\n"


def subsection(title: str) -> str:
    return f"\n--- {title} ---\n"


def save_fig(fig: plt.Figure, path: Path, name: str) -> Path:
    out = path / name
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return out


# ---------------------------------------------------------------------------
# Sections d'analyse
# ---------------------------------------------------------------------------


def analyse_volume(df: pd.DataFrame) -> str:
    lines = [section("1. VOLUME ET COUVERTURE TEMPORELLE")]

    n_rows = len(df)
    n_snapshots = df["timestamp"].nunique()
    n_icao = df["icao"].nunique()
    t_min = df["timestamp"].min()
    t_max = df["timestamp"].max()
    duration = t_max - t_min

    lines.append(f"Observations totales     : {n_rows:>10,}")
    lines.append(f"Snapshots uniques        : {n_snapshots:>10,}")
    lines.append(f"Avions uniques (ICAO)    : {n_icao:>10,}")
    lines.append(f"Premier snapshot         : {t_min}")
    lines.append(f"Dernier snapshot         : {t_max}")
    lines.append(f"Durée couverte           : {duration}")

    # Observations par snapshot
    per_snap = df.groupby("timestamp").size()
    lines.append(subsection("Observations par snapshot"))
    lines.append(f"  min    : {per_snap.min()}")
    lines.append(f"  median : {per_snap.median():.0f}")
    lines.append(f"  max    : {per_snap.max()}")

    return "\n".join(lines)


def analyse_completude(df: pd.DataFrame) -> str:
    lines = [section("2. COMPLÉTUDE DES CHAMPS")]

    champs = [
        ("lat", "Position lat/lon"),
        ("alt_baro_ft", "Altitude baro"),
        ("alt_geom_ft", "Altitude géom"),
        ("gs_kt", "Vitesse sol (gs)"),
        ("ias_kt", "IAS"),
        ("tas_kt", "TAS"),
        ("mach", "Mach"),
        ("track_deg", "Track"),
        ("heading_deg", "Cap magnétique"),
        ("baro_rate_fpm", "Baro rate"),
        ("geom_rate_fpm", "Geom rate"),
        ("nav_qnh_hpa", "Nav QNH"),
        ("seen_pos_s", "Seen pos"),
        ("rssi_dbm", "RSSI"),
        ("callsign", "Callsign"),
    ]

    n = len(df)
    lines.append(f"{'Champ':<25} {'Présents':>10} {'%':>7}")
    lines.append("-" * 45)
    for col, label in champs:
        if col not in df.columns:
            continue
        present = df[col].notna().sum()
        lines.append(f"{label:<25} {present:>10,} {100 * present / n:>6.1f}%")

    # EHS
    n_ehs = df["has_ehs"].sum()
    lines.append(f"\n{'EHS (tas + mach)':<25} {n_ehs:>10,} {100 * n_ehs / n:>6.1f}%")

    # EHS avec position
    n_ehs_pos = (df["has_ehs"] & df["lat"].notna()).sum()
    lines.append(
        f"{'EHS + position':<25} {n_ehs_pos:>10,} {100 * n_ehs_pos / n:>6.1f}%"
    )

    return "\n".join(lines)


def analyse_distributions(df: pd.DataFrame) -> str:
    lines = [section("3. DISTRIBUTIONS DES VALEURS CLÉS")]

    numeric_fields = [
        ("alt_baro_ft", "Altitude baro (ft)"),
        ("alt_geom_ft", "Altitude géom (ft)"),
        ("gs_kt", "Vitesse sol (kt)"),
        ("ias_kt", "IAS (kt)"),
        ("tas_kt", "TAS (kt)"),
        ("mach", "Mach"),
        ("baro_rate_fpm", "Baro rate (fpm)"),
        ("rssi_dbm", "RSSI (dBm)"),
        ("seen_pos_s", "Seen pos (s)"),
    ]

    for col, label in numeric_fields:
        if col not in df.columns:
            continue
        s = df[col].dropna()
        if len(s) == 0:
            continue
        lines.append(subsection(label))
        lines.append(f"  N       : {len(s):,}")
        lines.append(f"  min     : {s.min():.2f}")
        lines.append(f"  médiane : {s.median():.2f}")
        lines.append(f"  max     : {s.max():.2f}")
        lines.append(f"  moyenne : {s.mean():.2f}")
        lines.append(f"  std     : {s.std():.2f}")

    # Écart géom - baro
    df_both = df.dropna(subset=["alt_baro_ft", "alt_geom_ft"])
    if len(df_both) > 0:
        delta = df_both["alt_geom_ft"] - df_both["alt_baro_ft"]
        lines.append(subsection("Écart alt_geom - alt_baro (ft)"))
        lines.append(f"  N       : {len(delta):,}")
        lines.append(f"  min     : {delta.min():.0f}")
        lines.append(f"  médiane : {delta.median():.0f}")
        lines.append(f"  moyenne : {delta.mean():.2f}")
        lines.append(f"  max     : {delta.max():.0f}")
        lines.append(f"  std     : {delta.std():.2f}")

    return "\n".join(lines)


def analyse_aberrants(df: pd.DataFrame) -> str:
    lines = [section("4. VALEURS ABERRANTES")]

    # Mach > 1
    n_mach_sup1 = (df["mach"].dropna() > 1).sum()
    lines.append(f"Mach > 1                 : {n_mach_sup1:,}")

    # Mach < 0.1 (avions au sol ou erreur)
    n_mach_inf01 = (df["mach"].dropna() < 0.1).sum()
    lines.append(f"Mach < 0.1               : {n_mach_inf01:,}")

    # TAS incohérent avec Mach : on attend TAS ≈ Mach × vitesse_son
    # La vitesse du son varie entre ~295 m/s (haute altitude) et ~340 m/s (sol)
    # soit 573–661 kt. On vérifie juste que TAS/Mach est dans [500, 700] kt.
    df_ehs = df.dropna(subset=["tas_kt", "mach"]).copy()
    df_ehs = df_ehs[df_ehs["mach"] > 0]
    if len(df_ehs) > 0:
        ratio = df_ehs["tas_kt"] / df_ehs["mach"]
        n_incoherent = ((ratio < 500) | (ratio > 700)).sum()
        lines.append(
            f"TAS/Mach hors [500-700kt]: {n_incoherent:,}  "
            f"(ratio min={ratio.min():.0f}, max={ratio.max():.0f})"
        )

    # Altitude baro négative (sous le niveau de la mer)
    n_alt_neg = (df["alt_baro_ft"].dropna() < 0).sum()
    lines.append(f"alt_baro < 0 ft          : {n_alt_neg:,}")

    # Altitude baro > 60 000 ft (limite opérationnelle des avions commerciaux)
    n_alt_high = (df["alt_baro_ft"].dropna() > 60_000).sum()
    lines.append(f"alt_baro > 60 000 ft     : {n_alt_high:,}")

    # seen_pos > 60 s (position très périmée)
    n_stale = (df["seen_pos_s"].dropna() > 60).sum()
    lines.append(f"seen_pos > 60 s          : {n_stale:,}")

    return "\n".join(lines)


def analyse_palier(df: pd.DataFrame) -> str:
    lines = [section("5. AVIONS EN PALIER VS EN MANŒUVRE")]

    df_rate = df.dropna(subset=["baro_rate_fpm"])
    n = len(df_rate)

    seuils = [64, 200, 500]
    lines.append(f"{'Seuil |baro_rate|':<25} {'En palier':>10} {'%':>7}")
    lines.append("-" * 45)
    for seuil in seuils:
        n_palier = (df_rate["baro_rate_fpm"].abs() <= seuil).sum()
        lines.append(
            f"<= {seuil} fpm{'':<15} {n_palier:>10,} {100 * n_palier / n:>6.1f}%"
        )

    # Parmi les avions EHS, combien sont en palier (critère <= 200 fpm)
    df_ehs = df[df["has_ehs"]].dropna(subset=["baro_rate_fpm"])
    if len(df_ehs) > 0:
        n_ehs_palier = (df_ehs["baro_rate_fpm"].abs() <= 200).sum()
        lines.append(
            f"\nEHS + palier (<=200 fpm) : {n_ehs_palier:,} "
            f"({100 * n_ehs_palier / len(df_ehs):.1f}% des EHS avec baro_rate)"
        )

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Graphiques
# ---------------------------------------------------------------------------


def plot_altitude_histogram(df: pd.DataFrame, fig_dir: Path) -> Path:
    s = df["alt_baro_ft"].dropna()
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.hist(s, bins=80, color="#2c7bb6", edgecolor="none", alpha=0.85)
    ax.set_xlabel("Altitude baro (ft)")
    ax.set_ylabel("Nombre d'observations")
    ax.set_title("Distribution des altitudes barométriques")
    ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
    fig.tight_layout()
    return save_fig(fig, fig_dir, "01_altitude_histogram.png")


def plot_mach_distribution(df: pd.DataFrame, fig_dir: Path) -> Path:
    s = df.loc[df["has_ehs"], "mach"].dropna()
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.hist(s, bins=60, color="#1a9641", edgecolor="none", alpha=0.85)
    ax.axvline(1.0, color="red", linestyle="--", linewidth=1, label="Mach 1")
    ax.set_xlabel("Mach")
    ax.set_ylabel("Nombre d'observations")
    ax.set_title("Distribution du nombre de Mach (avions EHS)")
    ax.legend()
    fig.tight_layout()
    return save_fig(fig, fig_dir, "02_mach_distribution.png")


def plot_baro_rate(df: pd.DataFrame, fig_dir: Path) -> Path:
    s = df["baro_rate_fpm"].dropna()
    # Clip pour lisibilité (les valeurs extrêmes écrasent l'histogramme)
    s_clipped = s.clip(-5_000, 5_000)
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.hist(s_clipped, bins=100, color="#756bb1", edgecolor="none", alpha=0.85)
    ax.axvline(
        -200, color="orange", linestyle="--", linewidth=1, label="±200 fpm (palier)"
    )
    ax.axvline(200, color="orange", linestyle="--", linewidth=1)
    ax.set_xlabel("Baro rate (fpm) — clipé à ±5 000")
    ax.set_ylabel("Nombre d'observations")
    ax.set_title("Distribution du taux de montée/descente")
    ax.legend()
    fig.tight_layout()
    return save_fig(fig, fig_dir, "03_baro_rate.png")


def plot_rssi(df: pd.DataFrame, fig_dir: Path) -> Path:
    s = df["rssi_dbm"].dropna()
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.hist(s, bins=60, color="#636363", edgecolor="none", alpha=0.85)
    ax.set_xlabel("RSSI (dBm)")
    ax.set_ylabel("Nombre d'observations")
    ax.set_title("Distribution du niveau de signal reçu (RSSI)")
    fig.tight_layout()
    return save_fig(fig, fig_dir, "04_rssi.png")


def plot_positions(df: pd.DataFrame, fig_dir: Path) -> Path:
    df_pos = df.dropna(subset=["lat", "lon"])
    if len(df_pos) == 0:
        return None
    fig, ax = plt.subplots(figsize=(7, 6))
    ax.scatter(df_pos["lon"], df_pos["lat"], s=1, alpha=0.3, color="#2c7bb6")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_title(f"Positions des avions ({len(df_pos):,} observations avec lat/lon)")
    ax.set_aspect("equal")
    fig.tight_layout()
    return save_fig(fig, fig_dir, "05_positions.png")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyse exploratoire ADS-B interim")
    parser.add_argument("--interim", type=Path, default=Path("data/interim"))
    parser.add_argument("--reports", type=Path, default=Path("reports"))
    args = parser.parse_args()

    parquet_path = args.interim / "observations.parquet"
    if not parquet_path.exists():
        raise FileNotFoundError(f"Fichier introuvable : {parquet_path}")

    fig_dir = args.reports / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)

    print(f"Chargement de {parquet_path} ...")
    df = pd.read_parquet(parquet_path)
    print(f"  {len(df):,} lignes chargées.\n")

    # --- Rapport texte ---
    report_lines = ["RAPPORT D'ANALYSE ADS-B\n"]
    report_lines.append(f"Source : {parquet_path}")
    report_lines.append(f"Généré le : {pd.Timestamp.now()}\n")

    sections = [
        analyse_volume(df),
        analyse_completude(df),
        analyse_distributions(df),
        analyse_aberrants(df),
        analyse_palier(df),
    ]
    for s in sections:
        print(s)
        report_lines.append(s)

    report_path = args.reports / "adsb_analysis.txt"
    report_path.write_text("\n".join(report_lines), encoding="utf-8")
    print(f"\nRapport texte sauvegardé : {report_path}")

    # --- Figures ---
    figs = [
        ("Histogramme altitudes", plot_altitude_histogram(df, fig_dir)),
        ("Distribution Mach", plot_mach_distribution(df, fig_dir)),
        ("Baro rate", plot_baro_rate(df, fig_dir)),
        ("RSSI", plot_rssi(df, fig_dir)),
        ("Carte des positions", plot_positions(df, fig_dir)),
    ]
    print("\nFigures sauvegardées :")
    for label, path in figs:
        if path:
            print(f"  {label:<30} → {path}")


if __name__ == "__main__":
    main()
