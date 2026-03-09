import logging

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.responses import AtRiskInfrastructureResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/infrastructure/at-risk", response_model=list[AtRiskInfrastructureResponse])
def get_at_risk_infrastructure(
    min_score: float = Query(0.6, ge=0.0, le=1.0, description="Minimum composite risk score"),
    facility_type: str | None = Query(None, description="Filter: hospital, school, power_plant"),
    state_fips: str | None = Query(None, description="2-digit state FIPS filter"),
    limit: int = Query(200, ge=1, le=1000),
    db: Session = Depends(get_db),
) -> list[AtRiskInfrastructureResponse]:
    """
    Return critical infrastructure facilities located within high-risk census tracts.

    Joins facilities against risk_scores via spatial intersection with census_tracts
    to find facilities in tracts with composite_score >= min_score.
    """
    rows = (
        db.execute(
            text("""
                SELECT
                    ci.hifld_id,
                    ci.facility_type,
                    ci.name,
                    ci.address,
                    ci.city,
                    ci.state_fips,
                    ci.capacity,
                    rs.composite_score,
                    rs.tract_geoid
                FROM critical_infrastructure ci
                JOIN census_tracts ct ON ST_Within(ci.geom, ct.geom)
                JOIN risk_scores rs ON rs.tract_geoid = ct.geoid
                WHERE rs.composite_score >= :min_score
                    AND (:facility_type IS NULL OR ci.facility_type = :facility_type)
                    AND (:state_fips IS NULL OR ci.state_fips = :state_fips)
                ORDER BY rs.composite_score DESC, ci.capacity DESC NULLS LAST
                LIMIT :limit
            """),
            {
                "min_score": min_score,
                "facility_type": facility_type,
                "state_fips": state_fips,
                "limit": limit,
            },
        )
        .mappings()
        .all()
    )

    return [AtRiskInfrastructureResponse(**row) for row in rows]
