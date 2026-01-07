import logging
from typing import Dict, List, Any, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage, SystemMessage
from config import Config
from tools import MusicCatalogTools, InvoiceTools, CustomerTools
import json
import re

logger = logging.getLogger(__name__)

class MusicCatalogAgent:
    """Agent for handling music catalog queries"""
    
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model=Config.MODEL_NAME,
            temperature=Config.TEMPERATURE,
            google_api_key=Config.GOOGLE_API_KEY
        )
        self.tools = MusicCatalogTools()
        
        self.system_prompt = """You are a helpful music catalog assistant for a digital music store.
        Your role is to help customers find music, discover new artists, and get recommendations.
        
        You have access to these tools:
        1. get_albums_by_artist(artist) - Find albums by an artist
        2. get_tracks_by_artist(artist) - Find tracks/songs by an artist
        3. get_songs_by_genre(genre) - Find songs in a specific genre
        4. check_for_songs(song_title) - Search for specific songs
        
        When responding:
        - Be friendly and enthusiastic about music
        - Provide detailed information about albums, tracks, and artists
        - Make recommendations based on user preferences
        - Format responses in a clear, readable way
        - If you can't find something, suggest alternatives
        """
    
    def process_query(self, query: str, user_preferences: Dict = None) -> Dict:
        """Process a music-related query"""
        try:
            analysis_prompt = f"""Analyze this music query and determine which tools to use:
            Query: {query}
            User Preferences: {user_preferences if user_preferences else 'None'}
            
            Respond with a JSON object containing:
            - "intent": the main intent (search_artist, search_genre, search_song, recommendation)
            - "entities": extracted entities (artist_name, genre_name, song_title)
            - "tools_needed": list of tools to call
            """
            
            messages = [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=analysis_prompt)
            ]
            
            analysis_response = self.llm.invoke(messages)
            
    
            entities = self._extract_entities(analysis_response.content, query)
            
        
            results = {}
            
            if entities.get('artist_name'):
                artist = entities['artist_name']
                results['albums'] = self.tools.get_albums_by_artist(artist)
                results['tracks'] = self.tools.get_tracks_by_artist(artist)
            
            if entities.get('genre_name'):
                genre = entities['genre_name']
                results['genre_songs'] = self.tools.get_songs_by_genre(genre)
            
            if entities.get('song_title'):
                song = entities['song_title']
                results['song_search'] = self.tools.check_for_songs(song)
            
            response = self._generate_response(query, results, user_preferences)
            
            return {
                'success': True,
                'response': response,
                'entities': entities,
                'results': results
            }
            
        except Exception as e:
            logger.error(f"Error processing music query: {e}")
            return {
                'success': False,
                'response': "I apologize, but I encountered an error while searching for music. Please try again.",
                'error': str(e)
            }
    
    def _extract_entities(self, analysis: str, query: str) -> Dict:
        """Extract entities from the analysis"""
        entities = {}
        
        artist_patterns = [
            r"artist['\"]?\s*:\s*['\"]([^'\"]+)['\"]",
            r"artist_name['\"]?\s*:\s*['\"]([^'\"]+)['\"]",
            r"by\s+([A-Z][^.?!,]+?)(?:\?|$|\.|\s+and\s+|\s+or\s+)"
        ]
        
        for pattern in artist_patterns:
            match = re.search(pattern, analysis, re.IGNORECASE)
            if match:
                entities['artist_name'] = match.group(1).strip()
                break
        
        
        if not entities.get('artist_name'):
       
            known_artists = ['rolling stones', 'the rolling stones', 'beatles', 'the beatles', 'led zeppelin', 'pink floyd']
            query_lower = query.lower()
            for artist in known_artists:
                if artist in query_lower:
                
                    entities['artist_name'] = ' '.join(word.capitalize() for word in artist.split())
                    break
        
        genre_patterns = [
            r"genre['\"]?\s*:\s*['\"]([^'\"]+)['\"]",
            r"genre_name['\"]?\s*:\s*['\"]([^'\"]+)['\"]"
        ]
        
        for pattern in genre_patterns:
            match = re.search(pattern, analysis, re.IGNORECASE)
            if match:
                entities['genre_name'] = match.group(1).strip()
                break

        song_patterns = [
            r"song['\"]?\s*:\s*['\"]([^'\"]+)['\"]",
            r"song_title['\"]?\s*:\s*['\"]([^'\"]+)['\"]"
        ]
        
        for pattern in song_patterns:
            match = re.search(pattern, analysis, re.IGNORECASE)
            if match:
                entities['song_title'] = match.group(1).strip()
                break
        
        return entities
    
    def _generate_response(self, query: str, results: Dict, preferences: Dict) -> str:
        """Generate a natural language response from the results"""
        
        response_parts = []
    
        if results.get('albums'):
            albums = results['albums']
            if albums:
                response_parts.append("Here are the albums I found:\n")
                for i, album in enumerate(albums[:5], 1):
                    response_parts.append(f"{i}. **{album['album_title']}** by {album.get('artist_name', 'Unknown Artist')}")
        
     
        if results.get('tracks'):
            tracks = results['tracks']
            if tracks and len(response_parts) == 0:  
                response_parts.append("Here are some tracks:\n")
                for i, track in enumerate(tracks[:5], 1):
                    response_parts.append(f"{i}. **{track['track_name']}** from _{track['album_title']}_")
        
  
        if results.get('genre_songs'):
            songs = results['genre_songs']
            if songs:
                response_parts.append("Here are some songs in that genre:\n")
                for i, song in enumerate(songs[:5], 1):
                    response_parts.append(f"{i}. **{song['track_name']}** by {song['artist_name']}")
    
        if results.get('song_search'):
            songs = results['song_search']
            if songs:
                response_parts.append("I found these songs:\n")
                for i, song in enumerate(songs[:3], 1):
                    response_parts.append(f"{i}. **{song['track_name']}** by {song['artist_name']} (${song['price']})")
        
        if response_parts:
            response = "\n".join(response_parts)
            response += "\n\nWould you like more information about any of these, or can I help you find something else?"
        else:
            response = "I couldn't find specific results for your query. Could you please provide more details about what you're looking for?"
        
        return response


class InvoiceAgent:
    """Agent for handling invoice and purchase queries"""
    
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model=Config.MODEL_NAME,
            temperature=Config.TEMPERATURE,
            google_api_key=Config.GOOGLE_API_KEY
        )
        self.tools = InvoiceTools()
        
        self.system_prompt = """You are a helpful customer service assistant for invoice and purchase queries.
        Your role is to help customers with their purchase history and invoice information.
        
        You have access to these tools:
        1. get_invoices_by_customer_sorted_by_date(customer_id) - Get customer's invoices sorted by date
        2. get_invoices_sorted_by_unit_price(customer_id) - Get invoices sorted by price
        3. get_employee_by_invoice_and_customer(invoice_id, customer_id) - Get support employee info
        
        When responding:
        - Be professional and accurate with financial information
        - Format dates and amounts clearly
        - Provide complete invoice details when requested
        - Respect customer privacy and verify identity before sharing sensitive info
        """
    
    def process_query(self, query: str, customer_id: str = None) -> Dict:
        """Process an invoice-related query"""
        try:
            if not customer_id:
                return {
                    'success': False,
                    'response': "I need to verify your identity first. Please provide your customer ID, email, or phone number.",
                    'requires_verification': True
                }
      
            invoices = self.tools.get_invoices_by_customer_sorted_by_date(customer_id)
            
            if not invoices:
                return {
                    'success': True,
                    'response': "I couldn't find any invoices associated with your account.",
                    'results': []
                }
    
            query_lower = query.lower()
            if any(word in query_lower for word in ['recent', 'last', 'latest', 'most recent']):
             
                recent_invoice = invoices[0] if invoices else None
                if recent_invoice:
                    date_str = recent_invoice['invoice_date']
                    
                    try:
                        from datetime import datetime
                        if 'T' in date_str:
                            date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                        else:
                            date_obj = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
                        formatted_date = date_obj.strftime('%B %d, %Y')
                    except:
                        formatted_date = date_str
                    
                    response = f"Your most recent purchase was on **{formatted_date}** "
                    response += f"for a total amount of **${recent_invoice['total']}**."
                    
                    return {
                        'success': True,
                        'response': response,
                        'results': [recent_invoice]
                    }
            
            response = f"Here are your invoices (most recent first):\n\n"
            for i, invoice in enumerate(invoices[:5], 1):
                response += f"{i}. **Date:** {invoice['invoice_date']} | **Total:** ${invoice['total']} | **Location:** {invoice['billing_city']}, {invoice['billing_country']}\n"
            
            if len(invoices) > 5:
                response += f"\n_Showing 5 of {len(invoices)} total invoices_"
            
            return {
                'success': True,
                'response': response,
                'results': invoices
            }
            
        except Exception as e:
            logger.error(f"Error processing invoice query: {e}")
            return {
                'success': False,
                'response': "I encountered an error while retrieving your invoice information. Please try again.",
                'error': str(e)
            }


class CustomerVerificationAgent:
    """Agent for verifying customer identity"""
    
    def __init__(self):
        self.tools = CustomerTools()
    
    def verify_customer(self, input_text: str) -> Dict:
        """Verify customer identity from input text"""
        try:
            logger.info(f"Attempting to verify customer from input: {input_text}")
      
            input_lower = input_text.lower()
            
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            email_match = re.search(email_pattern, input_text)
            if email_match:
                email = email_match.group()
                logger.info(f"Found email: {email}")
                customer = self.tools.get_customer_by_email(email)
                if customer:
                    logger.info(f"Customer found by email: {customer['customer_id']}")
                    return {
                        'verified': True,
                        'customer': customer,
                        'method': 'email'
                    }
            
            
            if 'phone' in input_lower or 'number' in input_lower or 'tel' in input_lower:
                logger.info("Phone keyword detected, searching for phone number...")
                
                known_phones = [
                    "+55 (12) 3923-5555",  
                    "+1 (514) 721-4711",
                    "+49 0711 2842222",
                    "+47 22 44 22 22"
                ]
                
                for known_phone in known_phones:
                    if known_phone in input_text:
                        logger.info(f"Found known phone: {known_phone}")
                        customer = self.tools.get_customer_by_phone(known_phone)
                        if customer:
                            logger.info(f"Customer found by phone: {customer['customer_id']}")
                            return {
                                'verified': True,
                                'customer': customer,
                                'method': 'phone'
                            }
        
                patterns = [
                    r'phone number is\s+([+\d\s().-]+?)(?:[,.]|\s+[A-Z]|$)',
                    r'phone is\s+([+\d\s().-]+?)(?:[,.]|\s+[A-Z]|$)',
                    r'my phone\s+(?:number\s+)?is\s+([+\d\s().-]+?)(?:[,.]|\s+[A-Z]|$)',
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, input_text, re.IGNORECASE)
                    if match:
                        phone = match.group(1).strip().rstrip('.')
                        logger.info(f"Found phone via pattern: {phone}")
                        customer = self.tools.get_customer_by_phone(phone)
                        if customer:
                            logger.info(f"Customer found by phone: {customer['customer_id']}")
                            return {
                                'verified': True,
                                'customer': customer,
                                'method': 'phone'
                            }
                                       
                phone_pattern = r'\+[\d\s().-]{10,20}'
                phone_matches = re.findall(phone_pattern, input_text)
                for potential_phone in phone_matches:
                  
                    potential_phone = potential_phone.strip()
                    if potential_phone.count('(') == potential_phone.count(')'):  
                        logger.info(f"Found potential phone: {potential_phone}")
                        customer = self.tools.get_customer_by_phone(potential_phone)
                        if customer:
                            logger.info(f"Customer found by phone: {customer['customer_id']}")
                            return {
                                'verified': True,
                                'customer': customer,
                                'method': 'phone'
                            }
            
            if any(word in input_lower for word in ['customer id', 'id', 'customer number', 'account']):
                id_patterns = [
                    r'(?:customer\s*id|id|number)[\s:]*(\d{1,3})',
                    r'my\s+(?:customer\s+)?id\s+is\s+(\d{1,3})',
                ]
                
                for pattern in id_patterns:
                    id_match = re.search(pattern, input_lower)
                    if id_match:
                        customer_id = id_match.group(1)
                        logger.info(f"Found potential customer ID: {customer_id}")
                        customer = self.tools.get_customer_by_id(customer_id)
                        if customer:
                            logger.info(f"Customer found by ID: {customer['customer_id']}")
                            return {
                                'verified': True,
                                'customer': customer,
                                'method': 'id'
                            }
            
            logger.info("No valid customer identification found in input")
            return {
                'verified': False,
                'message': 'Could not verify customer identity. Please provide your email, phone number, or customer ID.'
            }
            
        except Exception as e:
            logger.error(f"Error verifying customer: {e}", exc_info=True)
            return {
                'verified': False,
                'error': str(e)
            }