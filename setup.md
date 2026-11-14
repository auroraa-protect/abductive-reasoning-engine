# Setup and run

A business-evidence reasoning service with a FastAPI backend and a Streamlit interface. The UI sends case information to the backend, which calls Groq to create a verification report. Run the backend and UI in separate terminals.

## Requirements

- Python 3.10 or newer
- A Groq API key for inference
- Git, if you are cloning the repository

## 1. Get the project and create an environment

From a terminal, clone the repository and move into its folder:

```powershell
git clone <repository-url>
cd abductive-reasoning-engine
```

Create and activate a virtual environment, then install the project dependencies:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

On macOS or Linux, activate the environment with `source .venv/bin/activate` instead.

## 2. Configure the language model

Create or edit a `.env` file in the project root and add your Groq key:

```dotenv
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=openai/gpt-oss-20b
```

The backend also accepts the legacy key name `GROK_CLOUD_API`. If `GROQ_MODEL` is omitted, it uses `llama-3.3-70b-versatile`. Keep your real key private and do not commit it.

## 3. Start the backend

In the first terminal, from the project root with the virtual environment active, run:

```powershell
python -m uvicorn app.main:app --reload --port 8000
```

The API is available at `http://localhost:8000`. Check that it is responding at `http://localhost:8000/health`; interactive API documentation is at `http://localhost:8000/docs`.

## 4. Start the Streamlit UI

Open a second terminal, activate the same virtual environment, and run from the project root:

```powershell
python -m streamlit run ui/app.py
```

Streamlit prints the local address for the UI, usually `http://localhost:8501`. Keep both terminals running while using it.

By default, the UI connects to the backend at `http://localhost:8000`. To use another backend address, set `AURORAA_BACKEND_URL` (or `BACKEND_URL`) in the environment where Streamlit is started, or change the **FastAPI URL** in the UI sidebar.

## Understanding the UI

- **Sidebar:** Start a new test, choose from sample business cases, check the backend connection, and refresh recent inference history.
- **JSON input:** Paste a structured case payload. Use **Load ABC Textile sample** to get started, and **Validate JSON** to check that the input is a JSON object before submitting.
- **Text input:** Enter business details and declared claims, then add supporting evidence under purchase, inventory, production, sales, physical, financial, and additional-evidence sections. Leave unknown fields blank.
- **File upload:** Upload JSON, text, PDF, or DOCX evidence. Readable text is extracted for the request; JSON files must contain an object. Image and video files are not analyzed or sent as media—enter verified observations in the notes or provide them in JSON instead.
- **Results:** Run inference to view the generated report and download it as Markdown or the full response as JSON. The raw response, including token usage when available, can also be inspected.

The report helps compare declared claims with the evidence provided; it does not independently verify the truth of uploaded records or media.

## Optional: run the tests

If pytest is not installed in the environment, install it first:

```powershell
python -m pip install pytest
```

Then run the test suite from the project root:

```powershell
python -m pytest tests/
```
