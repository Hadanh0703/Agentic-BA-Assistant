from fastapi.middleware.cors import CORSMiddleware

def setup_middlewares(app):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "https://agentic-ba-assistant-k3ih.vercel.app", 
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
    )