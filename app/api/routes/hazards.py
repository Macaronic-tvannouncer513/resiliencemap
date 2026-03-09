import json
import logging

from fastapi import APIRouter, Depends
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.hazard import FloodZone, SeismicHazard
from app.schemas.responses import GeoJSONFeature, GeoJSONFeatureCollection

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/hazards/geojson", response_model=GeoJSONFeatureCollection)
def get_hazards_geojson(
    layer: str = "flood",
    state_fips: str | None = None,
    db: Session = Depends(get_db),
) -> GeoJSONFeatureCollection:
    """
    Return hazard data as a GeoJSON FeatureCollection for map rendering.

    - **layer**: 'flood' (FEMA NFHL) or 'seismic' (USGS earthquakes)
    - **state_fips**: optional 2-digit state FIPS to filter flood zones
    """
    features: list[GeoJSONFeature] = []

    if layer == "flood":
        query = select(
            FloodZone.id,
            FloodZone.fld_zone,
            FloodZone.sfha_tf,
            FloodZone.zone_subty,
            text("ST_AsGeoJSON(geom) AS geom_json"),
        ).select_from(FloodZone)

        if state_fips:
            query = query.where(FloodZone.state_fips == state_fips)

        rows = db.execute(query).mappings().all()
        for row in rows:
            features.append(
                GeoJSONFeature(
                    geometry=json.loads(row["geom_json"]),
                    properties={
                        "id": row["id"],
                        "flood_zone": row["fld_zone"],
                        "in_sfha": row["sfha_tf"] == "T",
                        "zone_subtype": row["zone_subty"],
                        "layer": "flood",
                    },
                )
            )

    elif layer == "seismic":
        rows = (
            db.execute(
                select(
                    SeismicHazard.usgs_id,
                    SeismicHazard.magnitude,
                    SeismicHazard.place,
                    SeismicHazard.event_time,
                    text("ST_AsGeoJSON(geom) AS geom_json"),
                )
                .select_from(SeismicHazard)
                .order_by(SeismicHazard.event_time.desc())
                .limit(500)
            )
            .mappings()
            .all()
        )

        for row in rows:
            features.append(
                GeoJSONFeature(
                    geometry=json.loads(row["geom_json"]),
                    properties={
                        "id": row["usgs_id"],
                        "magnitude": row["magnitude"],
                        "place": row["place"],
                        "event_time": row["event_time"].isoformat(),
                        "layer": "seismic",
                    },
                )
            )

    return GeoJSONFeatureCollection(features=features)
