"""Run the service with uvicorn: ``python -m app.server``."""
import uvicorn

from .core.config import settings

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.port, reload=False)
