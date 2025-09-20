"""
Service Dependencies
"""

from supabase import create_client

from app.configs import config


client = create_client(
    config.SUPABASE_URL,
    config.SUPABASE_SERVICE_KEY
)
