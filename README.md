# adsb-weather

[![CI](https://github.com/dieuantoine/adsb-weather/actions/workflows/ci.yml/badge.svg)](https://github.com/dieuantoine/adsb-weather/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Estimation des conditions atmosphériques à partir de données d’avion (ADS-B / Mode-S) **WiP**

## Objectif

Reconstruire des mesures de température de l'air et de vent à partir des données transmises par les avions et évaluer la pertinence du modèle en comparant aux mesures de radiosondages Météo-France.

S'appuie sur le travail de Sun et al. (*Weather field reconstruction using aircraft surveillance data and a novel meteo-particle
model*, PLoS ONE, 2018).

## Architecture

| Environnement | Rôle |
|---|---|
| Raspberry Pi + SDR | Capture brute des messages 1090 MHz |
| PC | Décodage pyModeS, calcul, analyse |

```text
src/adsb_weather/
├── acquisition/   # capture + décodage → JSONL ; radiosondages Météo-France
├── physics/       # calculs température / pression
├── pipeline/      # orchestration
└── analysis/      # analyses
data/
├── raw/           # données brutes
├── interim/       # données nettoyées
└── processed/     # données avec température / pression calculées
```

## Installation

Le projet utilise [uv](https://docs.astral.sh/uv/). Après avoir cloné le dépôt :

```bash
uv sync
```

uv installe automatiquement la bonne version de Python et toutes les dépendances.


## Licence

MIT - voir [LICENSE](LICENSE).
