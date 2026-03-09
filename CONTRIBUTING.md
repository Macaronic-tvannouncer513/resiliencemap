# Contributing to ResilienceMap

Thank you for your interest in contributing! ResilienceMap is a public good project — every contribution
directly improves disaster preparedness tooling for municipalities across the US.

---

## Getting Started

1. **Fork** the repository and clone your fork locally
2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -e ".[dev]"
   ```
3. Copy `.env.example` to `.env` and fill in values
4. Start PostGIS locally: `docker compose up db -d`
5. Run tests to confirm your setup: `pytest`

---

## Development Workflow

- Branch naming: `feature/your-feature`, `fix/issue-description`, `docs/topic`
- Commit style: [Conventional Commits](https://www.conventionalcommits.org/)
  - `feat: add NOAA alert webhook support`
  - `fix: correct FEMA projection transformation`
  - `docs: update methodology for seismic scoring`
- Open a PR against `main` with a clear description of what and why

---

## Areas Where We Need Help

| Area | Skills Needed |
|------|--------------|
| Risk model validation | Emergency management, GIS |
| Additional hazard layers (wildfire, drought) | Python, GeoPandas |
| Frontend dashboard improvements | Leaflet.js, JavaScript |
| API performance optimization | FastAPI, PostGIS |
| Documentation & tutorials | Technical writing |

---

## Code Standards

- Python 3.11+, type hints everywhere
- `ruff` for linting, `black` for formatting
- Minimum 80% test coverage for new modules
- All geospatial operations must preserve/explicitly set CRS (EPSG:4326 for storage)

---

## Reporting Issues

Please use GitHub Issues with the appropriate label:
- `bug` — something is broken
- `enhancement` — new feature request
- `data-source` — issues with upstream data (FEMA/USGS/NOAA)
- `documentation` — gaps in docs

---

## Code of Conduct

Be respectful, constructive, and welcoming. This project serves communities — that culture starts here.
