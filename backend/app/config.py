import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'fallback-secret-key')
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/career_navigator_db')
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 16777216))
    ALLOWED_EXTENSIONS = {'pdf', 'docx'}
    MODEL_DIR = os.path.join(os.path.dirname(__file__), '..', 'ml', 'saved_models')
    TFIDF_MODEL_PATH = os.path.join(MODEL_DIR, 'tfidf_vectorizer.pkl')
    RF_MODEL_PATH    = os.path.join(MODEL_DIR, 'rf_career_model.pkl')
    KNN_MODEL_PATH   = os.path.join(MODEL_DIR, 'knn_readiness_model.pkl')
    ENCODER_PATH     = os.path.join(MODEL_DIR, 'label_encoder.pkl')
    SKILL_DB_PATH    = os.path.join(MODEL_DIR, 'skill_database.pkl')
    # YouTube Data API
    YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY', '')
    YOUTUBE_RESULTS_PER_SKILL = int(os.getenv('YOUTUBE_RESULTS_PER_SKILL', 3))
    YOUTUBE_CACHE_DAYS = 7  # Cache videos for 7 days before refresh``
    # JWT Authentication
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'dev_only_change_in_production')
    JWT_ACCESS_TOKEN_HOURS = int(os.getenv('JWT_ACCESS_TOKEN_HOURS', 24))
    # OpenAI
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
    OPENAI_MODEL   = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')
    