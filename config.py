import os
from dotenv import load_dotenv


load_dotenv()

class Config:
    """Configuration class for the application"""
    
    
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")


    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///chinook.db")
    
    MODEL_NAME = "gemini-2.0-flash-exp"
    TEMPERATURE = 0.7
    
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    PAGE_TITLE = "Digital Music Store Support"
    PAGE_ICON = "🎵"
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        if not cls.GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY is not set in .env file")
        return True