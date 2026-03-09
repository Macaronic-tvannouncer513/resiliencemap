# ResilienceMap 🛰️
### Open-Source Community Disaster Risk Intelligence Platform

[![CI](https://github.com/henok256/resiliencemap/actions/workflows/ci.yml/badge.svg)](https://github.com/henok256/resiliencemap/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)

> Bridging federal hazard datasets and local decision-making — built for the municipalities that need it most.

---

## The Problem

Thousands of US municipalities — especially smaller and underserved ones — lack the technical capacity to assess disaster risk in real time. FEMA, USGS, NOAA, and the US Census Bureau publish rich public datasets, but they are siloed, inconsistent in format, and require GIS expertise most local emergency managers do not have.

**ResilienceMap solves this** by ingesting those datasets, computing composite risk scores per census tract, and exposing them through a clean REST API and interactive map dashboard — with zero GIS expertise required on the consumer side.

---

## Features

- 📥 **Automated ingestion** of FEMA flood zones (NFHL), USGS earthquake data, and NOAA storm alerts
- 🗺️ **Geospatial risk scoring** per US census tract using PostGIS spatial joins
- 🔌 **REST API** — query risk by county FIPS code, retrieve active alerts, export GeoJSON
- 🗺️ **Interactive map dashboard** powered by Leaflet.js
- 🔔 **Configurable alerting** — webhook/email triggers when NOAA issues watches or warnings
- 🐳 **One-command setup** via Docker Compose

---

## Quickstart

```bash
# 1. Clone the repo
git clone https://github.com/henok256/resiliencemap.git
cd resiliencemap

# 2. Copy environment config
cp .env.example .env

# 3. Start all services (API + PostGIS + dashboard)
docker compose up --build

# 4. Run initial data ingestion
docker compose exec api python -m ingestion.fema.ingest_flood_zones
docker compose exec api python -m ingestion.usgs.ingest_earthquakes

# 5. Open the dashboard
open http://localhost:8000/dashboard
```

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/risk/county/{fips}` | Composite risk scores for all tracts in a county |
| GET | `/api/v1/risk/tract/{geoid}` | Risk score for a single census tract |
| GET | `/api/v1/hazards/geojson` | All active hazard layers as GeoJSON FeatureCollection |
| GET | `/api/v1/alerts/active` | Current NOAA watches & warnings |
| GET | `/health` | Health check |

Full API docs available at `http://localhost:8000/docs` (Swagger UI).

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                      Data Sources                        │
│   FEMA NFHL    USGS Earthquake    NOAA NWS    US Census  │
└────────┬───────────────┬──────────────┬──────────┬───────┘
         │               │              │          │
         ▼               ▼              ▼          ▼
┌─────────────────────────────────────────────────────────┐
│                  Ingestion Layer (Python)                 │
│     GeoPandas · Requests · Scheduled via cron/Airflow    │
└──────────────────────────┬──────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│               PostGIS (PostgreSQL + spatial)             │
│    census_tracts · flood_zones · seismic_hazard ·        │
│    storm_alerts · risk_scores                            │
└──────────────────────────┬──────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│               FastAPI Backend                            │
│         Risk API · Hazard API · Alert API                │
└──────────────────────────┬──────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│            Leaflet.js Map Dashboard                      │
└─────────────────────────────────────────────────────────┘
```

---

## Project Structure

```
resiliencemap/
├── app/                    # FastAPI application
│   ├── api/routes/         # Endpoint handlers
│   ├── core/               # Config, logging, settings
│   ├── db/                 # Database session, migrations
│   ├── models/             # SQLAlchemy ORM models
│   └── schemas/            # Pydantic request/response schemas
├── ingestion/              # Data ingestion modules
│   ├── fema/               # FEMA NFHL flood zone ingestion
│   ├── usgs/               # USGS earthquake data ingestion
│   └── noaa/               # NOAA NWS storm alerts ingestion
├── processing/             # Risk scoring algorithms
├── dashboard/              # Leaflet.js frontend
├── tests/                  # Unit and integration tests
├── scripts/                # DB seed, migration helpers
├── docs/                   # Methodology documentation
├── docker-compose.yml
├── Dockerfile
└── pyproject.toml
```

---

## Contributing

We welcome contributions! Please read [CONTRIBUTING.md](CONTRIBUTING.md) before opening a PR.

This project is especially looking for:
- GIS/geospatial engineers
- Emergency management professionals who can validate risk models
- Frontend contributors (Leaflet.js / React)

---

## Methodology

Risk scoring methodology is documented in [`docs/methodology.md`](docs/methodology.md). The composite risk score per census tract is a weighted function of:
- **Flood risk** — FEMA Special Flood Hazard Area (SFHA) coverage %
- **Seismic risk** — USGS Peak Ground Acceleration (PGA) percentile
- **Storm exposure** — Active NOAA watches/warnings in the past 30 days
- **Social vulnerability** — CDC/ATSDR SVI score for the tract

---

## License

MIT — see [LICENSE](LICENSE).

---

## Citation

If you use ResilienceMap in research or policy work, please cite:

```bibtex
@software{resiliencemap2025,
  title  = {ResilienceMap: Open-Source Community Disaster Risk Intelligence Platform},
  author = {Mengesha, Henok},
  year   = {2025},
  url    = {https://github.com/henok256/resiliencemap}
}
```
