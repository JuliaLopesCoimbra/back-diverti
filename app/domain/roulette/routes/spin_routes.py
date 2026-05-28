from fastapi import APIRouter, Depends, HTTPException
from app.config.roulette_db import get_roulette_db
from app.domain.auth.controllers.auth_controller import get_current_user
from app.domain.roulette.controllers.spin_controller import SpinController
from app.infra.redis import check_rate_limit

router = APIRouter(prefix="/roulette/events", tags=["Spin"])

@router.get("/{event_id}/spins/count")
def get_user_spin_count(
    event_id: int,
    db=Depends(get_roulette_db),
    user=Depends(get_current_user)
):
    return SpinController.count_user_spins(db, user, event_id)

@router.post("/{event_id}/spin")
def spin_roulette(
    event_id: int,
    db=Depends(get_roulette_db),
    user=Depends(get_current_user)
):
    # Rate limiting: 10 spins por hora por usuário por evento (CRÍTICO - retorna 503 se Redis cair)
    allowed, remaining = check_rate_limit(f"spin:user:{user.id}:event:{event_id}", max_requests=10, window_seconds=3600, critical=True)

    if not allowed:
        raise HTTPException(
            status_code=429,
            detail="Você já girou a roleta muitas vezes. Tente novamente em 1 hora.",
            headers={"Retry-After": "3600", "X-RateLimit-Remaining": str(remaining)}
        )

    return SpinController.spin(db, user, event_id)
