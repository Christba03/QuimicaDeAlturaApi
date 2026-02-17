from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


def setup_cors(app: FastAPI, origins: list[str]) -> None:
    """Attach CORS middleware to the FastAPI application.

    Args:
        app: The FastAPI application instance.
        origins: List of allowed origin URLs.
    """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
        max_age=600,
    )
