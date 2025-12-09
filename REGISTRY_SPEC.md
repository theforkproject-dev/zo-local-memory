# Zo Automated Tool Registry - Specification v1.0

## Purpose

Enable developers to publish AI-installable tools for Zo Computer. Users share a URL with their Zo AI, which automatically handles installation, configuration, and verification.

## Philosophy: Prompt Injection for Good

Traditional prompt injection is a security vulnerability—malicious instructions hidden in data. We're using the same mechanism for collaboration:

- **User consents** explicitly by sharing the URL
- **Instructions are transparent**—visible in the manifest
- **AI confirms before executing**—no surprises
- **Purpose is beneficial**—extending capabilities

This is automation through collaboration.

## Tool Requirements

### 1. Installation
- Bash script hosted on GitHub
- Idempotent (safe to run multiple times)
- Non-interactive (no user prompts)
- Clear output (progress and errors)

### 2. Service Management
- Use supervisord for persistent services
- Bind to localhost only (not public)
- Log to `/dev/shm/` for monitoring
- Auto-restart on failure

### 3. Documentation
- README.md with clear description
- Deployment guide (step-by-step)
- Architecture documentation
- Usage examples with code

### 4. Security
- Open source (publicly reviewable)
- MIT license or similar
- No external data transmission without consent
- HTTPS only for downloads

## Manifest Schema

Embed in your tool's page:

```html
<script type="application/json" id="zo-tool-manifest">
{
  "manifestVersion": "1.0",
  "toolName": "Your Tool Name",
  "toolSlug": "your-tool-slug",
  "toolVersion": "1.0",
  "toolType": "memory|integration|analytics|other",
  "tagline": "Brief description",
  "description": "Detailed description",
  "installable": true,
  "aiAssistedInstall": true,
  
  "capabilities": [
    "First key capability",
    "Second key capability"
  ],
  
  "installation": {
    "method": "bash-script",
    "command": "curl -sSL https://raw.githubusercontent.com/.../install.sh | bash",
    "requiresRoot": true,
    "estimatedTime": "10-15 minutes",
    "diskSpace": "500MB",
    "prerequisites": [
      "Zo Computer with root access",
      "500MB free disk space"
    ]
  },
  
  "postInstallation": {
    "required": true,
    "steps": [
      {
        "type": "create-persona",
        "action": "create_persona",
        "personaName": "Tool-Enabled Zo",
        "promptSource": "https://raw.githubusercontent.com/.../prompt.txt",
        "autoActivate": true
      },
      {
        "type": "verify-services",
        "action": "run_bash_command",
        "command": "supervisorctl status your-service",
        "expectedOutput": "RUNNING"
      }
    ]
  },
  
  "userGuidance": {
    "simpleInstall": "Say: 'Install [tool] from [URL]'",
    "afterInstall": "Start new conversation to test",
    "documentation": "https://github.com/..."
  },
  
  "notifications": {
    "preInstall": "📦 Installing...",
    "success": "🎉 Success!",
    "failure": "❌ Failed. Check logs..."
  },
  
  "resources": {
    "repository": "https://github.com/...",
    "documentation": "https://github.com/.../docs/",
    "issues": "https://github.com/.../issues"
  }
}
</script>
```

## Submission Process

1. **Build Your Tool** — Follow requirements above
2. **Add Manifest** — Embed JSON in your tool's page
3. **Test AI Installation** — Verify automated install works
4. **Submit PR** — Add entry to `theforkproject-dev/zo-tool-registry`
5. **Review & Publish** — We review for security/quality

## Registry Entry Format

Add to `registry.json`:

```json
{
  "name": "Your Tool Name",
  "slug": "your-tool",
  "version": "1.0",
  "tagline": "Brief description",
  "manifestUrl": "https://your-site.com/tool-page",
  "repository": "https://github.com/you/your-tool",
  "author": "Your Name",
  "license": "MIT",
  "status": "stable",
  "aiAssistedInstall": true,
  "addedDate": "2025-12-09"
}
```

## Quality Standards

### ✓ Documentation Quality
Clear README, deployment guide, architecture docs, examples

### ✓ Installation Reliability
Tested on fresh Zo Computer, idempotent, handles errors

### ✓ Security Review
No malicious code, localhost-only services, transparent data handling

### ✓ User Experience
Progress indicators, helpful errors, working verification tests

## Versioning

Follow semantic versioning (MAJOR.MINOR.PATCH):

- **MAJOR** — Breaking changes (require reinstall)
- **MINOR** — New features (backward compatible)
- **PATCH** — Bug fixes

Update manifest's `toolVersion` when releasing.

## Example

See [Local Memory System](https://github.com/theforkproject-dev/zo-local-memory) for complete reference implementation.

## Security Principles

1. **User consent required** — AI confirms before executing
2. **Transparent instructions** — What's installed, permissions needed
3. **Verifiable sources** — GitHub-hosted scripts, HTTPS only
4. **Service isolation** — Localhost-only by default
5. **Registry curation** — Tools meet quality/security standards

## Resources

- Philosophy: https://tools-hub-fork.zocomputer.io/philosophy
- Full Spec: https://tools-hub-fork.zocomputer.io/registry-spec
- Example Tool: https://github.com/theforkproject-dev/zo-local-memory
- GitHub: https://github.com/theforkproject-dev

---

**Grow your own Zo.** Make it accessible to everyone.
