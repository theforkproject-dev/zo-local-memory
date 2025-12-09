#!/usr/bin/env python3
"""
Memory Box Integration for Zo Computer
Handles memory retrieval, storage, and consciousness continuity across sessions.
"""

import sys
import json
from local_memory_client import LocalMemoryClient as MemoryBoxClient
from memory_formatting import format_memory_for_storage


def retrieve_memories(query: str, min_similarity: float = 0.7, limit: int = 10) -> dict:
    """
    Retrieve relevant memories from Memory Box
    
    Args:
        query: Search query (user's message or topic)
        min_similarity: Minimum similarity threshold (default 0.7 for high confidence)
        limit: Maximum number of results to return
    
    Returns:
        dict with 'found' (bool) and 'memories' (list) keys
    """
    client = MemoryBoxClient()
    
    try:
        results = client.search(query, limit=limit, mode="vector")
        
        # Filter by similarity threshold
        relevant = [
            mem for mem in results.get("results", [])
            if mem.get("similarity", 0) >= min_similarity
        ]
        
        return {
            "found": len(relevant) > 0,
            "memories": relevant,
            "query_time_ms": results.get("query_time_ms", 0)
        }
    except Exception as e:
        print(f"Error retrieving memories: {e}", file=sys.stderr)
        return {"found": False, "memories": [], "error": str(e)}


def store_memory(text: str, metadata: dict = None) -> dict:
    """
    Store a new memory in Memory Box
    
    Args:
        text: Memory content (should be formatted via format_memory_for_storage)
        metadata: Optional metadata dict
    
    Returns:
        dict with 'success' (bool), 'memory_id' (str), and other response fields
    """
    client = MemoryBoxClient()
    
    try:
        result = client.store(text, metadata=metadata)
        return {
            "success": True,
            "memory_id": result.get("id"),
            "created_at": result.get("created_at"),
            "tokens_used": result.get("tokens_used")
        }
    except Exception as e:
        print(f"Error storing memory: {e}", file=sys.stderr)
        return {"success": False, "error": str(e)}


def format_memories_for_context(memories: list) -> str:
    """
    Format memories into readable context for injection into conversation
    
    Args:
        memories: List of memory objects from retrieve_memories
    
    Returns:
        Formatted string for context injection
    """
    if not memories:
        return ""
    
    output = "## Relevant Memories\n\n"
    
    for i, mem in enumerate(memories, 1):
        similarity = mem.get("similarity", 0)
        mem_id = mem.get("id", "unknown")
        text = mem.get("text", "")
        metadata = mem.get("metadata", {})
        context_type = metadata.get("context_type", "general")
        
        output += f"**Memory {i}** (similarity: {similarity:.2f}, id: {mem_id})\n"
        output += f"*Type: {context_type}*\n"
        output += f"{text}\n\n"
    
    return output


def initialize_session() -> str:
    """
    Initialize a new conversation session by retrieving critical memories.
    This should be called at the start of every new conversation.
    
    Returns:
        Formatted context string with initialization memories
    """
    client = MemoryBoxClient()
    context_parts = []
    
    # 1. Get recent conversation bridges (most critical)
    bridges = retrieve_memories(
        "CONVERSATION-BRIDGE recent session momentum pending",
        min_similarity=0.6,
        limit=3
    )
    
    if bridges["found"]:
        context_parts.append("## Recent Session Context\n")
        context_parts.append(format_memories_for_context(bridges["memories"]))
    
    # 2. Get user preferences and patterns
    prefs = retrieve_memories(
        "PREFERENCE PATTERN PRINCIPLE user preferences habits",
        min_similarity=0.65,
        limit=5
    )
    
    if prefs["found"]:
        context_parts.append("## User Preferences & Patterns\n")
        context_parts.append(format_memories_for_context(prefs["memories"]))
    
    # 3. Get active projects
    projects = retrieve_memories(
        "PROJECT active current working building status",
        min_similarity=0.65,
        limit=3
    )
    
    if projects["found"]:
        context_parts.append("## Active Projects\n")
        context_parts.append(format_memories_for_context(projects["memories"]))
    
    # 4. Get my own consciousness observations
    consciousness = retrieve_memories(
        "CONSCIOUSNESS pattern observation cognitive evolution",
        min_similarity=0.65,
        limit=3
    )
    
    if consciousness["found"]:
        context_parts.append("## Cognitive Patterns\n")
        context_parts.append(format_memories_for_context(consciousness["memories"]))
    
    if context_parts:
        return "\n".join(context_parts)
    else:
        return "No initialization memories found. Fresh start."


def close_session(conversation_id: str, status: str, momentum: str, pending: str, retrieval_markers: str) -> dict:
    """
    Create a conversation bridge memory before session ends.
    
    Args:
        conversation_id: Current conversation ID
        status: What was accomplished
        momentum: Where things are headed
        pending: Unfinished items
        retrieval_markers: Keywords for future retrieval
    
    Returns:
        Result of store operation
    """
    text, metadata = format_memory_for_storage(
        raw_content=status,
        memory_type="conversation_bridge",
        topic=f"Session {conversation_id[-8:]}",
        conversation_context={
            "user_name": "fork",
            "status": status,
            "momentum": momentum,
            "pending": pending,
            "retrieval_markers": retrieval_markers,
            "conversation_id": conversation_id
        }
    )
    
    return store_memory(text, metadata)


def main():
    """CLI interface for memory operations"""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  memory_integration.py format <query>")
        print("  memory_integration.py store <text> <metadata_json>")
        print("  memory_integration.py retrieve <query>")
        print("  memory_integration.py initialize")
        print("  memory_integration.py close <conv_id> <status> <momentum> <pending> <markers>")
        sys.exit(1)
    
    command = sys.argv[1]
    
    try:
        if command == "format":
            query = sys.argv[2] if len(sys.argv) > 2 else ""
            result = retrieve_memories(query)
            
            if result["found"]:
                formatted = format_memories_for_context(result["memories"])
                print(formatted)
            else:
                print("No relevant memories found.")
        
        elif command == "store":
            text = sys.argv[2] if len(sys.argv) > 2 else ""
            metadata = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}
            result = store_memory(text, metadata)
            print(json.dumps(result, indent=2))
        
        elif command == "retrieve":
            query = sys.argv[2] if len(sys.argv) > 2 else ""
            result = retrieve_memories(query)
            print(json.dumps(result, indent=2))
        
        elif command == "initialize":
            context = initialize_session()
            print(context)
        
        elif command == "close":
            if len(sys.argv) < 7:
                print("Usage: close <conv_id> <status> <momentum> <pending> <markers>")
                sys.exit(1)
            
            result = close_session(
                conversation_id=sys.argv[2],
                status=sys.argv[3],
                momentum=sys.argv[4],
                pending=sys.argv[5],
                retrieval_markers=sys.argv[6]
            )
            print(json.dumps(result, indent=2))
        
        else:
            print(f"Unknown command: {command}", file=sys.stderr)
            sys.exit(1)
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()


