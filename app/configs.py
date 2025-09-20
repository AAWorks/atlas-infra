"""
API Configs
"""

import os


class DBSchema:
    """
    Database Schema
    """
    def __init__(self):
        self.ATTACHMENT = "attachment"
        self.BUDGET_ENTRY = "budget_entry"
        self.EVENT_ACTIVITY = "event_activity"
        self.ITEM_TAG = "item_tag"
        self.ITINERARY_ITEM = "itinerary_item"
        self.LODGING = "lodging"
        self.PLACE = "place"
        self.REQUIRED_DOCUMENT = "required_document"
        self.TAG = "tag"
        self.TICKET_LINK = "ticket_link"
        self.TRANSPORT_RENTAL = "transport_rental"
        self.TRAVEL_SEGMENT = "travel_segment"
        self.TRAVELER = "traveler"
        self.TRIP = "trip"
        self.TRIP_TRAVELER = "trip_traveler"


class Config:
    """
    Uniform Configs
    """
    TITLE = "Atlas Backend API"
    SEM_VER = "v1"
    DESCRIPTION = "Developer API for Atlas, an easy-to-use travel planner."

    def __init__(self):
        self.SUPABASE_URL = os.getenv("SUPABASE_URL")
        self.SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        self.SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
        self.DB_SCHEMA = DBSchema()
        self.LOGGER = 'uvicorn.error'

        self.ALLOWED_ORIGINS = os.getenv(
            "ALLOWED_ORIGINS",
            "http://localhost,http://localhost:8080"
        ).split(",")


class DevConfig(Config):
    """
    Development Configs
    """
    DEBUG = True
    def __init__(self):
        from dotenv import load_dotenv
        load_dotenv()

        super().__init__()


class ProdConfig(Config):
    """
    Production Configs
    """
    DEBUG = False

if os.getenv("ENV") == "PROD":
    config = ProdConfig()
else:
    config = DevConfig()
