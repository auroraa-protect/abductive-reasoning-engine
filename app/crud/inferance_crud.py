"""
Inference CRUD Module
---------------------

This module handles the core logic for generating fraud explanations using a Large Language Model (LLM).
It acts as the bridge between the API request and the LLM inference step.

Workflow:
1. Reads the strict instructions from `system_prompt.txt`.
2. Resolves incoming SHAP features against a predefined feature registry to fetch standardized titles, severities, and recommendations.
3. Filters the incoming payload (`shap_feature` and `context`) to only include data for features with a positive SHAP contribution. This significantly reduces the payload size and token cost.
4. Serializes the filtered data, individual document values, and registry blocks into a structured user message.
5. Sends the combined prompt to the Groq LLM to generate a JSON-formatted `ExplanationResponse` containing underwriter-ready case notes.
"""

import os
import json
from fastapi import HTTPException

from app.schemas.request_schemas import ExplainRequest
from app.schemas.response_schemas import ExplanationResponse
from app.dependencies.ollama_client import get_ollama_completion
from app.dependencies.grok_client import get_groq_completion
from app.service.registry_service import resolve, build_registry_context_block

async def generate(request: ExplainRequest) -> ExplanationResponse:
    prompt_path = os.path.join(os.path.dirname(__file__), "..", "prompt", "system_prompt.txt")
    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            system_prompt = f.read()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read system prompt: {str(e)}")

    # Resolve SHAP features against the salary-slip registry
    registry_ctx = resolve(request.shap_feature)
    registry_block = build_registry_context_block(registry_ctx)

    positive_features = {sf.feature for sf in request.shap_feature if sf.contribution > 0}

    shap_list = [{"feature": sf.feature, "contribution": sf.contribution} for sf in request.shap_feature if sf.contribution > 0]
    context_list = [{"feature": c.feature, "reason": c.reason} for c in request.context if c.feature in positive_features]
    individual_list = [{"field": idata.field, "value": idata.value} for idata in request.individual_data]

    user_message = (
        f"Document Type: {request.document_type}\n"
        f"SHAP Features:\n{json.dumps(shap_list, indent=2)}\n\n"
        f"Context:\n{json.dumps(context_list, indent=2)}\n\n"
        f"Individual Data:\n{json.dumps(individual_list, indent=2)}"
        f"{registry_block}"
    )

    content = await get_groq_completion(system_prompt, user_message)

    try:
        parsed_json = json.loads(content)
        return ExplanationResponse(**parsed_json)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse LLM response: {str(e)}\nResponse was: {content}")
