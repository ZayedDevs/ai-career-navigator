import os
from functools import lru_cache
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()


@lru_cache(maxsize=1)
def get_mongo_client() -> MongoClient:
    """Get a cached MongoDB client connection."""
    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/career_navigator_db")
    client = MongoClient(mongo_uri, serverSelectionTimeoutMS=3000)
    return client


@lru_cache(maxsize=1)
def get_db():
    """Get the career_navigator_db database."""
    client = get_mongo_client()
    # Extract database name from URI, default to 'career_navigator_db'
    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/career_navigator_db")
    db_name = mongo_uri.rstrip("/").split("/")[-1] or "career_navigator_db"
    return client[db_name]


def get_collection(name: str):
    """Get a specific collection by name."""
    return get_db()[name]