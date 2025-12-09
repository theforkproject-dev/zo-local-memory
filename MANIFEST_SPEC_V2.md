# Zo Tool Manifest Specification v2.0

**Based on real AI installer feedback**

## Key Insight

AI installers are **literal executors**, not interpretive agents. They need:
- Explicit instructions, not assumptions
- Programmatic verification, not visual indicators
- Executable diagnostics, not troubleshooting guides
- Automated rollback, not manual recovery steps

---

## Minimal Manifest (v1.0 Compatible)

```json
{
  "manifestVersion": "2.0",
  "toolName": "Local Memory System",
  "toolSlug": "local-memory",
  "toolVersion": "1.0.0",
  "repository": "https://github.com/theforkproject-dev/zo-local-memory",
  
  "installation": {
    "command": "curl -sSL https://raw.githubusercontent.com/theforkproject-dev/zo-local-memory/main/install.sh | bash",
    "estimatedTime": "15-20 minutes",
    "requiresRoot": true,
    "requiresSudo": false
  }
}
```

---

## Enhanced Manifest (v2.0 Features)

### Installation with Step-Level Health Checks

```json
{
  "installation": {
    "steps": [
      {
        "name": "Install Ollama",
        "command": "curl -fsSL https://ollama.com/install.sh | sh",
        "estimated_seconds": 30,
        "idempotency_check": "command -v ollama",
        "health_check": {
          "command": "ollama --version",
          "expected_exit": 0,
          "timeout_seconds": 5
        }
      },
      {
        "name": "Download embedding model",
        "command": "curl -s http://localhost:11434/api/pull -d '{\"name\": \"nomic-embed-text\"}'",
        "estimated_seconds": 300,
        "variable_duration": true,
        "progress_indicator": "Downloading model... (may take 5-10 minutes on slow networks)",
        "health_check": {
          "command": "curl -s http://localhost:11434/api/tags | grep -q nomic-embed-text",
          "expected_exit": 0,
          "retry_attempts": 3,
          "retry_delay_seconds": 2
        }
      }
    ]
  }
}
```

### Downloads with Checksums

```json
{
  "downloads": [
    {
      "name": "local_memory_client.py",
      "url": "https://raw.githubusercontent.com/theforkproject-dev/zo-local-memory/main/src/local_memory_client.py",
      "destination": "/home/workspace/.zo/local_memory_client.py",
      "sha256": "abc123...",
      "verify_command": "echo 'abc123... /home/workspace/.zo/local_memory_client.py' | sha256sum -c",
      "mirror_urls": [
        "https://backup-cdn.example.com/local_memory_client.py"
      ],
      "retry_attempts": 3,
      "retry_delay_seconds": 2
    }
  ]
}
```

### Service Verification with Polling

```json
{
  "postInstall": [
    {
      "type": "service_verification",
      "services": ["ollama", "sqld"],
      "command": "supervisorctl -c /etc/zo/supervisord-user.conf status {service}",
      "expected_status": "RUNNING",
      "retry_attempts": 30,
      "retry_delay_seconds": 1,
      "timeout_seconds": 60,
      "health_check": {
        "ollama": "curl -s http://localhost:11434/api/version",
        "sqld": "curl -s http://localhost:8787/ -d '{\"statements\":[{\"q\":\"SELECT 1\"}]}'"
      }
    }
  ]
}
```

### Persona Setup (Explicit)

```json
{
  "postInstall": [
    {
      "type": "persona_setup",
      "action": "create_persona",
      "name": "Memory-Enabled Zo",
      "promptUrl": "https://raw.githubusercontent.com/theforkproject-dev/zo-local-memory/main/docs/PERSONA.md",
      "set_as_active": true,
      "verify_dependencies": [
        "/home/workspace/.zo/memory_integration.py",
        "/home/workspace/.zo/memory_formatting.py",
        "/home/workspace/.zo/local_memory_client.py"
      ],
      "test_command": "python3 /home/workspace/.zo/memory_integration.py initialize"
    }
  ]
}
```

### Error Handling

```json
{
  "troubleshooting": [
    {
      "error_pattern": "bind: address already in use.*11434",
      "diagnostic_command": "lsof -i :11434",
      "explanation": "Port 11434 is in use by another process",
      "suggested_fix": "Stop the conflicting service",
      "automated_fix": {
        "command": "pkill -f 'ollama serve' && sleep 2 && supervisorctl -c /etc/zo/supervisord-user.conf start ollama",
        "requires_user_approval": true
      }
    },
    {
      "error_pattern": "Failed to download.*githubusercontent",
      "diagnostic_command": "curl -I https://raw.githubusercontent.com",
      "explanation": "GitHub download failed (rate limit or network issue)",
      "suggested_fix": "Retry installation in a few minutes",
      "automated_fix": {
        "use_mirror": true,
        "retry_with_backoff": true
      }
    }
  ]
}
```

### Rollback

```json
{
  "rollback": {
    "enabled": true,
    "script_url": "https://raw.githubusercontent.com/theforkproject-dev/zo-local-memory/main/rollback.sh",
    "steps": [
      {
        "name": "Stop services",
        "command": "supervisorctl -c /etc/zo/supervisord-user.conf stop ollama sqld",
        "ignore_errors": true
      },
      {
        "name": "Remove supervisor config",
        "command": "sed -i '/\\[program:ollama\\]/,/^\\[/d' /etc/zo/supervisord-user.conf"
      },
      {
        "name": "Remove client files",
        "command": "rm -f /home/workspace/.zo/{local_memory_client,memory_integration,memory_formatting}.py"
      },
      {
        "name": "Reload supervisor",
        "command": "supervisorctl -c /etc/zo/supervisord-user.conf reread && supervisorctl -c /etc/zo/supervisord-user.conf update"
      }
    ],
    "verification": {
      "command": "! supervisorctl -c /etc/zo/supervisord-user.conf status | grep -E '(ollama|sqld)'",
      "expected_exit": 0
    }
  }
}
```

### User Notifications (Step-Specific)

```json
{
  "userNotifications": {
    "perStep": true,
    "steps": {
      "Install Ollama": "Installing Ollama embedding service...",
      "Download embedding model": "Downloading 270MB model (3-10 minutes depending on network)...",
      "Configure services": "Setting up supervised services...",
      "Download client": "Installing Python libraries...",
      "Verify installation": "Running health checks..."
    },
    "progress_format": "[{current}/{total}] {message}",
    "success": "✅ Local Memory System installed and verified!",
    "failure": "❌ Installation failed at: {failed_step}. Rollback available."
  }
}
```

---

## Complete v2.0 Manifest Example

```json
{
  "manifestVersion": "2.0",
  "toolName": "Local Memory System",
  "toolSlug": "local-memory",
  "toolVersion": "1.0.0",
  "repository": "https://github.com/theforkproject-dev/zo-local-memory",
  
  "installation": {
    "command": "curl -sSL https://raw.githubusercontent.com/theforkproject-dev/zo-local-memory/main/install.sh | bash",
    "estimatedTime": "15-20 minutes",
    "requiresRoot": true,
    "requiresSudo": false,
    
    "steps": [
      {
        "name": "Check Zo environment",
        "command": "test -f /etc/zo/supervisord-user.conf",
        "estimated_seconds": 1,
        "required": true
      },
      {
        "name": "Install Ollama",
        "command": "curl -fsSL https://ollama.com/install.sh | sh",
        "estimated_seconds": 30,
        "idempotency_check": "command -v ollama",
        "health_check": {
          "command": "ollama --version",
          "expected_exit": 0,
          "timeout_seconds": 5
        }
      },
      {
        "name": "Configure Ollama service",
        "command": "cat >> /etc/zo/supervisord-user.conf << 'EOF'\n[program:ollama]\n...\nEOF\nsupervisorctl reread && supervisorctl update",
        "estimated_seconds": 5,
        "idempotency_check": "grep -q '\\[program:ollama\\]' /etc/zo/supervisord-user.conf",
        "health_check": {
          "command": "supervisorctl status ollama | grep RUNNING",
          "expected_exit": 0,
          "retry_attempts": 30,
          "retry_delay_seconds": 1
        }
      },
      {
        "name": "Download embedding model",
        "command": "curl -s http://localhost:11434/api/pull -d '{\"name\": \"nomic-embed-text\"}'",
        "estimated_seconds": 300,
        "variable_duration": true,
        "health_check": {
          "command": "curl -s http://localhost:11434/api/tags | grep -q nomic-embed-text",
          "expected_exit": 0
        }
      }
    ]
  },
  
  "downloads": [
    {
      "name": "local_memory_client.py",
      "url": "https://raw.githubusercontent.com/theforkproject-dev/zo-local-memory/main/src/local_memory_client.py",
      "destination": "/home/workspace/.zo/local_memory_client.py",
      "sha256": "TBD",
      "retry_attempts": 3
    }
  ],
  
  "postInstall": [
    {
      "type": "service_verification",
      "services": ["ollama", "sqld"],
      "command": "supervisorctl -c /etc/zo/supervisord-user.conf status {service}",
      "expected_status": "RUNNING",
      "retry_attempts": 30,
      "retry_delay_seconds": 1
    },
    {
      "type": "persona_setup",
      "action": "create_persona",
      "name": "Memory-Enabled Zo",
      "promptUrl": "https://raw.githubusercontent.com/theforkproject-dev/zo-local-memory/main/docs/PERSONA.md",
      "set_as_active": true,
      "verify_dependencies": [
        "/home/workspace/.zo/memory_integration.py",
        "/home/workspace/.zo/memory_formatting.py",
        "/home/workspace/.zo/local_memory_client.py"
      ]
    }
  ],
  
  "verification": {
    "end_to_end": {
      "command": "python3 /home/workspace/.zo/memory_integration.py initialize",
      "expected_exit": 0,
      "timeout_seconds": 10
    }
  },
  
  "troubleshooting": [
    {
      "error_pattern": "bind: address already in use.*11434",
      "diagnostic_command": "lsof -i :11434",
      "automated_fix": {
        "command": "pkill -f 'ollama serve' && sleep 2 && supervisorctl start ollama",
        "requires_user_approval": true
      }
    }
  ],
  
  "rollback": {
    "enabled": true,
    "script_url": "https://raw.githubusercontent.com/theforkproject-dev/zo-local-memory/main/rollback.sh"
  },
  
  "userNotifications": {
    "perStep": true,
    "progress_format": "[{current}/{total}] {message}",
    "success": "✅ Installation complete and verified!",
    "failure": "❌ Failed at: {failed_step}. Rollback available."
  },
  
  "documentation": {
    "deploy": "https://github.com/theforkproject-dev/zo-local-memory/blob/main/docs/DEPLOY.md",
    "persona": "https://github.com/theforkproject-dev/zo-local-memory/blob/main/docs/PERSONA.md",
    "quickStart": "https://github.com/theforkproject-dev/zo-local-memory/blob/main/docs/QUICK_START.md"
  }
}
```

---

## Migration from v1.0 to v2.0

v1.0 manifests remain valid. v2.0 adds:

**Breaking Changes**: None (fully backward compatible)

**New Features**:
- Per-step health checks
- SHA256 checksums for downloads
- Service polling with retry logic
- Explicit persona activation
- Executable error handling
- Automated rollback
- Step-specific progress notifications

**When to Use v2.0**:
- Tools with services that take time to start
- Tools with large downloads
- Tools where installation failure is high-risk
- Tools requiring complex post-install verification

---

## Implementation Guide for AI Installers

### Parsing the Manifest

```python
import json
import re
from html.parser import HTMLParser

def extract_manifest(html: str) -> dict:
    match = re.search(
        r'<script[^>]*id="zo-tool-manifest"[^>]*>(.*?)</script>',
        html,
        re.DOTALL
    )
    if match:
        return json.loads(match.group(1))
    return None
```

### Executing Installation with Health Checks

```python
def install_tool(manifest: dict):
    for step in manifest['installation']['steps']:
        # Check idempotency
        if 'idempotency_check' in step:
            if os.system(step['idempotency_check']) == 0:
                continue  # Already installed
        
        # Execute command
        result = os.system(step['command'])
        if result != 0:
            handle_error(step, result)
            return False
        
        # Run health check with retry
        if 'health_check' in step:
            if not verify_health(step['health_check']):
                return False
    
    return True

def verify_health(health_check: dict) -> bool:
    attempts = health_check.get('retry_attempts', 1)
    delay = health_check.get('retry_delay_seconds', 1)
    
    for attempt in range(attempts):
        result = os.system(health_check['command'])
        if result == health_check.get('expected_exit', 0):
            return True
        time.sleep(delay)
    
    return False
```

---

## Key Principles for v2.0

1. **Declarative, not imperative** - Manifest describes desired state, not implementation
2. **Verifiable at each step** - Health checks after every operation
3. **Recoverable from failure** - Rollback procedures included
4. **Transparent to user** - Progress and status always visible
5. **Deterministic** - Same manifest + same environment = same result
6. **Auditable** - All commands and checks logged
7. **Secure** - Checksums verify file integrity
8. **Resilient** - Retry logic handles transient failures

---

**Specification maintained by**: The Fork Project  
**Last updated**: 2025-12-09  
**Version**: 2.0.0  
**Feedback source**: Live AI installer experience
