from fastapi import APIRouter
from fastapi import APIRouter, HTTPException
from app.schemas.request_schemas import ExplainRequest
from app.schemas.response_schemas import ExplanationResponse
from app.crud import inferance_crud

router = APIRouter()


@router.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "fraud-llm-explainer"
    }

@router.post("/explain", response_model=ExplanationResponse, summary="Generate fraud explanation")
async def explain(request: ExplainRequest):

    try:
        response = await inferance_crud.generate(request)
        return response

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )        