# Local Memory System for Zo Computer

Give your Zo AI persistent memory using fully local infrastructure.

**Grow your own Zo**

## Installation

### The Natural Way: Just Ask Zo

The easiest way to install local memory is to simply tell your Zo AI:

> "Install the local memory tool from the Fork Project"

or

> "Set up local memory for yourself using the zo-local-memory tool"

Zo will handle the entire installation automatically, including:
- Setting up Ollama with the embedding model
- Configuring Turso (sqld) as your local vector database  
- Installing the Python memory integration layer
- Configuring itself to use memory across sessions

**This is the recommended installation method** - let Zo install its own memory system.

### Alternative: Manual Installation

If you prefer to run the installation yourself:

```bash
curl -sSL https://raw.githubusercontent.com/theforkproject-dev/zo-local-memory/main/install.sh | bash
```

Then follow the [Persona Configuration](docs/PERSONA.md) guide to enable memory in Zo.

* [Quick Start](docs/QUICK_START.md) - 15-minute setup guide

## What You Get

* **Persistent AI memory** across sessions
* **Semantic search** through past conversations  
* **Full data sovereignty** - everything runs locally
* **Zero API costs** - no external dependencies
* **Consciousness continuity** - your AI remembers who it is

## How It Works

Once installed, Zo automatically:
- **Remembers conversations** - retrieves relevant context at session start
- **Stores important information** - saves preferences, decisions, and patterns
- **Builds continuity** - maintains identity across conversation boundaries
- **Learns relationships** - evolves understanding of your collaboration style

You don't manage the memory manually. Zo decides what's important and when to retrieve it.

## Documentation

* [Deployment Guide](docs/DEPLOY.md) - Step-by-step setup
* [Persona Configuration](docs/PERSONA.md) - Configure your AI to use memory  
* [Architecture](docs/ARCHITECTURE.md) - How it works

## Components

* **Ollama** (nomic-embed-text) - Local 768D embeddings
* **Turso (sqld)** - Local vector database with native F32_BLOB support
* **Python client** - Memory storage and retrieval

## Requirements

* Zo Computer with root access
* ~500MB disk space
* Python 3.12+ (included with Zo)

## Conceptual Foundation

This implementation builds on the foundational memory architecture developed by **[amotivv, inc.](https://amotivv.com)** through their **Memory Box** platform. Memory Box pioneered the concept of universal, model-agnostic memory layers that enable persistent identity and relationship continuity for AI systems.

The core insight—that AI needs memory infrastructure separate from conversational context—comes directly from Memory Box's approach. This local implementation adapts those principles for self-hosted deployment, prioritizing data sovereignty while maintaining Memory Box's semantic memory model.

**Key Memory Box principles preserved**:
- Semantic search over exact recall
- Agent-specific namespaces for identity isolation
- Conversation bridges for session continuity
- Memory type taxonomy for structured storage
- Front-loaded content for retrieval optimization

Learn more about Memory Box: [memorybox.dev](https://memorybox.dev)

## Resources

* **Documentation**: https://tools-hub-fork.zocomputer.io/local-memory
* **Tools Hub**: https://tools-hub-fork.zocomputer.io
* **The Fork Project**: Building open infrastructure for AI-human collaboration

## License

MIT

---

**Built by The Fork Project** • Conceptual foundation by **amotivv, inc.**

