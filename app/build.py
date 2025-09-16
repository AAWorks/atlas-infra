"""
App Builder
"""

import os
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.configs import config
from app.routers import trips
from app.routers import items
from app.middleware import GlobalMiddleware


def build_app():
    app = FastAPI()

    api = FastAPI(
        title=config.TITLE,
        version=config.SEM_VER,
        description=config.DESCRIPTION,
    )

    api.add_middleware(
        CORSMiddleware,
        allow_origins=config.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Global middleware
    api.add_middleware(GlobalMiddleware)

    # Include routes
    api.include_router(trips.router)
    api.include_router(items.router)

    app.mount(f"/api/{config.SEM_VER}/", api)

    return app
