from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
from app.schemas.request_schemas import ExplainRequest
from app.schemas.response_schemas import ExplainResponse
from app.crud import inferance_crud

router = APIRouter()


@router.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "abductive-reasoning-engine",
        "version": "2.0.0",
    }


@router.post(
    "/explain",
    response_model=ExplainResponse,
    summary="Generate abductive reasoning explanation report",
    description="Accepts flexible natural language business information or structured multi-category evidence, and produces a readable 5-section abductive verification report.",
)
async def explain(request: ExplainRequest):
    try:
        response = await inferance_crud.generate(request)
        return response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics", summary="Get token usage and latency metrics")
async def get_metrics() -> Dict[str, Any]:
    """Retrieve cumulative token tracking metrics and inference history."""
    history = inferance_crud.get_token_history()
    total_input = sum(h.get("input_tokens", 0) for h in history)
    total_output = sum(h.get("output_tokens", 0) for h in history)
    total_tokens = sum(h.get("total_tokens", 0) for h in history)
    avg_latency = (
        round(sum(h.get("latency_ms", 0) for h in history) / len(history), 1)
        if history
        else 0
    )

    # Approximate cost estimate (e.g., ~$0.59 / 1M prompt, ~$0.79 / 1M completion on Groq)
    estimated_cost_usd = round((total_input * 0.00000059) + (total_output * 0.00000079), 6)

    return {
        "total_calls": len(history),
        "total_input_tokens": total_input,
        "total_output_tokens": total_output,
        "total_tokens": total_tokens,
        "average_latency_ms": avg_latency,
        "estimated_cost_usd": estimated_cost_usd,
        "call_history": history,
    }


@router.post("/metrics/reset", summary="Reset token tracking metrics")
async def reset_metrics():
    """Clear inference history and metrics log."""
    inferance_crud.clear_token_history()
    return {"status": "metrics_reset_successful"}
