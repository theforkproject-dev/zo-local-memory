# AI-Assisted Installation for Zo Tools

## Overview

Zo tools can be installed automatically by your Zo AI through embedded machine-readable manifests. Non-technical users can simply share a URL and let their AI handle the entire installation process.

## How It Works

### 1. User Experience

**User**: "I want memory. Install it from https://tools-hub-fork.zocomputer.io/local-memory"

**Zo AI**:
1. Views the page using `view_webpage`
2. Finds the hidden `<script type="application/json" id="zo-tool-manifest">`
3. Parses the installation instructions
4. Confirms with user
5. Runs installation script
6. Creates and activates persona
7. Verifies services
8. Tests functionality
9. Notifies user of success

**Result**: Fully working memory system in 10-15 minutes, zero technical knowledge required.

### 2. Tool Manifest Schema

Every tool page embeds a JSON manifest that Zo AI can parse:

```json
{
  "manifestVersion": "1.0",
  "toolName": "Local Memory System",
  "toolSlug": "local-memory",
  "toolVersion": "1.0",
  "toolType": "memory",
  "tagline": "Persistent semantic memory with full data sovereignty",
  "installable": true,
  "aiAssistedInstall": true,
  
  "capabilities": [
    "Persistent AI memory across sessions",
    "Semantic search with 768D vectors"
  ],
  
  "installation": {
    "method": "bash-script",
    "command": "curl -sSL https://raw.githubusercontent.com/...",
    "requiresRoot": true,
    "estimatedTime": "10-15 minutes",
    "prerequisites": [...]
  },
  
  "postInstallation": {
    "required": true,
    "steps": [
      {
        "type": "create-persona",
        "action": "create_persona",
        "personaName": "Memory-Enabled Zo",
        "promptSource": "https://raw.githubusercontent.com/...",
        "autoActivate": true
      },
      {
        "type": "verify-services",
        "action": "run_bash_command",
        "command": "supervisorctl -c /etc/zo/supervisord-user.conf status..."
      }
    ]
  },
  
  "userGuidance": {
    "simpleInstall": "Just say: 'Install the local memory tool from URL'",
    "afterInstall": "Start a new conversation to test memory"
  },
  
  "notifications": {
    "preInstall": "📦 Installing...",
    "success": "🎉 Success!",
    "failure": "❌ Failed. Check logs..."
  }
}
```

### 3. AI Execution Logic

When Zo AI encounters a tool manifest:

```python
# Parse manifest from page
manifest = json.loads(tool_manifest_script_content)

# Confirm with user
print(manifest['notifications']['preInstall'])
response = input("Proceed? [y/N]: ")

# Run installation
run_bash_command(manifest['installation']['command'])

# Post-install steps
for step in manifest['postInstallation']['steps']:
    if step['type'] == 'create-persona':
        # Fetch persona prompt
        prompt = read_webpage(step['promptSource'])
        # Create persona
        persona_id = create_persona(
            name=step['personaName'],
            prompt=prompt
        )
        # Activate if specified
        if step['autoActivate']:
            set_active_persona(persona_id)
    
    elif step['type'] == 'verify-services':
        result = run_bash_command(step['command'])
        # Check if result contains expectedOutput
    
    elif step['type'] == 'test-storage':
        run_bash_command(step['command'])

# Notify user
print(manifest['notifications']['success'])
```

## Tool Registry

The `/tools` page provides a central registry of all available tools:

```json
{
  "registryVersion": "1.0",
  "tools": [
    {
      "name": "Local Memory System",
      "slug": "local-memory",
      "manifestUrl": "https://tools-hub-fork.zocomputer.io/local-memory",
      "aiAssistedInstall": true,
      "status": "stable"
    }
  ]
}
```

Users can browse available tools and their Zo AI can discover them automatically.

## Benefits

### For Non-Technical Users
- **No command-line knowledge needed** - just share a URL
- **AI handles everything** - installation, configuration, verification
- **Natural language interface** - "I want memory" is all it takes
- **Guided testing** - AI helps verify installation worked

### For Tool Developers
- **Standardized format** - consistent installation experience
- **Self-documenting** - all install details in one place
- **Version controlled** - manifest lives with the tool
- **Discoverable** - tools listed in central registry

### For the Ecosystem
- **Lower barrier to entry** - anyone can install tools
- **"Grow your own Zo"** - users can easily extend their AI
- **Composable** - tools can reference each other
- **Community driven** - easy to contribute new tools

## Creating Your Own Tool

To make your tool AI-installable:

### 1. Create Tool Manifest

Embed in your tool's web page:

```html
<script type="application/json" id="zo-tool-manifest">
{
  "manifestVersion": "1.0",
  "toolName": "Your Tool Name",
  "toolSlug": "your-tool",
  ...
}
</script>
```

### 2. Document Installation Steps

Break down installation into discrete steps:
- Installation command (bash script)
- Post-install configuration (persona, services, etc.)
- Verification tests
- User guidance

### 3. Write Clear Notifications

Provide helpful messages for:
- Pre-install confirmation
- Progress updates
- Success state
- Failure troubleshooting

### 4. Test with Zo AI

Ask your Zo AI to install from your tool's URL and verify:
- Manifest parsing works
- Installation completes successfully
- Post-install steps execute
- Verification passes
- User gets clear feedback

### 5. Submit to Registry

Open a PR to add your tool to the central registry.

## Example: Installing Local Memory

**User conversation with Zo AI**:

```
User: I want my Zo to remember our conversations. Can you install 
      the memory system from https://tools-hub-fork.zocomputer.io/local-memory?

Zo: I found the Local Memory System installation manifest. This will:
    • Install Ollama (embedding service)
    • Install Turso (vector database)  
    • Download nomic-embed-text model
    • Configure supervised services
    • Set up memory-enabled persona
    
    Estimated time: 10-15 minutes
    
    Shall I proceed?

User: Yes

Zo: [Runs installation script]
    ⏳ Installing Ollama...
    ⏳ Installing Turso...
    ⏳ Downloading embedding model...
    ⏳ Configuring services...
    🤖 Setting up Memory-Enabled Zo persona...
    ✅ Verifying installation...
    ✅ Testing memory storage...
    ✅ Testing memory retrieval...
    
    🎉 Local memory system installed successfully!
    
    You now have:
    • Persistent memory across conversations
    • Semantic search over past discussions
    • Full data sovereignty (all local)
    • Zero API costs
    
    Try me out! Start a new conversation and I'll remember our context.

User: [starts new conversation]
      What did we just install?

Zo: We just installed the Local Memory System. It gives me persistent
    memory across our conversations using local Ollama embeddings
    (768D) and Turso vector database. All your data stays on your
    Zo Computer—full sovereignty, zero API costs.
```

## Security Considerations

### User Consent Required
- AI must always confirm before running installation scripts
- Display what will be installed and what permissions are needed
- Show estimated time and disk space requirements

### Script Verification
- Installation scripts should be hosted on GitHub (verifiable, version controlled)
- Use HTTPS for all downloads
- Display script URL before running

### Service Isolation
- Services run as supervised processes (auto-restart, logging)
- Bind to localhost only (not publicly accessible)
- Follow Zo security best practices

## Future Enhancements

### Tool Dependencies
```json
"dependencies": [
  {
    "toolSlug": "local-memory",
    "minimumVersion": "1.0"
  }
]
```

### Upgrade Paths
```json
"upgrade": {
  "from": "0.9",
  "to": "1.0",
  "command": "curl -sSL https://... | bash"
}
```

### Health Checks
```json
"health": {
  "endpoint": "http://localhost:8787/health",
  "expectedStatus": 200,
  "interval": "5m"
}
```

---

**The AI-assisted installation pattern makes "Grow your own Zo" accessible to everyone.**
