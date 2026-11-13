from fastapi import FastAPI

from app.routes.inferance_routes import router

app = FastAPI(
    title="Abductive Reasoning Engine",
    version="1.0.0"
)

app.include_router(router)

# streamlit run ui/app.py