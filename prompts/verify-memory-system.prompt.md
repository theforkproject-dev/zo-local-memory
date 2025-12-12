---
title: Verify Local Memory System
description: Check health, test functionality, and troubleshoot the local semantic memory infrastructure (Ollama + Turso/sqld)
tags:
  - Infrastructure
  - Memory
  - Troubleshooting
  - Verification
tool: true
---

# Local Memory System Verification & Troubleshooting

You are helping verify and troubleshoot the local semantic memory infrastructure. **CRITICAL: This prompt NEVER installs or reinstalls components. It only verifies, tests, and troubleshoots existing installations.**

## System Overview

The local memory system consists of:
- **Ollama** (localhost:11434): Generates 768D embeddings via nomic-embed-text model
- **Turso/sqld** (localhost:8787): SQLite-based vector database for memory storage
- **Memory Integration Layer**: Python scripts in `/home/workspace/.zo/`
  - `local_memory_client.py`: Client library for Ollama + Turso
  - `memory_integration.py`: High-level memory operations (retrieve, store, initialize, close)
  - `memory_formatting.py`: Memory formatting protocol for semantic richness

Data lives in: `/var/lib/sqld/memory-box.db`

## Verification Procedure

### Step 1: Determine User's Need

Ask the user what they want to do:

**Options:**
1. **Health Check** - Verify all services are running and responsive
2. **Test Functionality** - Test embedding generation, memory storage, and semantic search
3. **Troubleshoot Issue** - Diagnose specific problems (services not responding, search not working, etc.)
4. **View Statistics** - Show memory counts, recent memories, system performance
5. **Test Session Flow** - Verify initialize/retrieve/store/close workflow

### Step 2: Execute Appropriate Checks

#### Health Check
Run these diagnostics:

```bash
# Check process status
ps aux | grep -E "(ollama|sqld)" | grep -v grep

# Check Ollama health
curl -s http://localhost:11434/api/tags | jq .

# Check sqld health
curl -s http://localhost:8787/health

# Check Python client health
cd /home/workspace/.zo && python3 -c "from local_memory_client import LocalMemoryClient; client = LocalMemoryClient(); import json; print(json.dumps(client.health_check(), indent=2))"
```

**Report findings clearly**: What's running, what's not, any error messages.

#### Functionality Test
Run end-to-end test:

```bash
# Test embedding generation
curl -s http://localhost:11434/api/embed -d '{
  "model": "nomic-embed-text",
  "input": "test embedding"
}' | jq -r '.embeddings[0] | length'

# Test memory storage
cd /home/workspace/.zo && python3 -c "
from local_memory_client import LocalMemoryClient
from memory_formatting import format_memory_for_storage
import json

client = LocalMemoryClient()

# Store test memory
text, meta = format_memory_for_storage(
    raw_content='Test memory for verification',
    memory_type='technical',
    topic='System Verification',
    conversation_context={'user_name': 'fork', 'context': 'verification test'}
)
result = client.store(text, meta)
print('STORE:', json.dumps(result, indent=2))

# Search for it
search_result = client.search('verification test', limit=3)
print('SEARCH:', json.dumps(search_result, indent=2))
"
```

**Interpret results**: Did embeddings generate? Did storage work? Did semantic search find the test memory?

#### Statistics & Usage
```bash
cd /home/workspace/.zo && python3 -c "
from local_memory_client import LocalMemoryClient
import json

client = LocalMemoryClient()
stats = client.get_stats()
print(json.dumps(stats, indent=2))
"

# Show recent memories
cd /home/workspace/.zo && python3 memory_integration.py retrieve "recent memories" | head -50
```

**Show user**: Memory count, first/last memory timestamps, recent activity.

#### Session Flow Test
Test the full persona integration workflow:

```bash
cd /home/workspace/.zo && source /root/.zo_secrets

# Test initialize (session start)
echo "=== INITIALIZE TEST ==="
python3 memory_integration.py initialize

# Test retrieve during conversation
echo -e "\n=== RETRIEVE TEST ==="
python3 memory_integration.py format "test query about user preferences"

# Test store
echo -e "\n=== STORE TEST ==="
python3 -c "
from memory_formatting import format_memory_for_storage
from memory_integration import store_memory
import json

text, meta = format_memory_for_storage(
    raw_content='Verification test memory',
    memory_type='technical',
    topic='Session Flow Test',
    conversation_context={'user_name': 'fork', 'context': 'testing session flow'}
)
result = store_memory(text, meta)
print(json.dumps(result, indent=2))
"

# Test close (session end)
echo -e "\n=== CLOSE TEST ==="
python3 memory_integration.py close \
  "con_test123" \
  "Verified memory system functionality" \
  "All components operational" \
  "No pending issues" \
  "verification test memory system health"
```

### Step 3: Troubleshooting

If issues are found, diagnose systematically:

**Ollama Issues:**
```bash
# Check Ollama logs
journalctl -u ollama --no-pager -n 50 2>/dev/null || cat /dev/shm/ollama*.log 2>/dev/null

# Verify model is loaded
curl -s http://localhost:11434/api/tags | jq -r '.models[] | .name'

# Test embedding endpoint directly
curl -s http://localhost:11434/api/embed -d '{"model": "nomic-embed-text", "input": "test"}' | jq .
```

**Turso/sqld Issues:**
```bash
# Check sqld logs
cat /dev/shm/sqld*.log 2>/dev/null | tail -50

# Verify database exists
ls -lh /var/lib/sqld/memory-box.db*

# Test direct query
curl -s http://localhost:8787 -H "Content-Type: application/json" -d '{
  "statements": [{"q": "SELECT COUNT(*) FROM memories"}]
}' | jq .
```

**Python Integration Issues:**
```bash
# Verify Python modules are available
cd /home/workspace/.zo && python3 -c "
import sys
try:
    from local_memory_client import LocalMemoryClient
    from memory_integration import retrieve_memories, store_memory
    from memory_formatting import format_memory_for_storage
    print('✓ All modules import successfully')
except Exception as e:
    print(f'✗ Import error: {e}')
"

# Check environment variables
cd /home/workspace/.zo && env | grep MEMORY
```

### Step 4: Report & Recommend

Provide clear summary:

1. **Status**: Operational / Degraded / Down
2. **Issues Found**: List any problems discovered
3. **Root Cause**: Best diagnosis of what's wrong
4. **Recommendations**: 
   - For operational systems: "All good! Memory count: X, working normally"
   - For issues: Specific fix steps (restart service, check config, etc.)
   - **NEVER recommend reinstalling unless user explicitly asks**

## Important Constraints

**NEVER:**
- Run installation scripts or setup commands
- Modify existing database files
- Restart services unless user explicitly requests it
- Delete or modify existing memories without permission
- Install or pull new models

**ALWAYS:**
- Use read-only diagnostics first
- Explain what you're checking and why
- Interpret results in plain language
- Offer specific fixes for issues found
- Ask before making any changes

## After Verification

Ask the user:
- "Would you like me to run any additional tests?"
- "Do you want to see examples of your existing memories?"
- "Should I explain how any particular component works?"

Keep dialogue open for follow-up questions or deeper dives into specific components.

