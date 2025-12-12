# Troubleshooting Guide

## Common Issues

### Memory Storage Works But Search Finds Nothing

**Symptoms:**
- `client.store()` returns success
- `client.search()` returns empty results
- Your Zo AI doesn't remember previous conversations

**Root Cause:** Agent ID namespace mismatch

The memory system uses `agent_id` to isolate memories between different AI agents. If you store memories with one `agent_id` but search with a different one, you'll see empty results.

**Diagnosis:**
```bash
cd /home/workspace/.zo && python3 << 'EOF'
import requests

# Check which agent_ids exist in database
response = requests.post(
    "http://localhost:8787/",
    headers={"Content-Type": "application/json"},
    json={"statements": [{"q": "SELECT DISTINCT agent_id, COUNT(*) as count FROM memories GROUP BY agent_id"}]}
)
data = response.json()
if data and len(data) > 0 and 'results' in data[0]:
    print("Agent ID Namespaces:")
    print("=" * 50)
    for row in data[0]['results']['rows']:
        print(f"  {row[0]}: {row[1]} memories")
else:
    print("No memories found or database error")
EOF
```

**Solution:**

Set your agent_id consistently across all components:

```bash
# Add to ~/.bashrc
export MEMORY_BOX_AGENT_ID="fork-main"

# Reload shell
source ~/.bashrc
```

Verify it's working:
```bash
cd /home/workspace/.zo && python3 << 'EOF'
from local_memory_client import LocalMemoryClient
client = LocalMemoryClient()
print(f"Using agent_id: {client.agent_id}")

# Store a test memory
result = client.store("Test memory", {"type": "test"})
print(f"Stored: {result['id']}")

# Search for it immediately
results = client.search("test memory", limit=1)
print(f"Found: {len(results['results'])} memories")
EOF
```

### KeyError When Testing Turso

**Symptoms:**
```bash
curl -s http://localhost:8787/ ... | python3 -c "..."
# KeyError: 'results'
```

**Root Causes:**

1. **Turso service not running**
2. **Database not initialized**
3. **Shell JSON escaping issues**

**Diagnosis:**

```bash
# 1. Check if sqld is running
ps aux | grep sqld | grep -v grep

# 2. Check Turso directly (simpler test)
curl -s http://localhost:8787/ \
  -H "Content-Type: application/json" \
  -d '{"statements":[{"q":"SELECT 1"}]}' \
  | python3 -c "import json, sys; print(json.dumps(json.load(sys.stdin), indent=2))"

# 3. Check logs
tail -50 /dev/shm/sqld_err.log
```

**Solutions:**

If sqld not running:
```bash
# Start it via supervisord
sudo supervisorctl -c /etc/zo/supervisord-user.conf start sqld

# Check status
sudo supervisorctl -c /etc/zo/supervisord-user.conf status sqld
```

If database not initialized:
```bash
# Re-run schema initialization
curl -s http://localhost:8787/ -H "Content-Type: application/json" -d '{
  "statements": [{
    "q": "CREATE TABLE IF NOT EXISTS memories (
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

### Ollama Embedding Errors

**Symptoms:**
```
Ollama embedding error: [Errno 111] Connection refused
```

**Diagnosis:**
```bash
# Check if Ollama is running
ps aux | grep ollama | grep -v grep

# Test Ollama directly
curl -s http://localhost:11434/api/tags | python3 -m json.tool

# Check logs
tail -50 /dev/shm/ollama_err.log
```

**Solution:**
```bash
# Start Ollama via supervisord
sudo supervisorctl -c /etc/zo/supervisord-user.conf start ollama

# Check status
sudo supervisorctl -c /etc/zo/supervisord-user.conf status ollama

# Verify model is downloaded
curl -s http://localhost:11434/api/tags | grep nomic-embed-text
```

If model missing:
```bash
curl -s http://localhost:11434/api/pull -d '{"name": "nomic-embed-text"}'
```

### Zo AI Not Using Memory

**Symptoms:**
- Memory system works in manual tests
- But Zo AI doesn't remember conversations
- Or reports "no memories found"

**Root Cause:** Persona not configured or not active

**Solution:**

1. **Check if persona is active:**
   - Go to Settings > Your AI > Personas
   - Look for "Memory-Enabled Zo" persona
   - Ensure it's marked as "Active"

2. **If persona doesn't exist, create it:**
   ```
   Say to Zo: "Please set up the Memory-Enabled Zo persona for me"
   ```

3. **Verify persona has initialization protocol:**
   - The persona should include:
   ```
   At the START of EVERY new conversation, IMMEDIATELY run:
   cd /home/workspace/.zo && python3 memory_integration.py initialize
   ```

4. **Test it:**
   - Start a new conversation
   - Check if Zo runs the initialization automatically
   - Try: "What's my agent_id?"

### Services Keep Crashing

**Diagnosis:**
```bash
# Check supervisord logs
sudo supervisorctl -c /etc/zo/supervisord-user.conf status

# Check service logs
tail -100 /dev/shm/ollama_err.log
tail -100 /dev/shm/sqld_err.log

# Check system resources
df -h  # Disk space
free -h  # Memory
```

**Common Causes:**

1. **Out of disk space** - Ollama models need ~500MB
2. **Port conflicts** - Another service using 11434 or 8787
3. **Permission issues** - Database file not writable

**Solutions:**

Check ports:
```bash
netstat -tlnp | grep -E '(11434|8787)'
```

Check permissions:
```bash
ls -la /var/lib/sqld/
chmod 755 /var/lib/sqld
```

Clear space if needed:
```bash
du -sh /home/workspace/*  # Find large directories
```

## Getting Help

If none of these solutions work:

1. **Collect diagnostic info:**
```bash
cd /home/workspace/.zo && python3 << 'EOF'
from local_memory_client import LocalMemoryClient
import sys

client = LocalMemoryClient()
print(f"Agent ID: {client.agent_id}")
print(f"Ollama URL: {client.ollama_url}")
print(f"Turso URL: {client.turso_url}")

try:
    health = client.health_check()
    print(f"Health: {health}")
except Exception as e:
    print(f"Health check failed: {e}")

try:
    stats = client.get_stats()
    print(f"Stats: {stats}")
except Exception as e:
    print(f"Stats failed: {e}")
EOF
```

2. **Check service status:**
```bash
sudo supervisorctl -c /etc/zo/supervisord-user.conf status
```

3. **Share on Discord:**
   - Join: https://discord.gg/invite/zocomputer
   - Include: diagnostic output, error messages, service status

4. **Open GitHub issue:**
   - https://github.com/theforkproject-dev/zo-local-memory/issues
   - Include: same diagnostic info as above

