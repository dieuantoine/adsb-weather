import argparse

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from adsb_weather.physics.pressure import pressure_ia

_ABS = "#c1666b"  # erreur absolue (Pa)
_PCT = "#2e6f95"  # erreur relative (%)


def _err_panel(ax, x, abs_mean, pct_mean, xlabel, title):
    """Trace P_err (axe gauche) et P_err% (axe droit) vs x."""
    (l1,) = ax.plot(x, abs_mean, color=_ABS, marker=".", lw=1, label="$P_{err}$ (Pa)")
    ax.axhline(0, color="k", lw=0.8, ls="--")
    ax.set_xlabel(xlabel)
    ax.set_ylabel("$P_{err}$ moyen (Pa)", color=_ABS)
    ax.tick_params(axis="y", labelcolor=_ABS)
    ax.set_title(title)

    ax2 = ax.twinx()
    (l2,) = ax2.plot(x, pct_mean, color=_PCT, marker=".", lw=1, label="$P_{err}$ (%)")
    ax2.set_ylabel("$P_{err}$ moyen (%)", color=_PCT)
    ax2.tick_params(axis="y", labelcolor=_PCT)
    ax.legend(handles=[l1, l2], fontsize=9, loc="lower right")


def analyse(parquet, station=None, out="reports/pression_isotherme.png"):
    df = pd.read_parquet(parquet)
    if station:
        df = df[df["numer_sta"] == station]

    df = df.dropna(subset=["altitude", "p_niv", "t"]).copy()
    df["p_hyp"] = pressure_ia(df["altitude"])
    df["p_err"] = df["p_niv"] - df["p_hyp"]
    df["p_err_pct"] = df["p_err"] / df["p_niv"] * 100

    pe = df["p_err"]
    print(f"{len(df)} niveaux")
    print(
        f"P_err (Pa) : moyenne={pe.mean():.0f}  médiane={pe.median():.0f}  "
        f"écart-type={pe.std():.0f}  [{pe.min():.0f}, {pe.max():.0f}]"
    )
    print(
        f"P_err (%)  : moyenne={df['p_err_pct'].mean():.1f}  "
        f"[{df['p_err_pct'].min():.1f}, {df['p_err_pct'].max():.1f}]"
    )

    # tranches de température (2 K)
    tbins = np.arange(df["t"].min() // 2 * 2, df["t"].max() + 2, 2)
    t_bin = pd.cut(df["t"], tbins)
    t_abs = df.groupby(t_bin, observed=True)["p_err"].mean()
    t_pct = df.groupby(t_bin, observed=True)["p_err_pct"].mean()
    t_centers = [iv.mid for iv in t_abs.index]

    # tranches d'altitude (500 m)
    abins = np.arange(0, df["altitude"].max() + 500, 500)
    a_bin = pd.cut(df["altitude"], abins)
    g = df.groupby(a_bin, observed=True)["p_niv"]
    p_mean, p_q1, p_q3 = g.mean(), g.quantile(0.25), g.quantile(0.75)
    a_abs = df.groupby(a_bin, observed=True)["p_err"].mean()
    a_pct = df.groupby(a_bin, observed=True)["p_err_pct"].mean()
    a_centers = np.array([iv.mid for iv in p_mean.index])
    p_hyp_prof = pressure_ia(a_centers)

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    ax1, ax2, ax3, ax4 = axes.ravel()

    ax1.hist(pe, bins=70, color="#3a6ea5", edgecolor="none")
    ax1.axvline(0, color="k", lw=0.8, ls="--")
    ax1.set_title("Répartition de $P_{err} = P - P_{hyp}$")
    ax1.set_xlabel("$P_{err}$ (Pa)")
    ax1.set_ylabel("nb de niveaux")

    _err_panel(
        ax2,
        t_centers,
        t_abs.values,
        t_pct.values,
        "Température (K)",
        "$P_{err}$ en fonction de la température",
    )

    ax3.fill_between(
        a_centers, p_q1, p_q3, color="#3a6ea5", alpha=0.25, label="P réelle (Q1–Q3)"
    )
    ax3.plot(a_centers, p_mean, color="#3a6ea5", lw=1.5, label="P réelle moyenne")
    ax3.plot(
        a_centers,
        p_hyp_prof,
        color=_ABS,
        ls="--",
        lw=1.5,
        label="$P_{hyp}$ (isotherme)",
    )
    ax3.set_title("Profil de pression vs altitude")
    ax3.set_xlabel("Altitude (m)")
    ax3.set_ylabel("Pression (Pa)")
    ax3.legend(fontsize=9)

    _err_panel(
        ax4,
        a_centers,
        a_abs.values,
        a_pct.values,
        "Altitude (m)",
        "$P_{err}$ en fonction de l'altitude",
    )

    fig.tight_layout()
    fig.savefig(out, dpi=130, bbox_inches="tight")
    print(f"figure -> {out}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("parquet", default="data/interim/rs_complets.parquet")
    p.add_argument("--station", default=None)
    p.add_argument("--out", default="reports/pression_isotherme.png")
    a = p.parse_args()
    analyse(a.parquet, a.station, a.out)
