import streamlit as st
import logging
from datetime import datetime
import json
from typing import Dict, List, Optional
import time
import html

from config import Config
from database import db_manager
from graph import MusicStoreGraph
from memory_mangement import memory_manager
from agents import CustomerVerificationAgent
from tools import CustomerTools


def sanitize_html(content: str) -> str:
    """Sanitize content to prevent XSS attacks"""
    if not content:
        return ""
    return html.escape(str(content))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="🎵 Digital Music Store Support",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .info-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        margin-bottom: 1rem;
    }
    .customer-verified {
        background-color: #d4edda;
        border-left: 4px solid #28a745;
        padding: 10px;
        margin: 10px 0;
        border-radius: 4px;
    }
    .customer-unverified {
        background-color: #f8d7da;
        border-left: 4px solid #dc3545;
        padding: 10px;
        margin: 10px 0;
        border-radius: 4px;
    }
    .agent-response {
        background-color: #f8f9fa;
        border-left: 4px solid #007bff;
        padding: 15px;
        margin: 10px 0;
        border-radius: 4px;
    }
    .memory-section {
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 10px;
        margin: 10px 0;
        border-radius: 4px;
    }
    .workflow-status {
        background-color: #e7f3ff;
        border-left: 4px solid #2196F3;
        padding: 10px;
        margin: 10px 0;
        border-radius: 4px;
    }
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.5rem 2rem;
        border-radius: 5px;
        font-weight: bold;
        transition: all 0.3s;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Initialize all session state variables"""
    if 'initialized' not in st.session_state:
        st.session_state.initialized = False
        st.session_state.graph = None
        st.session_state.customer_id = None
        st.session_state.customer_info = None
        st.session_state.is_verified = False
        st.session_state.messages = []
        st.session_state.thread_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        st.session_state.memory = {}
        st.session_state.pending_verification = False
        st.session_state.workflow_state = "idle"
        st.session_state.last_query = ""
        st.session_state.agent_responses = {}
        st.session_state.current_agents = []
        st.session_state.verification_attempt = ""
        st.session_state.graph_state = {}  

def initialize_system():
    """Initialize the database and graph system"""
    with st.spinner("initializing Music Store System..."):
        try:
            
            if not db_manager.initialize():
                st.error("failed to initialize database")
                return False
            
           
            try:
                stats = db_manager.test_connection()
                if stats['status'] != 'Connected':
                    st.error(f"database connection failed: {stats.get('error')}")
                    return False
                logger.info(f"database connected with {len(stats.get('tables', []))} tables")
            except Exception as e:
                logger.warning(f"could not test database connection: {e}")
            
            
            st.session_state.graph = MusicStoreGraph()
            st.session_state.initialized = True
            
            return True
        except Exception as e:
            st.error(f"system initialization failed: {str(e)}")
            logger.error(f"Initialization error: {e}", exc_info=True)
            return False

def verify_customer(input_text: str):
    """Verify customer identity"""
    verifier = CustomerVerificationAgent()
    result = verifier.verify_customer(input_text)
    
    if result['verified']:
        st.session_state.customer_id = result['customer']['customer_id']
        st.session_state.customer_info = result['customer']
        st.session_state.is_verified = True
        st.session_state.pending_verification = False
        
        memory = memory_manager.load_customer_memory(st.session_state.customer_id)
        st.session_state.memory = memory
        
        st.session_state.graph_state['customer_id'] = st.session_state.customer_id
        st.session_state.graph_state['is_verified'] = True
        st.session_state.graph_state['customer_info'] = st.session_state.customer_info
        
        return True
    return False

def process_query(query: str):
    """process user query through the graph"""
    try:
        st.session_state.workflow_state = "processing"
        st.session_state.last_query = query
        st.session_state.agent_responses = {}
        st.session_state.current_agents = []
    
        st.session_state.messages.append({
            'role': 'user',
            'content': query,
            'timestamp': datetime.now().isoformat()
        })
        
        if 'phone' in query.lower() or 'email' in query.lower() or '@' in query:
            if not st.session_state.is_verified:
                if verify_customer(query):
                    verification_msg = f"**Customer Verified**: {st.session_state.customer_info['first_name']} {st.session_state.customer_info['last_name']}"
                    st.session_state.messages.append({
                        'role': 'system',
                        'content': verification_msg,
                        'timestamp': datetime.now().isoformat()
                    })
        
    
        with st.spinner("🤖 Processing your request..."):
            from langchain.schema import HumanMessage
            
            state_dict = {
                "messages": [HumanMessage(content=query)],
                "customer_id": st.session_state.customer_id if st.session_state.is_verified else None,
                "is_verified": st.session_state.is_verified,
                "customer_info": st.session_state.customer_info if st.session_state.is_verified else None,
                "loaded_memory": json.dumps(st.session_state.memory) if st.session_state.is_verified else "{}",
                "user_preferences": st.session_state.memory.get('preferences', {}) if st.session_state.is_verified else {},
                "current_query": query,
                "next_agent": None,
                "requires_human_input": False,
                "error": None,
                "process_invoice": False,
                "music_response": None,
                "invoice_response": None
            }
            
            query_lower = query.lower()
            needs_invoice_verification = any(word in query_lower for word in [
                'invoice', 'purchase', 'bought', 'order', 'payment',
                'recent', 'last', 'latest', 'spend', 'cost', 'how much'
            ])
            
            if needs_invoice_verification and not st.session_state.is_verified:
                st.session_state.pending_verification = True
                st.session_state.verification_attempt = query
                st.session_state.workflow_state = "waiting_verification"
                
                verification_request = "🔐 **Verification Required**: To access invoice information, please provide your customer ID, email, or phone number."
                st.session_state.messages.append({
                    'role': 'system',
                    'content': verification_request,
                    'timestamp': datetime.now().isoformat()
                })
                return
            
          
            result = st.session_state.graph.run_with_state(
                state_dict=state_dict,
                thread_id=st.session_state.thread_id
            )
        
        if result:
            logger.info(f"Graph result keys: {result.keys()}")
            logger.info(f"Music response: {result.get('music_response')}")
            logger.info(f"Invoice response: {result.get('invoice_response')}")
            
           
            has_music = result.get('music_response') and result['music_response'] != "I can help you find music. Try asking about specific artists, albums, or genres!"
            has_invoice = result.get('invoice_response') and result['invoice_response'] != "Please verify your identity first to view invoice information."
            
            if has_music and has_invoice:
        
                st.session_state.agent_responses['music'] = result['music_response']
                st.session_state.agent_responses['invoice'] = result['invoice_response']
                st.session_state.current_agents = ['Invoice Agent', 'Music Catalog Agent']
                
                combined_response = f"""I've found the information you requested:

{result['invoice_response']}

Also, here are the music results:
{result['music_response']}

Is there anything else you'd like to know?"""
                
                st.session_state.messages.append({
                    'role': 'assistant',
                    'content': combined_response,
                    'timestamp': datetime.now().isoformat(),
                    'agents': st.session_state.current_agents
                })
            elif has_music:
                st.session_state.agent_responses['music'] = result['music_response']
                st.session_state.current_agents.append('Music Catalog Agent')
                st.session_state.messages.append({
                    'role': 'assistant',
                    'content': result['music_response'],
                    'timestamp': datetime.now().isoformat(),
                    'agents': ['Music Catalog Agent']
                })
            elif has_invoice:
                st.session_state.agent_responses['invoice'] = result['invoice_response']
                st.session_state.current_agents.append('Invoice Agent')
                st.session_state.messages.append({
                    'role': 'assistant',
                    'content': result['invoice_response'],
                    'timestamp': datetime.now().isoformat(),
                    'agents': ['Invoice Agent']
                })
            else:
               
                if result.get('error'):
                    st.session_state.messages.append({
                        'role': 'system',
                        'content': f" {result['error']}",
                        'timestamp': datetime.now().isoformat()
                    })
                else:
                    
                    logger.warning(f"No meaningful response from graph. Result: {result}")
                    st.session_state.messages.append({
                        'role': 'assistant',
                        'content': "I can help you with music recommendations and invoice information. What would you like to know?",
                        'timestamp': datetime.now().isoformat()
                    })
        
        st.session_state.workflow_state = "idle"
        
    except Exception as e:
        logger.error(f"Error processing query: {e}", exc_info=True)
        st.session_state.messages.append({
            'role': 'system',
            'content': f"error: {str(e)}",
            'timestamp': datetime.now().isoformat()
        })
        st.session_state.workflow_state = "error"
def display_sidebar():
    """Display sidebar with customer info and memory"""
    with st.sidebar:
        st.markdown("## music Store Support")
   
        st.markdown("### 👤 Customer Status")
        if st.session_state.is_verified:
            # Sanitize customer info before displaying
            first_name = sanitize_html(st.session_state.customer_info['first_name'])
            last_name = sanitize_html(st.session_state.customer_info['last_name'])
            customer_id = sanitize_html(str(st.session_state.customer_id))
            email = sanitize_html(st.session_state.customer_info['email'])
            city = sanitize_html(st.session_state.customer_info['city'])
            country = sanitize_html(st.session_state.customer_info['country'])
            
            st.markdown(f"""
            <div class="customer-verified">
                <strong> Verified Customer</strong><br>
                Name: {first_name} {last_name}<br>
                ID: {customer_id}<br>
                Email: {email}<br>
                Location: {city}, {country}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="customer-unverified">
                <strong> not Verified</strong><br>
                Please provide your customer ID, email, or phone number
            </div>
            """, unsafe_allow_html=True)
        
    
        if st.session_state.is_verified and st.session_state.memory:
            st.markdown("Your Preferences")
            
            preferences = st.session_state.memory.get('preferences', {})
            if preferences.get('favorite_artists'):
                st.markdown("**Favorite Artists:**")
                for artist in preferences['favorite_artists'][:3]:
                    st.markdown(f"• {artist}")
            
            if preferences.get('favorite_genres'):
                st.markdown("**Favorite Genres:**")
                for genre in preferences['favorite_genres'][:3]:
                    st.markdown(f"• {genre}")
            
            if preferences.get('favorite_albums'):
                st.markdown("**Recent Albums:**")
                for album in preferences['favorite_albums'][:3]:
                    st.markdown(f"• {album}")
        
        
        st.markdown("### Workflow Status")
        status_emoji = {
            "idle": " Ready",
            "processing": "⚙️ Processing",
            "waiting_verification": "🔐 Awaiting Verification",
            "error": " Error"
        }
        st.markdown(f"**Status:** {status_emoji.get(st.session_state.workflow_state, ' Unknown')}")
        
        if st.session_state.current_agents:
            st.markdown("**Active Agents:**")
            for agent in st.session_state.current_agents:
                st.markdown(f"• {agent}")
        
      
        with st.expander("System Information"):
            st.markdown(f"**Session ID:** `{st.session_state.thread_id}`")
            st.markdown(f"**Database:** {'Connected' if st.session_state.initialized else ' Not Connected'}")
            st.markdown(f"**Total Messages:** {len(st.session_state.messages)}")
            
            if st.button(" Reset Session"):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()

def display_chat_interface():
    """Display the main chat interface"""
  
    st.markdown("""
    <div class="main-header">
        <h1 style="color: white; text-align: center; margin: 0;">🎵 Digital Music Store Customer Support</h1>
        <p style="color: rgba(255,255,255,0.9); text-align: center; margin-top: 10px;">
            Ask me about music, artists, albums, genres, or check your invoices and purchase history!
        </p>
    </div>
    """, unsafe_allow_html=True)
    
   
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("Browse Rock Music", use_container_width=True):
            process_query("Show me some rock music")
            st.rerun()
    
    with col2:
        if st.button("Recent Purchase", use_container_width=True):
            process_query("What was my most recent purchase?")
            st.rerun()
    
    with col3:
        if st.button(" My Preferences", use_container_width=True):
            process_query("Show me songs based on my preferences")
            st.rerun()
    
    with col4:
        if st.button("Rolling Stones", use_container_width=True):
            process_query("What albums do you have by the Rolling Stones?")
            st.rerun()
    
    
    chat_container = st.container()
    
    with chat_container:
        
        for message in st.session_state.messages:
            if message['role'] == 'user':
                with st.chat_message("user", avatar="👤"):
                    st.markdown(message['content'])
                    st.caption(f" {message['timestamp']}")
            
            elif message['role'] == 'assistant':
                with st.chat_message("assistant", avatar="🤖"):
                    st.markdown(message['content'])
                    if message.get('agents'):
                        st.caption(f"Handled by: {', '.join(message['agents'])}")
                    st.caption(f"{message['timestamp']}")
            
            elif message['role'] == 'system':
                with st.chat_message("assistant", avatar="⚙️"):
                    st.markdown(message['content'])
                    st.caption(f"{message['timestamp']}")
    
  
    if st.session_state.pending_verification:
        st.info(" **Verification Required**: Please enter your customer ID, email, or phone number to continue.")
    

    user_input = st.chat_input(
        placeholder="Type your message here... (e.g., 'Show me albums by The Beatles' or 'What was my last purchase?')",
        disabled=not st.session_state.initialized
    )
    
    if user_input:
        process_query(user_input)
        st.rerun()

def display_example_queries():
    """Display example queries for users"""
    with st.expander("Example Queries", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **Music Queries:**
            - "What albums do you have by The Beatles?"
            - "Show me some jazz music"
            - "Find songs by Led Zeppelin"
            - "What rock albums do you have?"
            - "Show me songs based on my preferences"
            """)
        
        with col2:
            st.markdown("""
            ** Invoice Queries:**
            - "What was my most recent purchase?"
            - "Show me all my invoices"
            - "How much did I spend last time?"
            - "Who was my support representative?"

            **Verification Examples:**
            - "My email is luisg@embraer.com.br"
            - "My phone number is +55 ********"
            - "My customer ID is 1"
            """)

def main():
    """Main application entry point"""
  
    initialize_session_state()
    
    if not st.session_state.initialized:
        if not initialize_system():
            st.error("Failed to initialize the system. Please refresh the page.")
            return
    
    display_sidebar()
    
    display_chat_interface()
    
    display_example_queries()
    
    
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 20px;">
        <p> Digital Music Store Support System | Powered by LangGraph & Google Gemini</p>
        <p style="font-size: 12px;">Multi-Agent System with Customer Verification, Music Catalog, and Invoice Management</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()