"""
Development server runner.
Usage: python run.py
"""

import uvicorn
from app.core.config import get_settings


def main():
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.BACKEND_PORT,
        reload=settings.ENV == "development",
        log_level="info",
    )


if __name__ == "__main__":
    main()
