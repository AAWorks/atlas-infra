import os
import logging

from fastapi import FastAPI
from app.routers import trips, items


TITLE = "Atlas Backend API"
SEM_VER = "v1"
DESCRIPTION = "Developer API for Atlas, a simple OO-inspired travel planner."


def build_app():
    app = FastAPI()

    api = FastAPI(
        title=TITLE,
        version=SEM_VER,
        description=DESCRIPTION,
    )

    # Include routes
    api.include_router(trips.router)
    api.include_router(items.router)

    app.mount(f"/api/{SEM_VER}/", api)

    return app
