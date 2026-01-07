import sqlite3
import requests
from langchain_community.utilities.sql_database import SQLDatabase
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
import logging

logger = logging.getLogger(__name__)

class ChinookDatabase:
    """Handles Chinook database operations"""
    
    def __init__(self):
        self.engine = None
        self.db = None
        self.connection = None
        
    def initialize(self):
        """Initialize the Chinook database"""
        try:
            logger.info("Initializing Chinook database...")
            self.engine = self._get_engine_for_chinook_db()
            self.db = SQLDatabase(self.engine)
            logger.info("Database initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            return False
    
    def _get_engine_for_chinook_db(self):
        """Pull sql file, populate in-memory database, and create engine."""

        url = "https://raw.githubusercontent.com/lerocha/chinook-database/master/ChinookDatabase/DataSources/Chinook_Sqlite.sql"
        
        logger.info("Downloading Chinook database script...")
    
        response = requests.get(url)
        response.raise_for_status()
        sql_script = response.text
        
        logger.info("Creating in-memory database...")
        
        self.connection = sqlite3.connect(":memory:", check_same_thread=False)
        
        self.connection.executescript(sql_script)
        
        engine = create_engine(
            "sqlite://",
            creator=lambda: self.connection,
            poolclass=StaticPool,
            connect_args={"check_same_thread": False},
        )
        
        logger.info("Database engine created successfully")
        return engine
    
    def get_database(self):
        """Get the SQLDatabase instance"""
        if not self.db:
            self.initialize()
        return self.db
    
    def test_connection(self):
        """Test database connection and return basic stats"""
        try:
            if not self.db:
                self.initialize()
            
            result = self.db.run("SELECT COUNT(*) as count FROM Customer")
            logger.info(f"Database test successful. Customer count: {result}")
            
       
            try:
                tables = self.db.get_usable_table_names()
            except AttributeError:
                tables = self.db.get_table_names()
            
            stats = {
                "status": "Connected",
                "tables": tables,
                "customer_count": result
            }
            
            return stats
        except Exception as e:
            logger.error(f"Database test failed: {e}")
            return {"status": "Error", "error": str(e)}
    
    def get_table_info(self):
        """Get information about database tables"""
        if not self.db:
            self.initialize()
        return self.db.get_table_info()

db_manager = ChinookDatabase()