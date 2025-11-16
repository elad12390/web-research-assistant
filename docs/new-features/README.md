# SearXNG MCP Server - New Features Development Tracker

**Last Updated:** 2025-01-15 (Session 2)  
**Current Status:** Phase 2 Started - 1/5 tools complete  
**Active Work:** Package registry tool ✅ DONE

---

## 📋 Quick Status Overview

### ✅ Completed (Phase 1)
- [x] Basic project structure with modular architecture
- [x] `web_search` tool - SearXNG JSON API integration
- [x] `crawl_url` tool - crawl4ai integration for page content extraction
- [x] MCP-compliant response size limits (8KB default, configurable)
- [x] Environment-based configuration system
- [x] OpenCode integration (registered in global config)
- [x] Documentation (README, setup instructions)

### ✅ Completed (Phase 2)
- [x] **`package_info` tool** - npm, PyPI, crates.io, Go module search (2025-01-15)

### 🚧 In Progress (Phase 2)
- [ ] Error translator tool
- [ ] GitHub repository info tool
- [ ] Structured data extraction enhancement
- [ ] API explorer tool

### 📅 Planned (Phase 3+)
- [ ] Multi-source aggregation
- [ ] Site-specific search filters
- [ ] Library comparison matrix
- [ ] Security/CVE monitoring
- [ ] Service health dashboard

---

## 📂 File Structure

```
docs/new-features/
├── README.md              # This file - overall status and roadmap
├── TASKS.md              # Detailed task breakdown with priorities
├── HISTORY.md            # Development history and decisions log
├── error-translator/     # Planned feature specs
├── package-registry/     # Planned feature specs
├── github-info/          # Planned feature specs
└── structured-extract/   # Planned feature specs
```

---

## 🎯 Current Development Goals

### Phase 2 Priority Rankings (by daily impact)

1. **Package Registry Search** (Highest ROI)
   - **Why First:** Highest frequency (5+ uses/day), lowest complexity
   - **Status:** Not started
   - **See:** `TASKS.md` → Task #1

2. **Error Translator**
   - **Why Second:** Massive time savings (10+ uses/day), moderate complexity
   - **Status:** Not started
   - **See:** `TASKS.md` → Task #2

3. **GitHub Repo Info**
   - **Why Third:** High frequency (3-5 uses/day), simple GitHub API
   - **Status:** Not started
   - **See:** `TASKS.md` → Task #3

4. **Structured Data Extraction**
   - **Why Fourth:** Natural extension of existing `crawl_url` tool
   - **Status:** Not started
   - **See:** `TASKS.md` → Task #4

5. **API Explorer**
   - **Why Fifth:** Useful for integration work, moderate complexity
   - **Status:** Not started
   - **See:** `TASKS.md` → Task #5

---

## 🚀 Getting Started with New Features

### For Contributors

1. **Check current status**: Read this README
2. **Pick a task**: See `TASKS.md` for detailed breakdowns
3. **Review history**: Check `HISTORY.md` for context and past decisions
4. **Update as you go**: 
   - Mark tasks in progress in `TASKS.md`
   - Log decisions/changes in `HISTORY.md`
   - Update status in this README

### Development Workflow

```bash
# 1. Create feature branch
git checkout -b feature/package-registry

# 2. Implement in modular structure
# Add new module: searxng_mcp/registry.py
# Add new tool in: searxng_mcp/server.py

# 3. Update tracking docs
# Edit: docs/new-features/TASKS.md (mark in-progress)
# Edit: docs/new-features/HISTORY.md (log changes)

# 4. Test locally
uv run searxng-mcp

# 5. Commit with updates
git add .
git commit -m "feat: add package registry search tool"
```

---

## 📊 Success Metrics

### Phase 1 (Completed)
- ✅ Two working MCP tools
- ✅ Response times < 5s for search
- ✅ Response times < 15s for crawl
- ✅ Zero manual configuration needed for users
- ✅ Successfully integrated with OpenCode

### Phase 2 (Target)
- [ ] 5+ working tools covering daily workflows
- [ ] All tools maintain <10s response times
- [ ] Structured responses (not just text blobs)
- [ ] Error handling with fallbacks
- [ ] Test coverage >70%

---

## 🔄 Update Frequency

**CRITICAL:** Update these docs every time you:
- Start working on a new feature
- Complete a task or milestone
- Make architectural decisions
- Hit blockers or change direction
- Finish a development session

This ensures anyone (including future you) can pick up exactly where work stopped.

---

## 🆘 If You're Starting Fresh

**Lost context? Here's how to get oriented:**

1. Read `HISTORY.md` from bottom to top (most recent first)
2. Check which tasks in `TASKS.md` are marked "In Progress"
3. Review the specific feature folder for that task
4. Check git log for recent commits
5. Run `uv run searxng-mcp` to verify current state
6. Continue from last checkpoint

---

## 📞 Key Decisions & Constraints

### Architectural Choices
- **Language:** Python 3.10+ (best FastMCP SDK support)
- **MCP Library:** `mcp[cli]>=1.2.0` with FastMCP
- **Crawler:** crawl4ai (expert-level, handles complex sites)
- **Search:** Local SearXNG Docker instance (privacy, control)
- **File Size:** Keep modules <200 lines for maintainability

### Response Constraints
- **Max response:** 8KB default (configurable via `MCP_MAX_RESPONSE_CHARS`)
- **Truncation:** Auto-trim with helpful suffix when exceeded
- **Format:** Plain text with clear structure (markdown for crawl results)

### Design Principles
1. **Modular:** Each tool in its own helper class
2. **Configurable:** All constants in `config.py` with env overrides
3. **Explicit:** Clear docstrings so AI hosts understand tool purpose
4. **Resilient:** Graceful error handling, never crash the server

---

## 📝 Next Steps (Immediate)

1. Review `TASKS.md` and pick highest priority unassigned task
2. Create detailed spec in corresponding feature folder
3. Implement following existing modular pattern
4. Update `HISTORY.md` with implementation notes
5. Mark task complete in `TASKS.md` and update this README

---

**Ready to build? Start with `TASKS.md` for detailed implementation plans!**
