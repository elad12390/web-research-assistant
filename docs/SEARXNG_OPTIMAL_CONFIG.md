# Optimal Free SearXNG Configuration

## Best Free Search Engines to Enable

### 🌐 General Web Search (Essential)
Enable these for broad web coverage:

```yaml
# In your SearXNG settings.yml
engines:
  - name: duckduckgo
    engine: duckduckgo
    shortcut: ddg
    disabled: false
    
  - name: brave
    engine: brave
    shortcut: br
    disabled: false
    
  - name: qwant
    engine: qwant
    shortcut: qw
    disabled: false
```

**Why:** Free, privacy-respecting, no API keys needed, good general coverage

---

### 💻 Code & Developer Resources (CRITICAL for search_examples)

```yaml
  - name: github
    engine: github
    shortcut: gh
    disabled: false
    
  - name: stackoverflow
    engine: stackoverflow
    shortcut: so
    disabled: false
    
  - name: gitlab
    engine: gitlab
    shortcut: gl
    disabled: false
    
  - name: codeberg
    engine: codeberg
    shortcut: cb
    disabled: false
```

**Why:** These give you actual code repositories and Q&A - exactly what `search_examples` needs!

---

### 📚 Documentation & Tutorials

```yaml
  - name: mdn
    engine: mdn
    shortcut: mdn
    disabled: false
    # You already have this!
    
  - name: devdocs
    engine: devdocs
    shortcut: dd
    disabled: false
    
  - name: wikipedia
    engine: wikipedia
    shortcut: wp
    disabled: false
```

**Why:** Official documentation and educational content

---

### 📰 Tech News & Articles

```yaml
  - name: reddit
    engine: reddit
    shortcut: re
    disabled: false
    
  - name: hackernews
    engine: hackernews
    shortcut: hn
    disabled: false
```

**Why:** Real-world discussions, tutorials, and tech articles

---

### 🎥 Video Content (Optional but useful)

```yaml
  - name: youtube
    engine: youtube_noapi
    shortcut: yt
    disabled: false
    
  - name: peertube
    engine: peertube
    shortcut: pt
    disabled: false
```

**Why:** Video tutorials and coding screencasts (no API key needed with youtube_noapi)

---

### 📦 Package Registries (Helpful)

```yaml
  - name: pypi
    engine: pypi
    shortcut: pypi
    disabled: false
    
  - name: npm
    engine: npm
    shortcut: npm
    disabled: false
    
  - name: crates
    engine: crates
    shortcut: cr
    disabled: false
```

**Why:** Find packages (though we have dedicated tools for this)

---

### 🎨 Images (If not using Pixabay tool)

```yaml
  - name: unsplash
    engine: unsplash
    shortcut: us
    disabled: false
    
  - name: flickr
    engine: flickr_noapi
    shortcut: fl
    disabled: false
```

**Why:** Free stock photos (alternative to our Pixabay tool)

---

## Minimal Optimal Configuration (Start Here)

If you want the **minimum for great results**, enable these 8 engines:

1. **duckduckgo** - General web
2. **brave** - General web backup
3. **github** - Code repositories ⭐
4. **stackoverflow** - Code Q&A ⭐
5. **mdn** - Documentation (you have this)
6. **wikipedia** - General knowledge
7. **reddit** - Discussions & tutorials
8. **hackernews** - Tech articles

---

## Full Recommended Configuration

Save this to your SearXNG `settings.yml`:

```yaml
search:
  safe_search: 0
  autocomplete: "duckduckgo"
  default_lang: "en"

engines:
  # General Web
  - name: duckduckgo
    engine: duckduckgo
    shortcut: ddg
    
  - name: brave
    engine: brave
    shortcut: br
    
  - name: qwant
    engine: qwant
    shortcut: qw
  
  # Code & Developer
  - name: github
    engine: github
    shortcut: gh
    
  - name: stackoverflow
    engine: stackoverflow
    shortcut: so
    
  - name: gitlab
    engine: gitlab
    shortcut: gl
  
  # Documentation
  - name: mdn
    engine: mdn
    shortcut: mdn
    
  - name: wikipedia
    engine: wikipedia
    shortcut: wp
    
  # Tech Community
  - name: reddit
    engine: reddit
    shortcut: re
    
  - name: hackernews
    engine: hackernews
    shortcut: hn
    
  # Package Registries
  - name: pypi
    engine: pypi
    shortcut: pypi
    
  - name: npm
    engine: npm
    shortcut: npm
    
  # Video
  - name: youtube
    engine: youtube_noapi
    shortcut: yt
```

---

## Category Configuration

Make sure these categories include the right engines:

```yaml
categories_as_tabs:
  general:
    - duckduckgo
    - brave
    - qwant
    - wikipedia
    
  it:
    - github
    - stackoverflow
    - gitlab
    - mdn
    - hackernews
    - reddit
    
  science:
    - wikipedia
    - stackoverflow
    
  news:
    - reddit
    - hackernews
```

The **`it` category is crucial** - this is what `search_examples` uses!

---

## Engines to AVOID (Cost Money or Need API Keys)

❌ **Don't enable these without API keys:**
- Google (requires API key + costs money after 100 queries/day)
- Bing (requires API key)
- YouTube API (requires Google API key)
- Flickr API (requires API key)

✅ **Use these free alternatives instead:**
- DuckDuckGo instead of Google
- Brave instead of Bing
- youtube_noapi instead of youtube
- flickr_noapi instead of flickr

---

## Testing Your Configuration

After updating your `settings.yml`:

1. **Restart SearXNG:**
```bash
docker restart searxng  # or however you run it
```

2. **Test with our tool:**
```python
search_examples("React hooks examples", content_type="code")
```

You should now see results from:
- GitHub repositories
- Stack Overflow answers
- Reddit discussions
- MDN documentation

---

## Expected Results After Configuration

### Before (MDN only):
```
1. Site glossary
   https://developer.mozilla.org/...

2. XSS documentation
   https://developer.mozilla.org/...
```

### After (Diverse sources):
```
1. [GitHub] facebook/react - Hooks documentation
   https://github.com/facebook/react/...

2. [Stack Overflow] How to use React hooks
   https://stackoverflow.com/q/12345678...

3. [Article] React Hooks Tutorial
   https://reddit.com/r/reactjs/...

4. React Hooks - MDN
   https://developer.mozilla.org/...
```

---

## Quick Setup Checklist

- [ ] Enable DuckDuckGo (general web)
- [ ] Enable Brave (general web backup)
- [ ] Enable GitHub (code repos) ⭐
- [ ] Enable Stack Overflow (code Q&A) ⭐
- [ ] Enable GitLab (more code repos)
- [ ] Keep MDN (documentation)
- [ ] Enable Reddit (discussions)
- [ ] Enable HackerNews (tech news)
- [ ] Configure 'it' category with code engines
- [ ] Restart SearXNG
- [ ] Test with search_examples tool

---

## Performance Tips

1. **Don't enable too many engines** - 8-12 is optimal
2. **Prioritize code engines** for our use case
3. **Use categories** - assign engines to relevant categories
4. **Test incrementally** - add a few engines, test, repeat

---

## Where to Find settings.yml

**Docker:**
```bash
# Usually in a volume mount
docker inspect searxng | grep -A 5 Mounts

# Common locations:
/etc/searxng/settings.yml
./searxng/settings.yml
```

**Native Install:**
```bash
/etc/searxng/settings.yml
~/.config/searxng/settings.yml
```

---

## Need Help?

If you need a complete example `settings.yml`, check:
- SearXNG docs: https://docs.searxng.org/
- Example config: https://github.com/searxng/searxng/blob/master/searx/settings.yml

---

**After this configuration, `search_examples` will return high-quality code examples from GitHub, Stack Overflow, and more!** 🎉
