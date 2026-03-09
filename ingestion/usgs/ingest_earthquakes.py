"""
USGS Earthquake Catalog Ingestion
==================================

Fetches recent significant earthquake events from the USGS FDSN Event Web Service
and upserts them into PostGIS.

Data source: https://earthquake.usgs.gov/fdsnws/event/1/

Usage:
    # Ingest last 30 days of earthquakes magnitude 2.5+
    python -m ingestion.usgs.ingest_earthquakes

    # Ingest last 90 days, magnitude 3.0+
    python -m ingestion.usgs.ingest_earthquakes --days 90 --minmag 3.0
"""

import argparse
import logging
from datetime import UTC, datetime, timedelta

import requests
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models.hazard import SeismicHazard

logger = logging.getLogger(__name__)
settings = get_settings()

USGS_API_URL = settings.usgs_earthquake_api


def fetch_earthquakes(
    days_back: int = 30,
    min_magnitude: float = 2.5,
    us_only: bool = True,
) -> list[dict]:
    """
    Fetch earthquake events from USGS FDSN service.

    Args:
        days_back: how many days back to query
        min_magnitude: minimum Richter magnitude to include
        us_only: if True, restrict to CONUS + territories bounding box

    Returns:
        List of earthquake feature dicts from USGS GeoJSON response
    """
    end_time = datetime.now(UTC)
    start_time = end_time - timedelta(days=days_back)

    params: dict = {
        "format": "geojson",
        "starttime": start_time.strftime("%Y-%m-%dT%H:%M:%S"),
        "endtime": end_time.strftime("%Y-%m-%dT%H:%M:%S"),
        "minmagnitude": min_magnitude,
        "orderby": "time",
    }

    # Bounding box for US + territories
    if us_only:
        params.update(
            {
                "minlatitude": 17.0,
                "maxlatitude": 72.0,
                "minlongitude": -180.0,
                "maxlongitude": -65.0,
            }
        )

    logger.info("Fetching USGS earthquakes: last %d days, M%.1f+", days_back, min_magnitude)
    resp = requests.get(USGS_API_URL, params=params, timeout=30)
    resp.raise_for_status()

    data = resp.json()
    features = data.get("features", [])
    logger.info("USGS returned %d earthquake events", len(features))
    return features


def upsert_earthquakes(features: list[dict], db: Session) -> int:
    """
    Upsert earthquake events into the seismic_hazard table.

    Uses INSERT ... ON CONFLICT DO NOTHING via SQLAlchemy to avoid
    re-inserting events we already have (idempotent).

    Args:
        features: list of GeoJSON feature dicts from USGS
        db: SQLAlchemy session

    Returns:
        Number of new records inserted
    """
    inserted = 0
    skipped = 0

    for feature in features:
        props = feature.get("properties", {})
        geom = feature.get("geometry", {})
        usgs_id = feature.get("id")

        if not usgs_id or not geom:
            continue

        # Check if already exists
        exists = db.execute(
            text("SELECT 1 FROM seismic_hazard WHERE usgs_id = :id"),
            {"id": usgs_id},
        ).scalar()

        if exists:
            skipped += 1
            continue

        coords = geom.get("coordinates", [])
        if len(coords) < 2:
            continue

        lon, lat = coords[0], coords[1]
        depth_km = coords[2] if len(coords) > 2 else None

        # USGS returns time as Unix milliseconds
        event_ms = props.get("time")
        if not event_ms:
            continue
        event_time = datetime.fromtimestamp(event_ms / 1000, tz=UTC)

        wkt = f"SRID=4326;POINT({lon} {lat})"

        record = SeismicHazard(
            usgs_id=usgs_id,
            magnitude=float(props.get("mag", 0)),
            depth_km=float(depth_km) if depth_km is not None else None,
            place=props.get("place"),
            event_time=event_time.replace(tzinfo=None),  # store as UTC naive
            geom=wkt,
        )
        db.add(record)
        inserted += 1

        if inserted % 200 == 0:
            db.commit()
            logger.info("Committed %d seismic records...", inserted)

    db.commit()
    logger.info(
        "Seismic upsert complete: %d new, %d skipped (already existed)",
        inserted,
        skipped,
    )
    return inserted


def run_ingestion(days_back: int = 30, min_magnitude: float = 2.5) -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    db = SessionLocal()
    try:
        features = fetch_earthquakes(days_back=days_back, min_magnitude=min_magnitude)
        count = upsert_earthquakes(features, db)
        logger.info("Earthquake ingestion complete. %d records inserted.", count)
    except Exception as e:
        logger.error("Earthquake ingestion failed: %s", e)
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest USGS earthquake events")
    parser.add_argument("--days", type=int, default=30, help="Days of history to fetch")
    parser.add_argument("--minmag", type=float, default=2.5, help="Minimum magnitude")
    args = parser.parse_args()

    run_ingestion(days_back=args.days, min_magnitude=args.minmag)
