from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.responses import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health_check(db: Session = Depends(get_db)) -> HealthResponse:
    try:
        db.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception:
        db_status = "error"

    try:
        postgis_version = db.execute(text("SELECT PostGIS_Version()")).scalar()
        postgis_status = f"ok ({postgis_version})"
    except Exception:
        postgis_status = "unavailable"

    return HealthResponse(
        status="ok" if db_status == "ok" else "degraded",
        database=db_status,
        postgis=postgis_status,
    )
