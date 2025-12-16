from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from app.api.routes import router as api_router

app = FastAPI(
    title="Superclaims Backend Assignment",
    description="LLM-powered medical claim document processing API.",
    version="1.0.0",
)


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def root():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8" />
        <title>Superclaims Backend Assignment</title>
        <style>
            body {
                font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
                background: linear-gradient(135deg, #0f172a, #1e293b);
                color: #e5e7eb;
                display: flex;
                align-items: center;
                justify-content: center;
                min-height: 100vh;
                margin: 0;
            }
            .card {
                background: #020617;
                border-radius: 16px;
                padding: 32px 40px;
                box-shadow: 0 20px 40px rgba(15, 23, 42, 0.6);
                max-width: 640px;
                text-align: center;
                border: 1px solid rgba(148, 163, 184, 0.3);
            }
            h1 {
                font-size: 28px;
                margin-bottom: 8px;
                color: #f9fafb;
            }
            p {
                margin: 6px 0;
                color: #cbd5f5;
                font-size: 14px;
            }
            .badge {
                display: inline-block;
                padding: 4px 10px;
                border-radius: 999px;
                background: rgba(56, 189, 248, 0.15);
                color: #7dd3fc;
                font-size: 11px;
                text-transform: uppercase;
                letter-spacing: 0.08em;
                margin-bottom: 12px;
            }
            .button {
                margin-top: 20px;
                display: inline-flex;
                align-items: center;
                justify-content: center;
                padding: 10px 18px;
                border-radius: 999px;
                border: none;
                background: linear-gradient(135deg, #22c55e, #16a34a);
                color: #0b1120;
                font-weight: 600;
                font-size: 14px;
                cursor: pointer;
                text-decoration: none;
                box-shadow: 0 12px 30px rgba(34, 197, 94, 0.45);
                transition: transform 0.1s ease, box-shadow 0.1s ease, filter 0.1s ease;
            }
            .button:hover {
                transform: translateY(-1px);
                filter: brightness(1.05);
                box-shadow: 0 18px 40px rgba(34, 197, 94, 0.55);
            }
            .button:active {
                transform: translateY(0);
                box-shadow: 0 10px 25px rgba(34, 197, 94, 0.4);
            }
            .button span {
                margin-left: 6px;
                font-size: 13px;
            }
            .hint {
                margin-top: 12px;
                font-size: 12px;
                color: #9ca3af;
            }
            .code {
                font-family: "JetBrains Mono", ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
                background: rgba(15, 23, 42, 0.9);
                padding: 2px 6px;
                border-radius: 6px;
                border: 1px solid rgba(148, 163, 184, 0.5);
            }
        </style>
    </head>
    <body>
        <div class="card">
            <div class="badge">Backend Assignment</div>
            <h1>Superclaims Claim Processing API</h1>
            <p>FastAPI + LLM agents for medical claim document ingestion, classification, and validation.</p>
            <p>Use the interactive Swagger UI to upload PDFs and see the full JSON response.</p>
            <form action="/docs">
                <button type="submit" class="button">
                    Open API Docs
                    <span>→</span>
                </button>
            </form>
            <div class="hint">
                Or go directly to <span class="code">/docs</span> in your browser.
            </div>
        </div>
    </body>
    </html>
    """


app.include_router(api_router, prefix="")
