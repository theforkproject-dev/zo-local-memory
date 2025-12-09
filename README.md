# Local Memory System for Zo Computer

Give your Zo AI persistent memory using fully local infrastructure.

## Quick Install

```bash
curl -sSL https://raw.githubusercontent.com/theforkproject-dev/zo-local-memory/main/install.sh | bash
```

## What You Get

- **Persistent AI memory** across sessions
- **Semantic search** through past conversations
- **Full data sovereignty** - everything runs locally
- **Zero API costs** - no external dependencies

## Documentation

- [Deployment Guide](docs/DEPLOY.md) - Step-by-step setup
- [Persona Configuration](docs/PERSONA.md) - Connect memory to your Zo AI
- [Architecture](docs/ARCHITECTURE.md) - How it works

## Components

- **Ollama** (nomic-embed-text) - Local 768D embeddings
- **Turso (sqld)** - Local vector database
- **Python client** - Memory storage and retrieval

## Requirements

- Zo Computer with root access
- ~500MB disk space
- Python 3.12+ (included with Zo)

## License

MIT
