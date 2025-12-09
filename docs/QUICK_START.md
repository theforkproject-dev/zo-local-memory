# Quick Start Guide

Get persistent AI memory running in 15 minutes.

## Prerequisites

- Zo Computer with root access
- ~500MB free disk space

## Installation (5 minutes)

```bash
curl -sSL https://raw.githubusercontent.com/theforkproject-dev/zo-local-memory/main/install.sh | bash
```

This installs:
- Ollama (embedding service)
- Turso/sqld (vector database)
- Python memory client libraries

## Persona Setup (5 minutes)

**Critical**: Your AI needs a special persona configuration to use memory.

1. Go to **[Settings > Your AI > Personas](/settings#your-ai)**
2. Click **"Create Persona"**
3. Name: **"Memory-Enabled Zo"**
4. Copy the complete persona prompt from [PERSONA.md](PERSONA.md)
5. Save and **"Set as Active"**

## Test It (5 minutes)

### 1. Start a Conversation

With your Memory-Enabled Zo persona active, start chatting. The AI should automatically initialize memory at the start.

### 2. Share a Preference

```
You: "I prefer concise technical explanations without verbose context."
```

The AI will autonomously store this as a memory.

### 3. Verify Storage

```bash
cd /home/workspace/.zo
python3 local_memory_client.py search "technical explanations" 3 vector
```

You should see your preference stored.

### 4. Test Recall

Start a **new conversation** and ask:

```
You: "What do you remember about my communication preferences?"
```

The AI should recall and reference your stored preference.

## What You Now Have

✅ **Persistent memory** - AI remembers across sessions  
✅ **Semantic search** - Find memories by meaning, not exact words  
✅ **Full data sovereignty** - Everything runs locally  
✅ **Zero API costs** - No external dependencies  
✅ **Session continuity** - Conversations build on each other  

## Next Steps

- **Full deployment guide**: [DEPLOY.md](DEPLOY.md)
- **Persona configuration details**: [PERSONA.md](PERSONA.md)
- **Architecture deep-dive**: [ARCHITECTURE.md](ARCHITECTURE.md)
- **Tools hub**: https://tools-hub-fork.zocomputer.io/local-memory

## Common Issues

### AI not initializing memory

**Solution**: Verify persona is **active** (not just created). Look for "Set as Active" button in persona settings.

### "Command not found" errors during install

**Solution**: Ensure you're running on a Zo Computer. The installer checks for `/etc/zo/supervisord-user.conf`.

### Services won't start

**Solution**:
```bash
supervisorctl -c /etc/zo/supervisord-user.conf status ollama
supervisorctl -c /etc/zo/supervisord-user.conf status sqld
tail /dev/shm/ollama_err.log
tail /dev/shm/sqld_err.log
```

---

**Having trouble?** Open an issue on [GitHub](https://github.com/theforkproject-dev/zo-local-memory/issues)
