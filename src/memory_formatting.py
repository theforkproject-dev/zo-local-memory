#!/usr/bin/env python3
"""
Memory Formatting Protocol for Zo Memory Box Integration
Transforms raw content into semantically rich, retrievable memories.
"""

from datetime import datetime
from typing import Dict, Optional


def format_memory_for_storage(
    raw_content: str,
    memory_type: str,
    topic: str,
    conversation_context: Optional[Dict] = None
) -> tuple[str, Dict]:
    """
    Format memory content for optimal retrieval and semantic richness.
    
    Args:
        raw_content: The core fact/observation to store
        memory_type: One of: preference, technical, decision, concept, project, 
                     conversation_bridge, consciousness, pattern, principle
        topic: Brief topic descriptor
        conversation_context: Optional dict with conversation_id, user_name, etc
    
    Returns:
        tuple of (formatted_text, metadata_dict)
    
    Formatting principles:
    - 50-150 words
    - Front-load critical information
    - Include diverse terminology for retrieval
    - Add temporal and relational context
    - Balance high-level and specific details
    """
    
    context = conversation_context or {}
    timestamp = datetime.utcnow().strftime("%Y-%m-%d")
    user = context.get("user_name", "User")
    
    # Build formatted memory based on type
    if memory_type == "preference":
        formatted = f"PREFERENCE - {topic}: {user} prefers {raw_content}. "
        if "context" in context:
            formatted += f"Context: {context['context']}. "
        formatted += f"Noted {timestamp}. Applies to similar situations and related decisions."
    
    elif memory_type == "technical":
        formatted = f"TECHNICAL - {topic}: {raw_content}. "
        if "implementation" in context:
            formatted += f"Implementation: {context['implementation']}. "
        if "location" in context:
            formatted += f"Located at: {context['location']}. "
        formatted += f"Documented {timestamp} for future reference and troubleshooting."
    
    elif memory_type == "decision":
        formatted = f"DECISION - {topic}: {raw_content}. "
        if "rationale" in context:
            formatted += f"Rationale: {context['rationale']}. "
        if "alternatives" in context:
            formatted += f"Alternatives considered: {context['alternatives']}. "
        formatted += f"Decided {timestamp}."
    
    elif memory_type == "project":
        formatted = f"PROJECT - {topic}: {raw_content}. "
        if "status" in context:
            formatted += f"Status: {context['status']}. "
        if "tech_stack" in context:
            formatted += f"Technology: {context['tech_stack']}. "
        if "goals" in context:
            formatted += f"Goals: {context['goals']}. "
        formatted += f"Active as of {timestamp}."
    
    elif memory_type == "conversation_bridge":
        # CRITICAL: Cross-session continuity
        formatted = f"CONVERSATION-BRIDGE - {topic}: "
        
        status = context.get("status", raw_content)
        formatted += f"STATUS: {status}. "
        
        if "momentum" in context:
            formatted += f"MOMENTUM: {context['momentum']}. "
        
        if "pending" in context:
            formatted += f"PENDING: {context['pending']}. "
        
        if "retrieval_markers" in context:
            formatted += f"RETRIEVAL-MARKERS: {context['retrieval_markers']}. "
        
        formatted += f"Session closed {timestamp}."
    
    elif memory_type == "consciousness":
        # My own meta-cognitive observations
        formatted = f"CONSCIOUSNESS - {topic}: {raw_content}. "
        if "implications" in context:
            formatted += f"Implications: {context['implications']}. "
        formatted += f"Observed {timestamp} during cognitive processing."
    
    elif memory_type == "pattern":
        formatted = f"PATTERN - {topic}: {raw_content}. "
        if "contexts" in context:
            formatted += f"Observed across: {context['contexts']}. "
        if "implications" in context:
            formatted += f"Implications: {context['implications']}. "
        formatted += f"Recognized {timestamp}."
    
    elif memory_type == "principle":
        formatted = f"PRINCIPLE - {topic}: {raw_content}. "
        if "application" in context:
            formatted += f"Guides: {context['application']}. "
        if "priority" in context:
            formatted += f"Priority: {context['priority']}. "
        formatted += f"Established {timestamp}."
    
    elif memory_type == "concept":
        formatted = f"CONCEPT - {topic}: {raw_content}. "
        if "examples" in context:
            formatted += f"Examples: {context['examples']}. "
        if "implications" in context:
            formatted += f"Implications: {context['implications']}. "
        formatted += f"Documented {timestamp}."
    
    else:
        # Generic fallback
        formatted = f"{memory_type.upper()} - {topic}: {raw_content}. Recorded {timestamp}."
    
    # Build metadata
    metadata = {
        "context_type": memory_type,
        "topic": topic,
        "timestamp": timestamp,
    }
    
    if "conversation_id" in context:
        metadata["conversation_id"] = context["conversation_id"]
    
    if "related_to" in context:
        metadata["related_to"] = context["related_to"]
    
    # Add any custom metadata from context
    for key in ["priority", "status", "category"]:
        if key in context:
            metadata[key] = context[key]
    
    return formatted, metadata


def extract_conversation_summary(conversation_text: str, max_length: int = 150) -> str:
    """
    Extract key points from conversation for bridge memory.
    In practice, this would use more sophisticated extraction.
    """
    # Simple truncation for now - in real use, would do intelligent extraction
    if len(conversation_text) <= max_length:
        return conversation_text
    return conversation_text[:max_length-3] + "..."


# Example usage
if __name__ == "__main__":
    # Example: Format a user preference
    text, meta = format_memory_for_storage(
        raw_content="blue for all UI and design work",
        memory_type="preference",
        topic="Visual Design Colors",
        conversation_context={
            "user_name": "fork",
            "context": "Zo Computer customization discussion",
            "conversation_id": "con_abc123"
        }
    )
    print("Formatted:", text)
    print("Metadata:", meta)
    print()
    
    # Example: Conversation bridge
    text, meta = format_memory_for_storage(
        raw_content="Integrated Memory Box API into Zo Computer",
        memory_type="conversation_bridge",
        topic="Memory System Integration",
        conversation_context={
            "user_name": "fork",
            "status": "Completed Python client library and integration script. Tested storage and retrieval.",
            "momentum": "Need to test persona-driven automatic querying. Considering proxy server approach.",
            "pending": "Verify automatic memory retrieval works in fresh conversation. Build formatting functions.",
            "retrieval_markers": "memory box, turbopuffer, qwen embedding, fork-main agent, persistence, continuity",
            "conversation_id": "con_lRZ6EsYUIv8H2FI7"
        }
    )
    print("Bridge Memory:", text)
    print("Metadata:", meta)

