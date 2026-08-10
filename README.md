# Auroraa Fraud Explanation Engine

## Overview
The **Fraud Explanation Engine** is a FastAPI-based microservice designed to act as an AI Fraud Analyst for Indian financial institutions. It takes the verdict, forgery score, and SHAP feature contributions from a fraud detection model (such as LightGBM) and generates plain-language, easy-to-understand explanations for human loan underwriters. 

The engine uses advanced LLMs (via Grok, Groq, or local Ollama clients) to translate complex SHAP scores into actionable findings without inventing information or contradicting the underlying model's verdict.

## Features
- **Explainable AI for Fraud Analysis**: Converts SHAP contributions into human-readable text.
- **Dynamic Severity**: Automatically categorizes findings into HIGH, MEDIUM, or LOW severity based on SHAP contribution values.
- **Multiple LLM Backend Support**: Supports generating explanations using different LLM providers (Grok, Ollama).
- **FastAPI Framework**: High performance, easy to use, and automatic interactive API documentation.

## Project Structure
```
explanation_engine/
├── app/
│   ├── config/          # Application configuration settings
│   ├── crud/            # CRUD operations and data access logic
│   ├── dependencies/    # FastAPI dependencies, LLM clients (Grok, Ollama)
│   ├── model/           # Data models 
│   ├── prompt/          # System prompts for the AI Analyst
│   ├── routes/          # API endpoint routes (e.g., inferance_routes)
│   ├── schemas/         # Pydantic schemas for request/response validation
│   └── main.py          # FastAPI application entry point
├── .env                 # Environment variables configuration
└── requirements.txt     # Python dependencies
```

## Prerequisites
- Python 3.8+
- [Ollama](https://ollama.com/) (Optional, if using local models)
- API Keys for external LLM providers (e.g., Grok, Groq)

## Installation

1. **Create and activate a virtual environment**
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Environment Setup**
   Configure your environment variables by checking the `.env` file in the root directory. Ensure all necessary LLM API keys are set.

## Running the Application

To start the FastAPI development server, run:

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.

## API Documentation

FastAPI automatically generates interactive API documentation. Once the server is running, you can access:
- **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
