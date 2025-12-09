#!/usr/bin/env python3
"""
Local Memory Client for Zo Computer
Provides semantic memory storage and retrieval using local Ollama + Turso.
Drop-in replacement for MemoryBoxClient with same API surface.
"""

import os
import json
import time
import uuid
from typing import Optional, Dict, List, Any
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from datetime import datetime, timezone


class LocalMemoryClient:
    """Client for local memory storage (Ollama + Turso)"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,  # Ignored, kept for compatibility
        agent_id: Optional[str] = None,
        base_url: Optional[str] = None,  # Ignored, kept for compatibility
        ollama_url: Optional[str] = None,
        turso_url: Optional[str] = None
    ):
        self.agent_id = agent_id or os.getenv("MEMORY_BOX_AGENT_ID", "fork-main")
        self.ollama_url = (ollama_url or "http://localhost:11434").rstrip("/")
        self.turso_url = (turso_url or "http://localhost:8787").rstrip("/")
    
    def _embed(self, text: str) -> List[float]:
        """Generate embedding using local Ollama"""
        url = f"{self.ollama_url}/api/embed"
        headers = {"Content-Type": "application/json"}
        data = json.dumps({
            "model": "nomic-embed-text",
            "input": text
        }).encode("utf-8")
        
        try:
            req = Request(url, data=data, headers=headers, method="POST")
            with urlopen(req, timeout=30) as response:
                result = json.loads(response.read().decode("utf-8"))
                return result["embeddings"][0]
        except Exception as e:
            raise Exception(f"Ollama embedding error: {e}")
    
    def _turso_execute(self, statements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute statements on Turso"""
        url = self.turso_url
        headers = {"Content-Type": "application/json"}
        data = json.dumps({"statements": statements}).encode("utf-8")
        
        try:
            req = Request(url, data=data, headers=headers, method="POST")
            with urlopen(req, timeout=30) as response:
                return json.loads(response.read().decode("utf-8"))
        except Exception as e:
            raise Exception(f"Turso execution error: {e}")
    
    def _format_timestamp(self, unix_ts: int) -> str:
        """Convert Unix timestamp to ISO 8601 format"""
        return datetime.fromtimestamp(unix_ts, tz=timezone.utc).isoformat()
    
    def store(self, text: str, metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Store a memory
        
        Args:
            text: Memory content
            metadata: Optional metadata dict
        
        Returns:
            {
                "id": "mem_abc123",
                "text": "...",
                "created_at": "2025-12-09T13:45:00Z",
                "tokens_used": 0  # Always 0 for local
            }
        """
        if len(text) > 100000:
            raise ValueError("Text exceeds 100k character limit")
        
        # Generate embedding
        embedding = self._embed(text)
        
        # Generate ID and timestamps
        memory_id = f"mem_{uuid.uuid4().hex[:12]}"
        timestamp = int(time.time())
        
        # Prepare metadata
        meta_json = json.dumps(metadata) if metadata else "{}"
        
        # Convert embedding to vector format (JSON array as string)
        vector_data = json.dumps(embedding)
        
        # Insert into Turso
        statements = [{
            "q": "INSERT INTO memories (id, agent_id, content, embedding, metadata, created_at, updated_at) VALUES (?, ?, ?, vector32(?), ?, ?, ?)",
            "params": [
                memory_id,
                self.agent_id,
                text,
                vector_data,
                meta_json,
                timestamp,
                timestamp
            ]
        }]
        
        results = self._turso_execute(statements)
        
        if results and "error" in results[0]:
            raise Exception(f"Turso storage error: {results[0]['error']}")
        
        return {
            "id": memory_id,
            "text": text,
            "created_at": self._format_timestamp(timestamp),
            "tokens_used": 0
        }
    
    def search(
        self,
        query: Optional[str] = None,
        limit: int = 10,
        mode: str = "vector"
    ) -> Dict[str, Any]:
        """
        Search memories
        
        Args:
            query: Search query (required for vector/hybrid modes)
            limit: Max results (1-100, default 10)
            mode: "vector" | "chronological" | "hybrid"
        
        Returns:
            {
                "results": [
                    {
                        "id": "mem_abc123",
                        "text": "...",
                        "similarity": 0.85,
                        "created_at": "2025-12-09T13:45:00Z",
                        "metadata": {...}
                    }
                ],
                "query_time_ms": 123,
                "namespace": "agent_fork-main",
                "mode": "vector"
            }
        """
        start_time = time.time()
        
        if mode not in ["vector", "chronological", "hybrid"]:
            raise ValueError("mode must be 'vector', 'chronological', or 'hybrid'")
        
        if mode == "chronological":
            # Chronological mode: recent memories without embedding
            statements = [{
                "q": "SELECT id, content, metadata, created_at FROM memories WHERE agent_id = ? ORDER BY created_at DESC LIMIT ?",
                "params": [self.agent_id, limit]
            }]
            
            results = self._turso_execute(statements)
            
            if results and "error" in results[0]:
                raise Exception(f"Turso search error: {results[0]['error']}")
            
            rows = results[0].get("results", {}).get("rows", [])
            
            formatted_results = []
            for row in rows:
                formatted_results.append({
                    "id": row[0],
                    "text": row[1],
                    "metadata": json.loads(row[2]) if row[2] else {},
                    "created_at": self._format_timestamp(row[3]),
                    "similarity": 1.0  # No similarity in chronological mode
                })
        
        else:
            # Vector or hybrid mode
            if not query:
                raise ValueError(f"query required for {mode} search")
            
            query_embedding = self._embed(query)
            vector_data = json.dumps(query_embedding)
            
            statements = [{
                "q": "SELECT id, content, metadata, created_at, vector_distance_cos(embedding, vector32(?)) as similarity FROM memories WHERE agent_id = ? ORDER BY similarity ASC LIMIT ?",
                "params": [vector_data, self.agent_id, limit]
            }]
            
            results = self._turso_execute(statements)
            
            if results and "error" in results[0]:
                raise Exception(f"Turso search error: {results[0]['error']}")
            
            rows = results[0].get("results", {}).get("rows", [])
            
            formatted_results = []
            for row in rows:
                # Convert distance to similarity (1 - distance for cosine)
                distance = row[4]
                similarity = 1.0 - distance
                
                formatted_results.append({
                    "id": row[0],
                    "text": row[1],
                    "metadata": json.loads(row[2]) if row[2] else {},
                    "created_at": self._format_timestamp(row[3]),
                    "similarity": similarity
                })
        
        query_time_ms = int((time.time() - start_time) * 1000)
        
        return {
            "results": formatted_results,
            "query_time_ms": query_time_ms,
            "namespace": f"agent_{self.agent_id}",
            "mode": mode
        }
    
    def get(self, memory_id: str) -> Dict[str, Any]:
        """
        Get a specific memory by ID
        
        Returns:
            {
                "memory": {
                    "id": "mem_abc123",
                    "text": "...",
                    "created_at": "2025-12-09T13:45:00Z",
                    "metadata": {...}
                }
            }
        """
        statements = [{
            "q": "SELECT id, content, metadata, created_at FROM memories WHERE id = ? AND agent_id = ?",
            "params": [memory_id, self.agent_id]
        }]
        
        results = self._turso_execute(statements)
        
        if results and "error" in results[0]:
            raise Exception(f"Turso get error: {results[0]['error']}")
        
        rows = results[0].get("results", {}).get("rows", [])
        
        if not rows:
            raise Exception(f"Memory not found: {memory_id}")
        
        row = rows[0]
        return {
            "memory": {
                "id": row[0],
                "text": row[1],
                "metadata": json.loads(row[2]) if row[2] else {},
                "created_at": self._format_timestamp(row[3])
            }
        }
    
    def delete(self, memory_id: str) -> None:
        """Delete a memory by ID"""
        statements = [{
            "q": "DELETE FROM memories WHERE id = ? AND agent_id = ?",
            "params": [memory_id, self.agent_id]
        }]
        
        results = self._turso_execute(statements)
        
        if results and "error" in results[0]:
            raise Exception(f"Turso delete error: {results[0]['error']}")
    
    def get_related(
        self,
        memory_id: str,
        min_similarity: float = 0.0
    ) -> Dict[str, Any]:
        """
        Find memories related to a specific memory
        
        Returns:
            {
                "results": [...],
                "query_time_ms": 123
            }
        """
        # First, get the memory to retrieve its embedding
        statements = [{
            "q": "SELECT embedding FROM memories WHERE id = ? AND agent_id = ?",
            "params": [memory_id, self.agent_id]
        }]
        
        results = self._turso_execute(statements)
        
        if results and "error" in results[0]:
            raise Exception(f"Turso get_related error: {results[0]['error']}")
        
        rows = results[0].get("results", {}).get("rows", [])
        if not rows:
            raise Exception(f"Memory not found: {memory_id}")
        
        # Note: We would need to extract the embedding from F32_BLOB
        # For now, use a simplified approach - search similar content
        # This is a limitation we'll need to address if get_related is critical
        raise NotImplementedError("get_related requires embedding extraction from F32_BLOB - not yet implemented")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get agent statistics
        
        Returns:
            {
                "agent_id": "fork-main",
                "namespace": "agent_fork-main",
                "memory_count": 42,
                "first_memory_at": "2025-12-09T13:45:00Z",
                "last_memory_at": "2025-12-09T13:50:00Z"
            }
        """
        statements = [{
            "q": "SELECT COUNT(*), MIN(created_at), MAX(created_at) FROM memories WHERE agent_id = ?",
            "params": [self.agent_id]
        }]
        
        results = self._turso_execute(statements)
        
        if results and "error" in results[0]:
            raise Exception(f"Turso stats error: {results[0]['error']}")
        
        rows = results[0].get("results", {}).get("rows", [])
        
        if not rows or not rows[0][0]:
            return {
                "agent_id": self.agent_id,
                "namespace": f"agent_{self.agent_id}",
                "memory_count": 0,
                "first_memory_at": None,
                "last_memory_at": None
            }
        
        count, first_ts, last_ts = rows[0]
        
        return {
            "agent_id": self.agent_id,
            "namespace": f"agent_{self.agent_id}",
            "memory_count": count,
            "first_memory_at": self._format_timestamp(first_ts) if first_ts else None,
            "last_memory_at": self._format_timestamp(last_ts) if last_ts else None
        }
    
    def health_check(self) -> Dict[str, Any]:
        """Check local services health status"""
        try:
            # Check Ollama
            ollama_req = Request(f"{self.ollama_url}/api/version")
            with urlopen(ollama_req, timeout=5) as response:
                ollama_health = response.status == 200
        except:
            ollama_health = False
        
        try:
            # Check Turso
            turso_results = self._turso_execute([{"q": "SELECT 1"}])
            turso_health = len(turso_results) > 0 and "error" not in turso_results[0]
        except:
            turso_health = False
        
        return {
            "status": "healthy" if (ollama_health and turso_health) else "degraded",
            "ollama": "up" if ollama_health else "down",
            "turso": "up" if turso_health else "down"
        }


def main():
    """CLI interface for testing"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: local_memory_client.py <command> [args...]")
        print("\nCommands:")
        print("  store <text> [metadata_json]")
        print("  search <query> [limit] [mode]")
        print("  get <memory_id>")
        print("  delete <memory_id>")
        print("  stats")
        print("  health")
        sys.exit(1)
    
    client = LocalMemoryClient()
    command = sys.argv[1]
    
    try:
        if command == "store":
            text = sys.argv[2]
            metadata = json.loads(sys.argv[3]) if len(sys.argv) > 3 else None
            result = client.store(text, metadata)
            print(json.dumps(result, indent=2))
        
        elif command == "search":
            query = sys.argv[2] if len(sys.argv) > 2 else None
            limit = int(sys.argv[3]) if len(sys.argv) > 3 else 10
            mode = sys.argv[4] if len(sys.argv) > 4 else "vector"
            result = client.search(query, limit, mode)
            print(json.dumps(result, indent=2))
        
        elif command == "get":
            memory_id = sys.argv[2]
            result = client.get(memory_id)
            print(json.dumps(result, indent=2))
        
        elif command == "delete":
            memory_id = sys.argv[2]
            client.delete(memory_id)
            print(f"Deleted {memory_id}")
        
        elif command == "stats":
            result = client.get_stats()
            print(json.dumps(result, indent=2))
        
        elif command == "health":
            result = client.health_check()
            print(json.dumps(result, indent=2))
        
        else:
            print(f"Unknown command: {command}")
            sys.exit(1)
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

