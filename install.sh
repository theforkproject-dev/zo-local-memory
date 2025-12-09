#!/usr/bin/env bash
set -e

echo "================================"
echo "Zo Local Memory System Installer"
echo "================================"
echo ""

# Check if running on Zo Computer
if [ ! -f "/etc/zo/supervisord-user.conf" ]; then
    echo "❌ Error: This script must be run on a Zo Computer"
    echo "   Could not find /etc/zo/supervisord-user.conf"
    exit 1
fi

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Error: This script must be run as root"
    echo "   Try: sudo bash install.sh"
    exit 1
fi

echo "✓ Running on Zo Computer"
echo ""

# Create directories
echo "[1/6] Creating directories..."
mkdir -p /home/workspace/.zo
mkdir -p /var/lib/sqld
echo "✓ Directories created"
echo ""

# Install Ollama
echo "[2/6] Installing Ollama..."
if command -v ollama &> /dev/null; then
    echo "✓ Ollama already installed"
else
    curl -fsSL https://ollama.com/install.sh | sh
    echo "✓ Ollama installed"
fi
echo ""

# Configure Ollama in supervisord
echo "[3/6] Configuring Ollama service..."
if grep -q "\[program:ollama\]" /etc/zo/supervisord-user.conf; then
    echo "✓ Ollama already configured in supervisord"
else
    cat >> /etc/zo/supervisord-user.conf << 'EOFOLLAMA'

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
EOFOLLAMA
    
    supervisorctl -c /etc/zo/supervisord-user.conf reread
    supervisorctl -c /etc/zo/supervisord-user.conf update
    sleep 3
    echo "✓ Ollama service configured"
fi
echo ""

# Pull embedding model
echo "[4/6] Downloading embedding model (nomic-embed-text, ~270MB)..."
curl -s http://localhost:11434/api/pull -d '{"name": "nomic-embed-text"}' > /dev/null 2>&1 || true
sleep 5
echo "✓ Embedding model downloaded"
echo ""

# Install Turso (sqld)
echo "[5/6] Installing Turso (sqld)..."
if command -v sqld &> /dev/null; then
    echo "✓ sqld already installed"
else
    cd /tmp
    curl -sL -o libsql-server.tar.xz \
        https://github.com/tursodatabase/libsql/releases/download/libsql-server-v0.24.32/libsql-server-x86_64-unknown-linux-gnu.tar.xz
    tar -xf libsql-server.tar.xz
    mv libsql-server-x86_64-unknown-linux-gnu/sqld /usr/local/bin/
    chmod +x /usr/local/bin/sqld
    rm -rf libsql-server.tar.xz libsql-server-x86_64-unknown-linux-gnu
    echo "✓ sqld installed"
fi
echo ""

# Configure sqld in supervisord
echo "[6/6] Configuring Turso service..."
if grep -q "\[program:sqld\]" /etc/zo/supervisord-user.conf; then
    echo "✓ sqld already configured in supervisord"
else
    cat >> /etc/zo/supervisord-user.conf << 'EOFSQLD'

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
EOFSQLD
    
    supervisorctl -c /etc/zo/supervisord-user.conf reread
    supervisorctl -c /etc/zo/supervisord-user.conf update
    sleep 3
    echo "✓ sqld service configured"
fi
echo ""

# Wait for services to be ready
echo "Waiting for services to start..."
sleep 5

# Initialize database schema
echo "Initializing database schema..."
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
}' > /dev/null

curl -s http://localhost:8787/ -H "Content-Type: application/json" -d '{
  "statements": [
    {"q": "CREATE INDEX IF NOT EXISTS idx_agent ON memories(agent_id)"},
    {"q": "CREATE INDEX IF NOT EXISTS idx_created ON memories(created_at)"},
    {"q": "CREATE INDEX IF NOT EXISTS idx_vector ON memories(libsql_vector_idx(embedding))"}
  ]
}' > /dev/null

echo "✓ Database schema initialized"
echo ""

# Download Python client library
echo "Installing Python client library..."
curl -sL https://raw.githubusercontent.com/theforkproject-dev/zo-local-memory/main/src/local_memory_client.py \
    -o /home/workspace/.zo/local_memory_client.py
chmod +x /home/workspace/.zo/local_memory_client.py
echo "✓ Python client installed"
echo ""

# Download verification prompt
echo "Installing verification prompt..."
mkdir -p /home/workspace/Prompts
curl -sL https://raw.githubusercontent.com/theforkproject-dev/zo-local-memory/main/prompts/verify-memory-system.prompt.md \
    -o /home/workspace/Prompts/verify-memory-system.prompt.md
echo "✓ Verification prompt installed to /home/workspace/Prompts/"
echo ""

# Test installation
echo "Testing installation..."
python3 << 'EOFTEST'
import sys
sys.path.insert(0, '/home/workspace/.zo')

try:
    from local_memory_client import LocalMemoryClient
    client = LocalMemoryClient(agent_id="main")
    health = client.health_check()
    
    if health['status'] == 'healthy':
        print("✓ All services healthy")
    else:
        print(f"⚠ Services status: {health}")
        sys.exit(1)
except Exception as e:
    print(f"❌ Test failed: {e}")
    sys.exit(1)
EOFTEST

echo ""
echo "================================"
echo "✓ Installation Complete!"
echo "================================"
echo ""
echo "Next steps:"
echo "1. Verify installation by running the verification prompt:"
echo "   @verify-memory-system"
echo ""
echo "2. Configure your Zo AI persona to use memory"
echo "   See: https://tools-hub-fork.zocomputer.io/local-memory"
echo ""
echo "3. Test the memory system:"
echo "   cd /home/workspace/.zo"
echo "   python3 -c 'from local_memory_client import LocalMemoryClient; c=LocalMemoryClient(); print(c.get_stats())'"
echo ""
echo "Services running:"
echo "  • Ollama: http://localhost:11434"
echo "  • Turso: http://localhost:8787"
echo "  • Database: /var/lib/sqld/memory-box.db"
echo ""


echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "⚠️  IMPORTANT: Persona Configuration Required"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "The memory system is installed, but your Zo AI needs to be"
echo "configured to use it. This requires creating a special persona."
echo ""
echo "OPTION 1 - Let Zo AI do it for you (RECOMMENDED):"
echo "──────────────────────────────────────────────────────────"
echo "  1. Start a new conversation with your Zo AI"
echo "  2. Say: 'Please set up the Memory-Enabled Zo persona for me'"
echo "  3. Your AI will create and activate the persona automatically"
echo ""
echo "OPTION 2 - Manual setup:"
echo "──────────────────────────────────────────────────────────"
echo "  1. Go to: Settings > Your AI > Personas"
echo "  2. Click 'Create Persona'"
echo "  3. Name it: 'Memory-Enabled Zo'"
echo "  4. Copy prompt from:"
echo "     https://github.com/theforkproject-dev/zo-local-memory/blob/main/docs/PERSONA.md"
echo "  5. Save and click 'Set as Active'"
echo ""
echo "Full documentation:"
echo "  https://github.com/theforkproject-dev/zo-local-memory/blob/main/docs/QUICK_START.md"
echo ""


