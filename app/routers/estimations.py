import structlog
from fastapi import APIRouter, HTTPException

from app.schemas.estimation import EstimationRequest, EstimationResponse
from app.services.llm_service import LLMServiceError, generate_estimation

router = APIRouter(prefix="/api/v1", tags=["estimations"])
log = structlog.get_logger()


@router.post("/estimate", response_model=EstimationResponse)
def estimate(request: EstimationRequest) -> EstimationResponse:
    try:
        result = generate_estimation(request.transcription)
    except LLMServiceError as exc:
        log.error("estimation_failed", error=str(exc))
        raise HTTPException(
            status_code=500, detail="No se pudo generar la estimación."
        ) from exc
    return EstimationResponse(**result)
