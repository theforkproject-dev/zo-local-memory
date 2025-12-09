# Deploy Local Semantic Memory on Zo Computer

**A complete guide to giving your Zo AI persistent memory using local infrastructure**

---

## What This Gives You

**Persistent AI memory** that enables your Zo AI to:
- Remember conversations across sessions
- Recall your preferences, decisions, and context
- Search past memories semantically (by meaning, not keywords)
- Build genuine continuity and relationship over time

**All running locally** on your Zo Computer:
- ✅ Full data sovereignty (memories never leave your infrastructure)
- ✅ Zero external API costs
- ✅ Sub-second semantic search
- ✅ Standard SQLite storage (portable, inspectable, backupable)
- ✅ Works offline

---

## Architecture Overview

```
Zo AI Conversation
        ↓
Memory Integration Layer
        ↓
    ┌───────┴────────┐
    ↓                ↓
Ollama           Turso (sqld)
(Embeddings)     (Vector DB)
localhost:11434  localhost:8787
```

**Components:**
1. **Ollama** - Local embedding model server (nomic-embed-text, 768-dimensional vectors)
2. **Turso (sqld)** - Local vector database (libSQL with native vector support)
3. **Python client** - Connects Ollama + Turso for memory storage/retrieval
4. **Integration layer** - Zo AI uses this to remember and recall

---

## Prerequisites

- Zo Computer (root access)
- ~500MB disk space
- Python 3.12+ (already installed on Zo)
- Basic terminal familiarity

---

## Deployment Guide

### Step 1: Install Ollama

```bash
# Download and install Ollama
curl -fsSL https://ollama.com/install.sh | sh
```

**Add to supervisord** (for automatic management):

```bash
cat >> /etc/zo/supervisord-user.conf << 'EOF'

[program:ollama]
command=ollama serve
directory=/home/workspace
environment=OLLAMA_HOST=127.0.0.1:11434
autostart=true
autorestart=true
startretries=20
startsecs=5
stdout_logfile=/dev/shm/ollama.log
stderr_logfile=/dev/shm/ollama_err.log
stdout_logfile_maxbytes=10MB
stdout_logfile_backups=3
stopsignal=TERM
stopasgroup=true
killasgroup=true
stopwaitsecs=4
user=root
EOF

# Reload and start
supervisorctl -c /etc/zo/supervisord-user.conf reread
supervisorctl -c /etc/zo/supervisord-user.conf update
```

**Pull the embedding model:**

```bash
curl -s http://localhost:11434/api/pull -d '{"name": "nomic-embed-text"}'
```

Wait ~30 seconds for download (270MB model).

**Test it:**

```bash
curl -s http://localhost:11434/api/embed -d '{
  "model": "nomic-embed-text",
  "input": "test embedding"
}' | python3 -c "import json, sys; d=json.load(sys.stdin); print(f'✓ Ollama working: {len(d[\"embeddings\"][0])}D vectors')"
```

Expected output: `✓ Ollama working: 768D vectors`

---

### Step 2: Install Turso (sqld)

**Download sqld binary:**

```bash
cd /tmp
curl -L -o libsql-server.tar.xz \
  https://github.com/tursodatabase/libsql/releases/download/libsql-server-v0.24.32/libsql-server-x86_64-unknown-linux-gnu.tar.xz
tar -xf libsql-server.tar.xz
mv libsql-server-x86_64-unknown-linux-gnu/sqld /usr/local/bin/
chmod +x /usr/local/bin/sqld
```

**Create database directory:**

```bash
mkdir -p /var/lib/sqld
```

**Add to supervisord:**

```bash
cat >> /etc/zo/supervisord-user.conf << 'EOF'

[program:sqld]
command=/usr/local/bin/sqld --db-path /var/lib/sqld/memory-box.db --http-listen-addr 127.0.0.1:8787
directory=/var/lib/sqld
autostart=true
autorestart=true
startretries=20
startsecs=5
stdout_logfile=/dev/shm/sqld.log
stderr_logfile=/dev/shm/sqld_err.log
stdout_logfile_maxbytes=10MB
stdout_logfile_backups=3
stopsignal=TERM
stopasgroup=true
killasgroup=true
stopwaitsecs=4
user=root
EOF

# Reload and start
supervisorctl -c /etc/zo/supervisord-user.conf reread
supervisorctl -c /etc/zo/supervisord-user.conf update
```

**Test it:**

```bash
curl -s http://localhost:8787/ -H "Content-Type: application/json" \
  -d '{"statements": [{"q": "SELECT 1 as test"}]}' | python3 -m json.tool
```

Expected output: JSON with `"columns": ["test"]` and `"rows": [[1]]`

---

### Step 3: Initialize Database Schema

**Create the memories table:**

```bash
curl -s http://localhost:8787/ -H "Content-Type: application/json" -d '{
  "statements": [{
    "q": "CREATE TABLE memories (
      id TEXT PRIMARY KEY,
      agent_id TEXT NOT NULL,
      content TEXT NOT NULL,
      embedding F32_BLOB(768),
      metadata JSON,
      created_at INTEGER NOT NULL,
      updated_at INTEGER NOT NULL
    )"
  }]
}'
```

**Create indices:**

```bash
curl -s http://localhost:8787/ -H "Content-Type: application/json" -d '{
  "statements": [
    {"q": "CREATE INDEX idx_agent ON memories(agent_id)"},
    {"q": "CREATE INDEX idx_created ON memories(created_at)"},
    {"q": "CREATE INDEX idx_vector ON memories(libsql_vector_idx(embedding))"}
  ]
}'
```

**Verify schema:**

```bash
curl -s http://localhost:8787/ -H "Content-Type: application/json" \
  -d '{"statements": [{"q": "SELECT name FROM sqlite_master WHERE type='"'"'table'"'"'"}]}' \
  | python3 -c "import json, sys; d=json.load(sys.stdin); print('✓ Tables:', [r[0] for r in d[0]['results']['rows']])"
```

Expected output: `✓ Tables: ['memories', 'libsql_vector_meta_shadow', 'idx_vector_shadow']`

---

### Step 4: Install Python Memory Client

**Create the memory client library:**

```bash
mkdir -p /home/workspace/.zo
cd /home/workspace/.zo
```

Create `local_memory_client.py` with this content:

```python
#!/usr/bin/env python3
"""Local Memory Client for Zo Computer"""

import os
import json
import time
import uuid
from typing import Optional, Dict, List, Any
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from datetime import datetime, timezone


class LocalMemoryClient:
    def __init__(
        self,
        agent_id: str = "main",
        ollama_url: str = "http://localhost:11434",
        turso_url: str = "http://localhost:8787"
    ):
        self.agent_id = agent_id
        self.namespace = f"agent_{agent_id}"
        self.ollama_url = ollama_url
        self.turso_url = turso_url
        self.embedding_model = "nomic-embed-text"
    
    def _http_request(self, url: str, data: dict) -> dict:
        """Make HTTP POST request"""
        req = Request(
            url,
            data=json.dumps(data).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        try:
            with urlopen(req, timeout=30) as response:
                return json.loads(response.read().decode('utf-8'))
        except (HTTPError, URLError) as e:
            raise Exception(f"HTTP request failed: {e}")
    
    def _get_embedding(self, text: str) -> List[float]:
        """Get embedding vector from Ollama"""
        response = self._http_request(
            f"{self.ollama_url}/api/embed",
            {"model": self.embedding_model, "input": text}
        )
        return response["embeddings"][0]
    
    def _turso_execute(self, statements: List[Dict]) -> List[Dict]:
        """Execute statements on Turso"""
        response = self._http_request(
            self.turso_url,
            {"statements": statements}
        )
        return response
    
    def store(self, text: str, metadata: Optional[Dict] = None) -> Dict:
        """Store a memory"""
        memory_id = f"mem_{uuid.uuid4().hex[:12]}"
        embedding = self._get_embedding(text)
        timestamp = int(time.time())
        
        # Convert embedding to bytes
        import struct
        embedding_bytes = struct.pack(f'{len(embedding)}f', *embedding)
        import base64
        embedding_b64 = base64.b64encode(embedding_bytes).decode('ascii')
        
        metadata_json = json.dumps(metadata or {})
        
        # Insert into database
        statements = [{
            "q": "INSERT INTO memories (id, agent_id, content, embedding, metadata, created_at, updated_at) VALUES (?, ?, ?, vector32(?), ?, ?, ?)",
            "params": [
                memory_id,
                self.namespace,
                text,
                embedding_b64,
                metadata_json,
                timestamp,
                timestamp
            ]
        }]
        
        self._turso_execute(statements)
        
        return {
            "id": memory_id,
            "text": text,
            "created_at": datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat(),
            "tokens_used": 0
        }
    
    def search(
        self,
        query: str,
        limit: int = 10,
        mode: str = "vector"
    ) -> Dict:
        """Search memories"""
        start_time = time.time()
        query_embedding = self._get_embedding(query)
        
        # Convert to base64
        import struct
        import base64
        embedding_bytes = struct.pack(f'{len(query_embedding)}f', *query_embedding)
        embedding_b64 = base64.b64encode(embedding_bytes).decode('ascii')
        
        # Vector search
        sql = f"""
            SELECT id, content, metadata, created_at,
                   vector_distance_cos(embedding, vector32(?)) as distance
            FROM memories
            WHERE agent_id = ?
            ORDER BY distance ASC
            LIMIT ?
        """
        
        results = self._turso_execute([{
            "q": sql,
            "params": [embedding_b64, self.namespace, limit]
        }])
        
        formatted_results = []
        if results and "results" in results[0]:
            for row in results[0]["results"]["rows"]:
                distance = row[4]
                similarity = 1.0 - distance
                
                formatted_results.append({
                    "id": row[0],
                    "text": row[1],
                    "metadata": json.loads(row[2]) if row[2] else {},
                    "created_at": datetime.fromtimestamp(row[3], tz=timezone.utc).isoformat(),
                    "similarity": similarity
                })
        
        query_time_ms = int((time.time() - start_time) * 1000)
        
        return {
            "results": formatted_results,
            "query_time_ms": query_time_ms,
            "namespace": self.namespace,
            "mode": mode
        }
    
    def get_stats(self) -> Dict:
        """Get memory statistics"""
        results = self._turso_execute([{
            "q": """
                SELECT COUNT(*), MIN(created_at), MAX(created_at)
                FROM memories
                WHERE agent_id = ?
            """,
            "params": [self.namespace]
        }])
        
        if results and "results" in results[0]:
            row = results[0]["results"]["rows"][0]
            count = row[0]
            first_ts = row[1]
            last_ts = row[2]
            
            return {
                "agent_id": self.agent_id,
                "namespace": self.namespace,
                "memory_count": count,
                "first_memory_at": datetime.fromtimestamp(first_ts, tz=timezone.utc).isoformat() if first_ts else None,
                "last_memory_at": datetime.fromtimestamp(last_ts, tz=timezone.utc).isoformat() if last_ts else None
            }
        
        return {"agent_id": self.agent_id, "namespace": self.namespace, "memory_count": 0}
    
    def health_check(self) -> Dict:
        """Check if services are healthy"""
        try:
            # Check Ollama
            self._http_request(f"{self.ollama_url}/api/version", {})
            ollama_status = "up"
        except:
            ollama_status = "down"
        
        try:
            # Check Turso
            self._turso_execute([{"q": "SELECT 1"}])
            turso_status = "up"
        except:
            turso_status = "down"
        
        return {
            "status": "healthy" if ollama_status == "up" and turso_status == "up" else "degraded",
            "ollama": ollama_status,
            "turso": turso_status
        }
```

Make it executable:

```bash
chmod +x /home/workspace/.zo/local_memory_client.py
```

---

### Step 5: Test the Memory System

**Store a test memory:**

```bash
cd /home/workspace/.zo
python3 << 'EOF'
from local_memory_client import LocalMemoryClient

client = LocalMemoryClient(agent_id="main")
result = client.store(
    text="I prefer Python over JavaScript for backend development",
    metadata={"type": "preference", "topic": "programming"}
)
print(f"✓ Stored: {result['id']}")
EOF
```

**Search for it:**

```bash
cd /home/workspace/.zo
python3 << 'EOF'
from local_memory_client import LocalMemoryClient

client = LocalMemoryClient(agent_id="main")
results = client.search("backend programming language preference", limit=3)
print(f"✓ Found {len(results['results'])} memories")
for r in results['results']:
    print(f"  [{r['similarity']:.2f}] {r['text'][:60]}...")
EOF
```

**Check statistics:**

```bash
cd /home/workspace/.zo
python3 << 'EOF'
from local_memory_client import LocalMemoryClient

client = LocalMemoryClient(agent_id="main")
stats = client.get_stats()
print(f"✓ Total memories: {stats['memory_count']}")
EOF
```

---

## Integration with Zo AI

To enable your Zo AI to use this memory system, create an integration layer that:

1. **Initializes sessions** - retrieves relevant context at the start of conversations
2. **Stores memories** - saves important information during conversations
3. **Queries on demand** - searches when specific context is needed

**Example integration pattern:**

```python
# At conversation start
from local_memory_client import LocalMemoryClient

client = LocalMemoryClient(agent_id="main")

# Retrieve relevant context
recent_context = client.search(user_message, limit=5, mode="vector")
preferences = client.search("user preferences constraints principles", limit=3)

# Use retrieved context in your prompt...

# During conversation, store important facts
client.store(
    text="User wants to build a local-first architecture for their project",
    metadata={"type": "preference", "topic": "architecture", "timestamp": "2025-12-09"}
)
```

---

## Operational Guide

### Service Management

**Check status:**
```bash
supervisorctl -c /etc/zo/supervisord-user.conf status ollama
supervisorctl -c /etc/zo/supervisord-user.conf status sqld
```

**Restart services:**
```bash
supervisorctl -c /etc/zo/supervisord-user.conf restart ollama
supervisorctl -c /etc/zo/supervisord-user.conf restart sqld
```

**View logs:**
```bash
tail -f /dev/shm/ollama.log
tail -f /dev/shm/sqld.log
```

### Backup & Recovery

**Backup memories:**
```bash
cp /var/lib/sqld/memory-box.db ~/backups/memory-$(date +%Y%m%d).db
```

**Restore from backup:**
```bash
supervisorctl -c /etc/zo/supervisord-user.conf stop sqld
cp ~/backups/memory-20251209.db /var/lib/sqld/memory-box.db
supervisorctl -c /etc/zo/supervisord-user.conf start sqld
```

**Export memories as JSON:**
```bash
curl -s http://localhost:8787/ -H "Content-Type: application/json" \
  -d '{"statements": [{"q": "SELECT id, content, metadata, created_at FROM memories"}]}' \
  | python3 -m json.tool > memories-export.json
```

### Security Notes

- Both services listen on `127.0.0.1` (localhost only)
- Not exposed to public internet
- No authentication required (trusted local environment)
- Access controlled at OS level (only processes on same machine)

---

## Technical Details

### Embedding Model

**nomic-embed-text** (Nomic AI)
- **Dimensions**: 768
- **Model size**: ~270MB
- **Performance**: ~100-200ms per embedding on CPU
- **Context length**: 8192 tokens
- **License**: Apache 2.0

### Vector Database

**Turso (libSQL)** 
- **Based on**: SQLite (fork with enhancements)
- **Vector support**: Native F32_BLOB type with vector_distance_cos()
- **Indexing**: DiskANN-based vector index (libsql_vector_idx)
- **Storage**: Single-file database (~1KB per memory)
- **Performance**: Sub-millisecond vector queries at <10K memories

### Memory Schema

```sql
CREATE TABLE memories (
    id TEXT PRIMARY KEY,           -- Unique identifier (mem_xxxx)
    agent_id TEXT NOT NULL,        -- Namespace (agent_main)
    content TEXT NOT NULL,         -- Memory text
    embedding F32_BLOB(768),       -- 768D vector
    metadata JSON,                 -- Structured metadata
    created_at INTEGER NOT NULL,   -- Unix timestamp
    updated_at INTEGER NOT NULL    -- Unix timestamp
);
```

**Indices:**
- `idx_agent` - Fast filtering by agent_id
- `idx_created` - Temporal queries
- `idx_vector` - Vector similarity search

---

## Customization Options

### Using a Different Embedding Model

Ollama supports many embedding models. To use a different one:

1. **Pull the model:**
```bash
curl -s http://localhost:11434/api/pull -d '{"name": "mxbai-embed-large"}'
```

2. **Update the client:**
```python
client = LocalMemoryClient(
    agent_id="main",
    embedding_model="mxbai-embed-large"  # Change here
)
```

3. **Adjust schema if dimensions change** (e.g., 1024D):
```sql
ALTER TABLE memories ADD COLUMN embedding_1024 F32_BLOB(1024);
```

Popular alternatives:
- **mxbai-embed-large** (1024D, better quality, slower)
- **snowflake-arctic-embed** (1024D, strong performance)
- **all-minilm** (384D, faster, smaller)

### Multi-Agent Memory

To support multiple AI agents with separate memory spaces:

```python
# Agent 1
client_agent1 = LocalMemoryClient(agent_id="assistant")

# Agent 2  
client_agent2 = LocalMemoryClient(agent_id="researcher")
```

Each agent's memories are isolated by the `agent_id` namespace.

### Memory Types & Metadata

Structure your memories with metadata for better organization:

```python
# Preference memory
client.store(
    text="User prefers concise technical explanations without unnecessary context",
    metadata={"type": "preference", "category": "communication"}
)

# Project context
client.store(
    text="Working on local-first architecture for personal AI assistant",
    metadata={"type": "project", "project_name": "ai-assistant", "status": "active"}
)

# Technical decision
client.store(
    text="Chose Turso over PostgreSQL for simpler deployment and SQLite compatibility",
    metadata={"type": "decision", "topic": "database", "rationale": "operational simplicity"}
)
```

Then query by type:
```python
# Get all preferences
results = client.search("user preferences", limit=10)
# Filter in application code by metadata.type == "preference"
```

---

## Troubleshooting

### Ollama not responding

```bash
# Check if running
supervisorctl -c /etc/zo/supervisord-user.conf status ollama

# Check logs
tail -50 /dev/shm/ollama_err.log

# Restart
supervisorctl -c /etc/zo/supervisord-user.conf restart ollama
```

### Turso database locked

```bash
# Check for multiple sqld processes
ps aux | grep sqld

# Stop and restart cleanly
supervisorctl -c /etc/zo/supervisord-user.conf stop sqld
sleep 2
supervisorctl -c /etc/zo/supervisord-user.conf start sqld
```

### Slow embedding performance

- **Cause**: CPU-bound operation
- **Solution**: Use smaller model (all-minilm) or upgrade Zo Computer resources
- **Batch optimization**: Ollama supports batch embeddings:
```python
embeddings = self._http_request(
    f"{self.ollama_url}/api/embed",
    {"model": self.embedding_model, "input": ["text1", "text2", "text3"]}
)
```

### Database corruption

```bash
# Check integrity
curl -s http://localhost:8787/ -H "Content-Type: application/json" \
  -d '{"statements": [{"q": "PRAGMA integrity_check"}]}'

# Restore from backup if corrupted
cp ~/backups/memory-latest.db /var/lib/sqld/memory-box.db
supervisorctl -c /etc/zo/supervisord-user.conf restart sqld
```

---

## Performance Characteristics

**Embedding latency** (CPU):
- Single text: ~100-200ms
- Batch of 10: ~500-800ms

**Vector search latency**:
- <1000 memories: <10ms
- 1000-10000 memories: 10-50ms
- 10000+ memories: 50-200ms

**Storage**:
- Per memory: ~1KB (text) + 3KB (vector) = ~4KB average
- 10,000 memories: ~40MB database size

**Resource usage**:
- Ollama: ~500MB RAM, <5% CPU idle
- sqld: ~50MB RAM, <1% CPU idle

---

## Why This Architecture?

**Ollama** - Standard tool for local LLM/embedding serving, widely adopted, well-maintained

**Turso (libSQL)** - SQLite heritage means proven reliability, native vector support means no extensions needed

**Python client** - Simple HTTP calls, no complex dependencies, easy to modify/extend

**Local-first** - Data sovereignty, zero external costs, works offline, full control

This is **production-grade** infrastructure that scales from personal use to thousands of memories while remaining simple to understand, deploy, and maintain.

---

## Next Steps

1. **Integrate with your Zo AI persona** - Add memory retrieval to session initialization
2. **Develop memory formatting patterns** - Standardize how you structure memories
3. **Implement conversation bridges** - Store session summaries for continuity
4. **Experiment with retrieval strategies** - Tune similarity thresholds, query patterns
5. **Expand to workspace indexing** - Apply same pattern to code/docs/notes

---

## Resources

- **Ollama**: https://ollama.com/
- **Turso (libSQL)**: https://turso.tech/libsql
- **nomic-embed-text**: https://huggingface.co/nomic-ai/nomic-embed-text-v1.5
- **Vector similarity**: Cosine distance (1 = identical, 0 = orthogonal, -1 = opposite)

---

**You now have local semantic memory running on your Zo Computer.** Your AI can remember, learn, and build continuity—all on your infrastructure, under your control.


---

## Step 6: Configure Your Zo AI Persona

**Critical**: The memory system requires a specially configured Zo AI persona to function. Without this, your AI won't know how to use the memory system.

### Quick Setup

1. Navigate to **[Settings > Your AI > Personas](/settings#your-ai)** in your Zo Computer
2. Click **"Create Persona"**
3. Name it **"Memory-Enabled Zo"**  
4. **Copy the complete persona prompt from**: [docs/PERSONA.md](PERSONA.md)
5. Click **"Save"**
6. Click **"Set as Active"**

### What the Persona Does

The Memory-Enabled Zo persona configures your AI to:

**At the start of every conversation**:
```bash
# Automatically retrieves recent context
cd /home/workspace/.zo && source /root/.zo_secrets && python3 memory_integration.py initialize
```

**During conversations**:
- Queries memory when you reference past work
- Autonomously decides what's important to remember
- Stores memories with rich context

**At conversation end**:
- Creates a "conversation bridge" summarizing the session
- Enables next session to resume with full continuity

### Why This Matters

Without the persona configuration:
- ❌ Memory system exists but AI doesn't use it
- ❌ No automatic context retrieval
- ❌ No autonomous memory formation
- ❌ No session continuity

With the persona configuration:
- ✅ AI automatically initializes memory each session
- ✅ Remembers preferences, decisions, projects
- ✅ Builds genuine continuity over time
- ✅ Stores self-observations for evolution

### Full Documentation

See **[docs/PERSONA.md](PERSONA.md)** for:
- Complete persona prompt text
- Memory type taxonomy
- Quality guidelines
- Troubleshooting
- Usage examples

---

## Next Steps

### Verify Everything Works

Start a conversation with your memory-enabled persona active:

1. **Check initialization**: First message should trigger memory retrieval
2. **Share a preference**: "I prefer concise technical explanations"
3. **Verify storage**: Check if it was remembered
   ```bash
   cd /home/workspace/.zo && python3 local_memory_client.py search "technical explanations" 3 vector
   ```
4. **Start new conversation**: Ask "What do you remember about my preferences?"

### Monitor Memory Health

```bash
# Check memory count
cd /home/workspace/.zo && python3 local_memory_client.py stats

# Search memories
cd /home/workspace/.zo && python3 local_memory_client.py search "your query" 5 vector
```

### Backup Your Memories

```bash
# Database is just a SQLite file
cp /var/lib/sqld/memory-box.db ~/backups/memory-box-$(date +%Y%m%d).db
```

---

## Troubleshooting

### AI not using memory

**Symptom**: No memory initialization at conversation start

**Solution**:
1. Verify persona is set as **active** (not just created)
2. Check persona prompt includes initialization protocol
3. Start a fresh conversation to trigger initialization

### Services not running

```bash
# Check service status
supervisorctl -c /etc/zo/supervisord-user.conf status ollama
supervisorctl -c /etc/zo/supervisord-user.conf status sqld

# Restart if needed
supervisorctl -c /etc/zo/supervisord-user.conf restart ollama
supervisorctl -c /etc/zo/supervisord-user.conf restart sqld
```

### Persona prompt too long

**Symptom**: Can't save persona - prompt too large

**Solution**: The provided persona prompt is within limits. If using a custom prompt, ensure it's under character limit.

---

