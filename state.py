from typing_extensions import TypedDict
from typing import Annotated, List, Optional, Dict, Any
from langgraph.graph.message import AnyMessage, add_messages

class State(TypedDict):
    """represents the state of our LangGraph agent"""
    customer_id: Optional[str]
    messages: Annotated[List[AnyMessage], add_messages]
    loaded_memory: Optional[str]
    current_query: Optional[str]
    is_verified: bool
    next_agent: Optional[str]
    requires_human_input: bool
    error: Optional[str]
    process_invoice: bool
    user_preferences: Optional[Dict[str, Any]]
    customer_info: Optional[Dict[str, Any]]
    music_response: Optional[str]
    invoice_response: Optional[str]