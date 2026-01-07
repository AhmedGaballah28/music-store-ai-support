import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import os

logger = logging.getLogger(__name__)

class MemoryManager:
    """Manages long-term memory storage for user preferences and history"""
    
    def __init__(self, storage_path: str = "./memory_store"):
        self.storage_path = storage_path
        self.memory_cache = {}
        
        os.makedirs(storage_path, exist_ok=True)
    
    def get_customer_memory_file(self, customer_id: str) -> str:
        """Get the file path for a customer's memory"""
        return os.path.join(self.storage_path, f"customer_{customer_id}.json")
    
    def load_customer_memory(self, customer_id: str) -> Dict:
        """Load customer preferences and history from storage"""
        try:
            if customer_id in self.memory_cache:
                logger.info(f"Loading memory from cache for customer {customer_id}")
                return self.memory_cache[customer_id]
            
            file_path = self.get_customer_memory_file(customer_id)
            
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    memory = json.load(f)
                logger.info(f"Loaded memory from file for customer {customer_id}")
            else:
                memory = self._initialize_memory()
                logger.info(f"Initialized new memory for customer {customer_id}")
            
            self.memory_cache[customer_id] = memory
            return memory
            
        except Exception as e:
            logger.error(f"Error loading memory for customer {customer_id}: {e}")
            return self._initialize_memory()
    
    def save_customer_memory(self, customer_id: str, memory: Dict) -> bool:
        """Save customer memory to storage"""
        try:
            file_path = self.get_customer_memory_file(customer_id)
            memory['last_updated'] = datetime.now().isoformat()
            with open(file_path, 'w') as f:
                json.dump(memory, f, indent=2)
            
            self.memory_cache[customer_id] = memory
            
            logger.info(f"Saved memory for customer {customer_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving memory for customer {customer_id}: {e}")
            return False
    
    def _initialize_memory(self) -> Dict:
        """Initialize a new memory structure"""
        return {
            'preferences': {
                'favorite_artists': [],
                'favorite_genres': [],
                'favorite_albums': [],
                'disliked_genres': []
            },
            'history': {
                'recent_searches': [],
                'recent_purchases': [],
                'recent_recommendations': []
            },
            'context': {
                'last_session': None,
                'total_sessions': 0,
                'first_interaction': datetime.now().isoformat()
            },
            'last_updated': datetime.now().isoformat()
        }
    
    def update_preferences(self, customer_id: str, preferences_update: Dict) -> Dict:
        """Update customer preferences"""
        memory = self.load_customer_memory(customer_id)
        
        
        if 'artist' in preferences_update:
            artist = preferences_update['artist']
            if artist not in memory['preferences']['favorite_artists']:
                memory['preferences']['favorite_artists'].append(artist)
                
                memory['preferences']['favorite_artists'] = memory['preferences']['favorite_artists'][-10:]
        
        
        if 'genre' in preferences_update:
            genre = preferences_update['genre']
            if genre not in memory['preferences']['favorite_genres']:
                memory['preferences']['favorite_genres'].append(genre)
            
                memory['preferences']['favorite_genres'] = memory['preferences']['favorite_genres'][-5:]
        
    
        if 'album' in preferences_update:
            album = preferences_update['album']
            if album not in memory['preferences']['favorite_albums']:
                memory['preferences']['favorite_albums'].append(album)
                memory['preferences']['favorite_albums'] = memory['preferences']['favorite_albums'][-10:]
        
        
        self.save_customer_memory(customer_id, memory)
        return memory
    
    def add_search_history(self, customer_id: str, search_query: str, results: List[Dict]) -> None:
        """Add a search to history"""
        memory = self.load_customer_memory(customer_id)
        
        search_entry = {
            'query': search_query,
            'timestamp': datetime.now().isoformat(),
            'results_count': len(results)
        }
        
        memory['history']['recent_searches'].append(search_entry)
    
        memory['history']['recent_searches'] = memory['history']['recent_searches'][-20:]
        
        self.save_customer_memory(customer_id, memory)
    
    def get_personalized_recommendations(self, customer_id: str) -> Dict:
        """Get personalized recommendations based on memory"""
        memory = self.load_customer_memory(customer_id)
        
        recommendations = {
            'based_on_artists': [],
            'based_on_genres': [],
            'based_on_history': []
        }
        
        
        if memory['preferences']['favorite_artists']:
            recommendations['based_on_artists'] = memory['preferences']['favorite_artists'][-3:]
        
    
        if memory['preferences']['favorite_genres']:
            recommendations['based_on_genres'] = memory['preferences']['favorite_genres'][-2:]
        
        if memory['history']['recent_searches']:
            recent = memory['history']['recent_searches'][-5:]
            recommendations['based_on_history'] = [s['query'] for s in recent]
        
        return recommendations
    
    def update_session_info(self, customer_id: str) -> None:
        """Update session information"""
        memory = self.load_customer_memory(customer_id)
        
        memory['context']['last_session'] = datetime.now().isoformat()
        memory['context']['total_sessions'] = memory['context'].get('total_sessions', 0) + 1
        
        self.save_customer_memory(customer_id, memory)
    
    def clear_customer_memory(self, customer_id: str) -> bool:
        """Clear all memory for a customer"""
        try:

            if customer_id in self.memory_cache:
                del self.memory_cache[customer_id]
            
            file_path = self.get_customer_memory_file(customer_id)
            if os.path.exists(file_path):
                os.remove(file_path)
            
            logger.info(f"Cleared memory for customer {customer_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error clearing memory for customer {customer_id}: {e}")
            return False
    
    def extract_preferences_from_query(self, query: str, results: Dict) -> Dict:
        """Extract preferences from a query and its results"""
        preferences = {}
        
        if results.get('entities', {}).get('artist_name'):
            preferences['artist'] = results['entities']['artist_name']
        
        if results.get('entities', {}).get('genre_name'):
            preferences['genre'] = results['entities']['genre_name']
        
        if results.get('results', {}).get('albums'):
            albums = results['results']['albums']
            if albums and len(albums) > 0:
                preferences['album'] = albums[0].get('album_title')
        
        return preferences

memory_manager = MemoryManager()