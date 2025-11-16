# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability in Web Research Assistant, please report it by emailing **elad12390@gmail.com**.

**Please do not report security vulnerabilities through public GitHub issues.**

### What to Include

When reporting a vulnerability, please include:

- Description of the vulnerability
- Steps to reproduce the issue
- Potential impact
- Suggested fix (if you have one)

### Response Timeline

- **Initial Response**: Within 48 hours
- **Status Update**: Within 7 days
- **Fix Timeline**: Varies by severity, but critical issues will be prioritized

## Security Considerations

### API Keys and Secrets

This MCP server uses environment variables for sensitive data:

- `PIXABAY_API_KEY` - Optional Pixabay API key for image search
- `GITHUB_TOKEN` - Optional GitHub token for higher rate limits

**Never commit API keys or tokens to the repository.**

### Local SearXNG Instance

This server connects to a local SearXNG instance. Ensure your SearXNG instance is:

- Running locally (not exposed to the internet)
- Properly configured with rate limiting
- Updated to the latest version

### Web Crawling

The `crawl_url` tool fetches content from arbitrary URLs. Be aware:

- Only crawl URLs from trusted sources
- The tool respects a maximum character limit to prevent memory issues
- Malicious websites could potentially return harmful content

### Usage Analytics

Usage data is stored locally in `~/.config/web-research-assistant/usage.json`. This file:

- Contains tool usage statistics and reasoning parameters
- Does not contain API keys or sensitive data
- Is stored with user-only permissions
- Can be disabled or deleted if desired

## Best Practices

1. **Keep dependencies updated**: Run `uv sync` regularly to get security patches
2. **Use environment variables**: Never hardcode API keys
3. **Limit SearXNG access**: Keep your SearXNG instance local-only
4. **Review crawled content**: Be cautious when crawling untrusted URLs
5. **Monitor usage logs**: Check `usage.json` for unusual patterns

## Acknowledgments

We appreciate the security research community's efforts to improve the security of open source projects.
