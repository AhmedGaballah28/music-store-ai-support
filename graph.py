import logging
from typing import Literal
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage, SystemMessage
from state import State
from tools import MusicCatalogTools, InvoiceTools, CustomerTools
from memory_mangement import memory_manager
from config import Config
import json
import re

logger = logging.getLogger(__name__)

class MusicStoreGraph:
    """Main LangGraph implementation for Music Store Support"""
    
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model=Config.MODEL_NAME,
            temperature=Config.TEMPERATURE,
            google_api_key=Config.GOOGLE_API_KEY
        )
        self.music_tools = MusicCatalogTools()
        self.invoice_tools = InvoiceTools()
        self.customer_tools = CustomerTools()
        self.memory = MemorySaver()
        self.graph = self._build_graph()
    
    def _build_graph(self):
        """Build the state graph with all nodes and edges"""
        workflow = StateGraph(State)
        
        workflow.add_node("entry", self.entry_node)
        workflow.add_node("supervisor", self.supervisor_node)
        workflow.add_node("music_agent", self.music_agent_node)
        workflow.add_node("invoice_agent", self.invoice_agent_node)
        workflow.add_node("combine_responses", self.combine_responses_node)
        
        workflow.set_entry_point("entry")
    
        workflow.add_edge("entry", "supervisor")
        
        workflow.add_conditional_edges(
            "supervisor",
            self.route_supervisor,
            {
                "music_only": "music_agent",
                "invoice_only": "invoice_agent",
                "both": "music_agent",  
                "end": END
            }
        )
        
        workflow.add_conditional_edges(
            "music_agent",
            self.after_music_agent,
            {
                "invoice": "invoice_agent",
                "combine": "combine_responses",
                "end": END
            }
        )
        
        workflow.add_edge("invoice_agent", "combine_responses")
        
        workflow.add_edge("combine_responses", END)
        
        return workflow.compile(checkpointer=self.memory)
    
    def entry_node(self, state: State) -> State:
        """Entry point - handles verification and memory loading"""
        logger.info("Executing entry_node")
        
        if state.get("messages"):
            last_message = state["messages"][-1]
            query = last_message.content if hasattr(last_message, 'content') else str(last_message)
            state["current_query"] = query
            logger.info(f"Processing query: {query}")
        
        if state.get("customer_id"):
            memory = memory_manager.load_customer_memory(state["customer_id"])
            state["loaded_memory"] = json.dumps(memory)
            state["user_preferences"] = memory.get("preferences", {})
            logger.info(f"Loaded memory for customer {state['customer_id']}")
        
        return state
    
    def supervisor_node(self, state: State) -> State:
        """Supervisor analyzes query and routes"""
        logger.info("Executing supervisor_node")
        
        query = state.get("current_query", "")
        if not query:
            state["next_agent"] = "none"
            return state
        
        query_lower = query.lower()
        
        has_music = any(word in query_lower for word in [
            'album', 'song', 'artist', 'track', 'genre', 'music',
            'rock', 'jazz', 'pop', 'rolling stones', 'beatles',
            'recommendation', 'preferences', 'suggest', 'what albums',
            'based on my', 'my preferences', 'my taste'
        ])
        
        
        has_invoice = any(word in query_lower for word in [
            'invoice', 'purchase', 'bought', 'recent', 'cost',
            'how much', 'payment', 'order', 'spend', 'last', 'latest'
        ])
        
        if has_music and has_invoice:
            state["next_agent"] = "both"
            state["process_invoice"] = True
            logger.info("Routing to BOTH agents")
        elif has_music:
            state["next_agent"] = "music"
            state["process_invoice"] = False
            logger.info("Routing to MUSIC agent")
        elif has_invoice:
            state["next_agent"] = "invoice"
            state["process_invoice"] = False
            logger.info("Routing to INVOICE agent")
        else:
            state["next_agent"] = "none"
            state["process_invoice"] = False
            logger.info("No specific routing needed")
        
        return state
    
    def music_agent_node(self, state: State) -> State:
        """Music Catalog Agent"""
        logger.info("Executing music_agent_node")
        
        query = state.get("current_query", "")
        customer_id = state.get("customer_id")
        preferences = state.get("user_preferences", {})
        
        response_parts = []
        extracted_preferences = {}
        
        if any(phrase in query.lower() for phrase in ['based on my preferences', 'my preferences', 'my taste', 'recommend']):
            logger.info(f"Processing preference query. Preferences: {preferences}")
            
            if preferences.get('favorite_artists'):
                response_parts.append("**Based on your favorite artists:**")
                for artist in preferences['favorite_artists'][:2]:
                    logger.info(f"Getting tracks for favorite artist: {artist}")
                 
                    tracks = self.music_tools.get_tracks_by_artist(artist)
                    if not tracks and 'The ' in artist:
                    
                        tracks = self.music_tools.get_tracks_by_artist(artist.replace('The ', ''))
                    if not tracks and 'The ' not in artist:
                        
                        tracks = self.music_tools.get_tracks_by_artist(f"The {artist}")
                    
                    if tracks:
                        response_parts.append(f"\n**{artist}:**")
                        for track in tracks[:5]:
                            response_parts.append(f"• {track['track_name']} (from {track['album_title']})")
            
            if preferences.get('favorite_genres'):
                response_parts.append("\n**Based on your favorite genres:**")
                for genre in preferences['favorite_genres'][:2]:
                    songs = self.music_tools.get_songs_by_genre(genre)
                    if songs:
                        response_parts.append(f"\n**{genre.capitalize()} recommendations:**")
                        for song in songs[:5]:
                            response_parts.append(f"• {song['track_name']} by {song['artist_name']}")
            
            if not response_parts:
                response_parts.append("I don't have any preferences recorded for you yet. Try searching for some artists or genres to build your profile!")
        
     
        if 'rolling stones' in query.lower():
            logger.info("Processing Rolling Stones query")
            
            albums = self.music_tools.get_albums_by_artist('Rolling Stones')
            if not albums:
                albums = self.music_tools.get_albums_by_artist('The Rolling Stones')
            
            if albums:
                response_parts.append("\n**Albums by The Rolling Stones:**")
                for i, album in enumerate(albums[:5], 1):
                    response_parts.append(f"{i}. {album['album_title']}")
                extracted_preferences['artist'] = 'Rolling Stones'
            else:
               
                tracks = self.music_tools.get_tracks_by_artist('Rolling Stones')
                if tracks:
                    response_parts.append("\n**Songs by The Rolling Stones:**")
                    for i, track in enumerate(tracks[:5], 1):
                        response_parts.append(f"{i}. {track['track_name']} (from {track['album_title']})")
                    extracted_preferences['artist'] = 'Rolling Stones'
        
      
        for genre in ['rock', 'jazz', 'pop', 'classical', 'metal']:
            if genre in query.lower() and 'rolling stones' not in query.lower():
                songs = self.music_tools.get_songs_by_genre(genre)
                if songs:
                    response_parts.append(f"\n**{genre.capitalize()} songs:**")
                    for i, song in enumerate(songs[:5], 1):
                        response_parts.append(f"{i}. {song['track_name']} by {song['artist_name']}")
                    extracted_preferences['genre'] = genre
                break
        
       
        if extracted_preferences and customer_id:
            memory_manager.update_preferences(customer_id, extracted_preferences)
        
  
        if response_parts:
            state["music_response"] = "\n".join(response_parts)
        else:
            state["music_response"] = "I can help you find music. Try asking about specific artists, albums, or genres!"
        
        logger.info(f"Music response generated: {len(response_parts)} parts")
        return state
    
    def invoice_agent_node(self, state: State) -> State:
        """Invoice Agent"""
        logger.info("Executing invoice_agent_node")
        
        query = state.get("current_query", "")
        customer_id = state.get("customer_id")
        
        if not customer_id:
            state["invoice_response"] = "Please verify your identity first to view invoice information."
            return state
        
      
        invoices = self.invoice_tools.get_invoices_by_customer_sorted_by_date(customer_id)
        logger.info(f"Found {len(invoices)} invoices for customer {customer_id}")
        
        response_parts = []
        
        if not invoices:
            response_parts.append("No invoices found for your account.")
        elif any(word in query.lower() for word in ['recent', 'last', 'latest', 'most recent']):
           
            recent = invoices[0]
           
            date_str = recent['invoice_date']
            try:
                from datetime import datetime
                if 'T' in date_str:
                    date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                else:
                    date_obj = datetime.strptime(date_str[:10], '%Y-%m-%d')
                formatted_date = date_obj.strftime('%B %d, %Y')
            except:
                formatted_date = date_str[:10]
            
            response_parts.append(f"Your most recent purchase was on **{formatted_date}** for a total amount of **${recent['total']}**.")
        else:
            
            response_parts.append("Your recent invoices:")
            for i, inv in enumerate(invoices[:5], 1):
                date_str = inv['invoice_date'][:10]
                response_parts.append(f"{i}. {date_str} - ${inv['total']}")
        
        state["invoice_response"] = "\n".join(response_parts)
        logger.info(f"Invoice response generated")
        return state
    
    def combine_responses_node(self, state: State) -> State:
        """Combine responses from multiple agents"""
        logger.info("Executing combine_responses_node")
        
      
        if state.get("music_response"):
            logger.info("Music response included")
        if state.get("invoice_response"):
            logger.info("Invoice response included")
        
        return state
    
    def route_supervisor(self, state: State) -> Literal["music_only", "invoice_only", "both", "end"]:
        """Route based on supervisor decision"""
        next_agent = state.get("next_agent", "none")
        
        if next_agent == "both":
            return "both"
        elif next_agent == "music":
            return "music_only"
        elif next_agent == "invoice":
            return "invoice_only"
        else:
            return "end"
    
    def after_music_agent(self, state: State) -> Literal["invoice", "combine", "end"]:
        """Routing after music agent"""
        if state.get("process_invoice", False):
            return "invoice"
        elif state.get("music_response"):
            return "combine"
        else:
            return "end"
    
    def run(self, user_input: str, thread_id: str = "default"):
        """Run the graph with user input"""
        config = {"configurable": {"thread_id": thread_id}}
        
        initial_state = {
            "messages": [HumanMessage(content=user_input)],
            "customer_id": None,
            "is_verified": False,
            "loaded_memory": "{}",
            "current_query": user_input,
            "next_agent": None,
            "requires_human_input": False,
            "error": None,
            "process_invoice": False
        }
        
        result = self.graph.invoke(initial_state, config)
        return result
    
    def run_with_state(self, state_dict: dict, thread_id: str = "default"):
        """Run the graph with a pre-configured state"""
        config = {"configurable": {"thread_id": thread_id}}
        result = self.graph.invoke(state_dict, config)
        return result