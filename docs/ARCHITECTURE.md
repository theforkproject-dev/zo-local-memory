# Local Memory System Architecture

## Overview

The local memory system provides persistent semantic memory for Zo AI using fully local infrastructure.

## Components

### 1. Ollama (Embedding Service)
- **Port**: localhost:11434
- **Model**: nomic-embed-text
- **Dimensions**: 768
- **Purpose**: Converts text to semantic vectors

### 2. Turso/sqld (Vector Database)
- **Port**: localhost:8787
- **Storage**: /var/lib/sqld/memory-box.db
- **Purpose**: Stores and searches vectors using libSQL

### 3. Python Client (Integration Layer)
- **Location**: /home/workspace/.zo/local_memory_client.py
- **Purpose**: Connects Ollama + Turso for memory operations

## Data Flow

\`\`\`
Store Memory:
  Text → Ollama (embed) → 768D vector → Turso (store)

Search Memory:
  Query → Ollama (embed) → 768D vector → Turso (cosine similarity) → Results
\`\`\`

## Database Schema

\`\`\`sql
CREATE TABLE memories (
  id TEXT PRIMARY KEY,
  agent_id TEXT NOT NULL,
  content TEXT NOT NULL,
  embedding F32_BLOB(768),
  metadata JSON,
  created_at INTEGER NOT NULL,
  updated_at INTEGER NOT NULL
);

CREATE INDEX idx_agent ON memories(agent_id);
CREATE INDEX idx_created ON memories(created_at);
CREATE INDEX idx_vector ON memories(libsql_vector_idx(embedding));
\`\`\`

## Performance

- **Embedding generation**: ~100ms per query
- **Vector search**: <10ms for 1000s of memories
- **Storage overhead**: ~3KB per memory (768 floats)

## Security

- All services bind to localhost only
- No external API calls after setup
- Database is standard SQLite (portable, inspectable)
