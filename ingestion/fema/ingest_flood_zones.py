"""
FEMA National Flood Hazard Layer (NFHL) Ingestion
==================================================

Fetches Special Flood Hazard Area (SFHA) polygons for a given state
from FEMA's public ArcGIS REST service and upserts them into PostGIS.

Data source: https://hazards.fema.gov/arcgis/rest/services/public/NFHL/MapServer/28
Layer 28 = Flood Hazard Zones (S_FLD_HAZ_AR)

Usage:
    # Ingest flood zones for Texas (state FIPS 48)
    python -m ingestion.fema.ingest_flood_zones --state 48

    # Ingest for multiple states
    python -m ingestion.fema.ingest_flood_zones --state 48 12 06
"""

import argparse
import logging
import time
from datetime import datetime

import geopandas as gpd
import requests
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models.hazard import FloodZone

logger = logging.getLogger(__name__)

settings = get_settings()

# FEMA ArcGIS REST endpoint for flood hazard zones
FEMA_NFHL_URL = settings.fema_nfhl_wfs

# FEMA's flood zone classification
# High-risk zones (Special Flood Hazard Areas — SFHA)
HIGH_RISK_ZONES = {"A", "AE", "AH", "AO", "AR", "A99", "V", "VE"}
# Moderate risk
MODERATE_RISK_ZONES = {"B", "X"}
# Undetermined
UNDETERMINED_ZONES = {"D"}


def fetch_flood_zones_for_state(
    state_fips: str,
    batch_size: int = 1000,
) -> gpd.GeoDataFrame:
    """
    Fetch all flood hazard zone polygons for a US state from FEMA's REST API.

    FEMA paginates at 1000 features per request. We loop until all features
    for the state are retrieved.

    Args:
        state_fips: 2-digit state FIPS code (e.g. '48' for Texas)
        batch_size: records per API request (FEMA max is 1000)

    Returns:
        GeoDataFrame with flood zone polygons in EPSG:4326
    """
    logger.info("Fetching FEMA flood zones for state FIPS %s", state_fips)

    all_features = []
    offset = 0

    while True:
        params = {
            # broad filter; FEMA doesn't support state_fips directly
            "where": "STATE_ABBR IS NOT NULL",
            "outFields": "FLD_ZONE,ZONE_SUBTY,SFHA_TF,STATE_ABBR",
            "geometryType": "esriGeometryPolygon",
            "spatialRel": "esriSpatialRelIntersects",
            "outSR": "4326",  # WGS84 — store everything in 4326
            "f": "geojson",
            "resultOffset": offset,
            "resultRecordCount": batch_size,
            "returnGeometry": "true",
        }

        # FEMA doesn't have a direct state_fips field in layer 28,
        # so we use a bounding box derived from Census state geometry.
        # For a production system, you'd download the full NFHL shapefile
        # per state from https://msc.fema.gov/portal/advanceSearch
        # Here we demonstrate the API approach for live data.
        bbox = _get_state_bbox(state_fips)
        if bbox:
            params["geometry"] = f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}"
            params["inSR"] = "4326"

        try:
            resp = requests.get(FEMA_NFHL_URL, params=params, timeout=60)
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException as e:
            logger.error("FEMA API request failed at offset %d: %s", offset, e)
            raise

        features = data.get("features", [])
        if not features:
            logger.info("No more features at offset %d — fetch complete", offset)
            break

        all_features.extend(features)
        logger.info("Retrieved %d features (total so far: %d)", len(features), len(all_features))

        if len(features) < batch_size:
            # Last page
            break

        offset += batch_size
        time.sleep(0.5)  # Be a good API citizen

    if not all_features:
        logger.warning("No flood zone features found for state FIPS %s", state_fips)
        return gpd.GeoDataFrame()

    gdf = gpd.GeoDataFrame.from_features(all_features, crs="EPSG:4326")

    # Normalize column names to lowercase
    gdf.columns = [c.lower() for c in gdf.columns]

    logger.info("Fetched %d flood zone polygons for state FIPS %s", len(gdf), state_fips)
    return gdf


def _get_state_bbox(state_fips: str) -> tuple[float, float, float, float] | None:
    """
    Return approximate bounding box (minx, miny, maxx, maxy) for a US state.
    Used to spatially filter FEMA API results.

    In production, fetch this from the Census Cartographic Boundary Files.
    These are hard-coded approximations for common states.
    """
    # fmt: off
    BBOXES: dict[str, tuple[float, float, float, float]] = {
        "01": (-88.47, 30.14, -84.89, 35.01),   # Alabama
        "04": (-114.82, 31.33, -109.05, 37.00),  # Arizona
        "05": (-94.62, 33.00, -89.64, 36.50),    # Arkansas
        "06": (-124.41, 32.53, -114.13, 42.01),  # California
        "08": (-109.06, 36.99, -102.04, 41.00),  # Colorado
        "09": (-73.73, 40.98, -71.79, 42.05),    # Connecticut
        "10": (-75.79, 38.45, -75.05, 39.84),    # Delaware
        "12": (-87.63, 24.52, -79.97, 31.00),    # Florida
        "13": (-85.61, 30.36, -80.84, 35.00),    # Georgia
        "15": (-178.33, 18.91, -154.81, 28.40),  # Hawaii
        "16": (-117.24, 41.99, -111.04, 49.00),  # Idaho
        "17": (-91.51, 36.97, -87.02, 42.51),    # Illinois
        "18": (-88.10, 37.77, -84.78, 41.76),    # Indiana
        "19": (-96.64, 40.38, -90.14, 43.50),    # Iowa
        "20": (-102.05, 36.99, -94.59, 40.00),   # Kansas
        "21": (-89.57, 36.50, -81.96, 39.15),    # Kentucky
        "22": (-94.04, 28.93, -88.82, 33.02),    # Louisiana
        "23": (-71.08, 43.06, -66.95, 47.46),    # Maine
        "24": (-79.49, 37.91, -75.05, 39.72),    # Maryland
        "25": (-73.51, 41.24, -69.93, 42.89),    # Massachusetts
        "26": (-90.42, 41.70, -82.41, 48.19),    # Michigan
        "27": (-97.24, 43.50, -89.49, 49.38),    # Minnesota
        "28": (-91.66, 30.17, -88.10, 34.99),    # Mississippi
        "29": (-95.77, 35.99, -89.10, 40.61),    # Missouri
        "30": (-116.05, 44.36, -104.04, 49.00),  # Montana
        "31": (-104.05, 40.00, -95.31, 43.00),   # Nebraska
        "32": (-120.00, 35.00, -114.04, 42.00),  # Nevada
        "33": (-72.56, 42.70, -70.61, 45.31),    # New Hampshire
        "34": (-75.56, 38.93, -73.89, 41.36),    # New Jersey
        "35": (-109.05, 31.33, -103.00, 37.00),  # New Mexico
        "36": (-79.76, 40.50, -71.86, 45.01),    # New York
        "37": (-84.32, 33.84, -75.46, 36.59),    # North Carolina
        "38": (-104.05, 45.93, -96.55, 49.00),   # North Dakota
        "39": (-84.82, 38.40, -80.52, 42.33),    # Ohio
        "40": (-103.00, 33.62, -94.43, 37.00),   # Oklahoma
        "41": (-124.57, 41.99, -116.46, 46.24),  # Oregon
        "42": (-80.52, 39.72, -74.69, 42.27),    # Pennsylvania
        "44": (-71.86, 41.15, -71.12, 42.02),    # Rhode Island
        "45": (-83.36, 32.05, -78.54, 35.22),    # South Carolina
        "46": (-104.06, 42.48, -96.44, 45.94),   # South Dakota
        "47": (-90.31, 34.98, -81.65, 36.68),    # Tennessee
        "48": (-106.65, 25.84, -93.51, 36.50),   # Texas
        "49": (-114.05, 37.00, -109.04, 42.00),  # Utah
        "50": (-73.44, 42.73, -71.47, 45.02),    # Vermont
        "51": (-83.68, 36.54, -75.24, 39.47),    # Virginia
        "53": (-124.73, 45.54, -116.92, 49.00),  # Washington
        "54": (-82.64, 37.20, -77.72, 40.64),    # West Virginia
        "55": (-92.89, 42.49, -86.25, 47.31),    # Wisconsin
        "56": (-111.05, 40.99, -104.05, 45.01),  # Wyoming
    }
    # fmt: on
    return BBOXES.get(state_fips)


def upsert_flood_zones(gdf: gpd.GeoDataFrame, state_fips: str, db: Session) -> int:
    """
    Upsert flood zone records into the database.

    Uses a delete-then-insert strategy per state to keep data fresh.
    In production, consider using ON CONFLICT for finer control.

    Args:
        gdf: GeoDataFrame from fetch_flood_zones_for_state()
        state_fips: 2-digit state FIPS
        db: SQLAlchemy session

    Returns:
        Number of records inserted
    """
    if gdf.empty:
        logger.warning("Empty GeoDataFrame — nothing to upsert for state %s", state_fips)
        return 0

    # Delete existing records for this state
    deleted = db.execute(
        text("DELETE FROM flood_zones WHERE state_fips = :fips"),
        {"fips": state_fips},
    ).rowcount
    logger.info("Deleted %d existing flood zone records for state %s", deleted, state_fips)

    inserted = 0
    for _, row in gdf.iterrows():
        geom = row.get("geometry")
        if geom is None or geom.is_empty:
            continue

        # Convert to WKT for PostGIS — GeoAlchemy2 accepts WKT with SRID prefix
        wkt = f"SRID=4326;{geom.wkt}"

        flood_zone = FloodZone(
            fld_zone=str(row.get("fld_zone", "UNKNOWN")),
            zone_subty=row.get("zone_subty"),
            sfha_tf=row.get("sfha_tf"),
            state_fips=state_fips,
            geom=wkt,
            ingested_at=datetime.utcnow(),
        )
        db.add(flood_zone)
        inserted += 1

        # Batch commit every 500 records to avoid memory buildup
        if inserted % 500 == 0:
            db.commit()
            logger.info("Committed %d flood zone records...", inserted)

    db.commit()
    logger.info(
        "Upsert complete: %d flood zone records inserted for state %s",
        inserted,
        state_fips,
    )
    return inserted


def run_ingestion(state_fips_list: list[str]) -> None:
    """
    Full ingestion pipeline: fetch from FEMA → upsert to PostGIS.

    Args:
        state_fips_list: list of 2-digit state FIPS codes to ingest
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    db = SessionLocal()
    try:
        total_inserted = 0
        for state_fips in state_fips_list:
            logger.info("=== Starting ingestion for state FIPS: %s ===", state_fips)
            try:
                gdf = fetch_flood_zones_for_state(state_fips)
                count = upsert_flood_zones(gdf, state_fips, db)
                total_inserted += count
                logger.info("State %s: %d records ingested", state_fips, count)
            except Exception as e:
                logger.error("Failed to ingest state %s: %s", state_fips, e)
                db.rollback()
                continue

        logger.info("=== Ingestion complete. Total records inserted: %d ===", total_inserted)
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Ingest FEMA NFHL flood zones for one or more US states"
    )
    parser.add_argument(
        "--state",
        nargs="+",
        required=True,
        help="One or more 2-digit state FIPS codes (e.g. --state 48 12 06)",
    )
    args = parser.parse_args()

    # Zero-pad any single-digit FIPS codes
    state_list = [s.zfill(2) for s in args.state]
    run_ingestion(state_list)
