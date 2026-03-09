from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.hazard import StormAlert
from app.schemas.responses import StormAlertResponse

router = APIRouter()


@router.get("/alerts/active", response_model=list[StormAlertResponse])
def get_active_alerts(
    severity: str | None = None,
    db: Session = Depends(get_db),
) -> list[StormAlertResponse]:
    """
    Return currently active NOAA NWS storm alerts.

    - **severity**: filter by 'Extreme', 'Severe', 'Moderate', or 'Minor'
    """
    now = datetime.now(timezone.utc)
    query = (
        select(StormAlert)
        .where(StormAlert.expires > now)
        .order_by(StormAlert.severity, StormAlert.effective.desc())
    )
    if severity:
        query = query.where(StormAlert.severity == severity)

    rows = db.execute(query).scalars().all()
    return [StormAlertResponse.model_validate(r) for r in rows]
