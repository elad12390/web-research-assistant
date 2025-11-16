# API Explorer - Design Document

## Overview

A comprehensive API exploration tool that combines **structured API specs** (OpenAPI/Swagger) with **human-readable documentation** to give you the complete picture when integrating with APIs.

## The Problem

When integrating with a new API, you need:
1. ✅ **Structure** - Endpoints, parameters, request/response schemas (from OpenAPI spec)
2. ✅ **Context** - What it does, why you'd use it, examples (from docs)
3. ✅ **Examples** - Real request/response examples, code snippets
4. ✅ **Authentication** - How to authenticate, where to get API keys

Current solution is fragmented:
- Read OpenAPI spec separately
- Browse documentation website separately
- Search for examples separately
- Piece it together manually

## Proposed Solution: Multi-Source API Explorer

### Tool 1: `explore_api` (Primary Tool)

**Purpose:** One-stop shop for API exploration combining spec + docs

**How it works:**
```python
explore_api(
    api_name="stripe",  # or URL to OpenAPI spec
    endpoint="/v1/customers",  # optional - specific endpoint
    reasoning="Setting up payment integration"
)
```

**Multi-step process:**

1. **Fetch OpenAPI/Swagger Spec**
   - Try common locations:
     - `https://api.{name}.com/openapi.json`
     - `https://api.{name}.com/swagger.json`
     - `https://{name}.com/api/v1/openapi.json`
   - Or use provided URL directly
   
2. **Parse Spec Structure**
   - Extract endpoints, methods, parameters
   - Parse request/response schemas
   - Identify authentication methods
   
3. **Fetch Documentation** (The Key Addition!)
   - Try common doc locations:
     - `https://docs.{name}.com`
     - `https://{name}.com/docs`
     - `https://developers.{name}.com`
   - Search for endpoint-specific docs using web_search
   - Crawl relevant doc pages using crawl_url
   
4. **Combine & Present**
   - Show spec structure PLUS doc explanations
   - Include examples from both sources
   - Highlight authentication requirements

### Tool 2: `search_api_docs` (Supplementary)

**Purpose:** Search API documentation when you know what you're looking for

```python
search_api_docs(
    api_name="stripe",
    query="create subscription with trial period",
    reasoning="Implementing free trial flow"
)
```

**How it works:**
1. Search `site:docs.{api_name}.com {query}`
2. Crawl top 2-3 results
3. Extract relevant sections
4. Return formatted documentation

### Tool 3: `get_api_examples` (Supplementary)

**Purpose:** Find real-world code examples for specific API operations

```python
get_api_examples(
    api_name="stripe",
    endpoint="/v1/subscriptions",
    language="python",  # optional
    reasoning="Need working example code"
)
```

**How it works:**
1. Search GitHub for examples: `{api_name} {endpoint} language:{language}`
2. Search Stack Overflow for examples
3. Extract code snippets
4. Rank by quality (stars, votes)

## Implementation Strategy

### Phase 1: Core API Explorer ✅ START HERE
Build `explore_api` with:
- OpenAPI/Swagger spec fetching
- Basic spec parsing (endpoints, parameters)
- Documentation URL detection
- Simple doc crawling

### Phase 2: Enhanced Documentation
Add to `explore_api`:
- Smart doc section extraction
- Endpoint-specific doc matching
- Example extraction from docs
- Authentication guide extraction

### Phase 3: Supplementary Tools
Add separate tools:
- `search_api_docs` for targeted searches
- `get_api_examples` for code examples

## Detailed Design: explore_api

### Input Parameters

```python
@mcp.tool()
async def explore_api(
    api_identifier: str,  # Name (e.g., "stripe") or OpenAPI spec URL
    reasoning: str,  # Required for analytics
    endpoint: str | None = None,  # Specific endpoint to explore
    fetch_docs: bool = True,  # Fetch human-readable docs
    fetch_examples: bool = True,  # Fetch code examples
) -> str:
```

### Output Format

```
API Explorer: Stripe API
════════════════════════════════════════════════════════════════════

📋 API Information:
   Name: Stripe API
   Version: 2023-10-16
   Base URL: https://api.stripe.com/v1
   Documentation: https://stripe.com/docs/api
   
🔐 Authentication:
   Type: Bearer Token
   Header: Authorization: Bearer sk_test_...
   Docs: https://stripe.com/docs/api/authentication
   
📍 Endpoint: POST /v1/customers
────────────────────────────────────────────────────────────────────

📖 Description (from docs):
   Creates a new customer object. Customers can be charged immediately
   or subscribed to a plan. Use customers to track multiple charges
   associated with a single user.
   
📥 Request Parameters:
   email (string, optional)
     - Customer's email address
     - Example: "customer@example.com"
   
   name (string, optional)
     - Customer's full name
     - Example: "John Doe"
   
   metadata (object, optional)
     - Key-value pairs for custom data
     - Example: {"user_id": "123", "plan": "premium"}
   
   payment_method (string, optional)
     - ID of payment method to attach
     - Example: "pm_1234567890"

📤 Response (200 OK):
   {
     "id": "cus_1234567890",
     "object": "customer",
     "email": "customer@example.com",
     "created": 1234567890,
     "metadata": {}
   }

💡 Code Example (Python):
   ```python
   import stripe
   stripe.api_key = "sk_test_..."
   
   customer = stripe.Customer.create(
       email="customer@example.com",
       name="John Doe",
       metadata={"user_id": "123"}
   )
   ```

💡 Code Example (curl):
   ```bash
   curl https://api.stripe.com/v1/customers \
     -u sk_test_...: \
     -d email="customer@example.com" \
     -d name="John Doe"
   ```

🔗 Related Endpoints:
   - GET /v1/customers/{id} - Retrieve customer
   - POST /v1/customers/{id} - Update customer
   - DELETE /v1/customers/{id} - Delete customer

📚 Additional Resources:
   - Official Docs: https://stripe.com/docs/api/customers/create
   - Tutorial: https://stripe.com/docs/billing/subscriptions/creating
   - Guide: https://stripe.com/docs/payments/save-and-reuse
```

## Technical Implementation

### 1. OpenAPI Spec Fetching

```python
class OpenAPIClient:
    async def fetch_spec(self, identifier: str) -> dict:
        """Fetch OpenAPI spec from various sources."""
        # If it's a URL, fetch directly
        if identifier.startswith('http'):
            return await self._fetch_url(identifier)
        
        # Otherwise try common patterns
        common_urls = [
            f"https://api.{identifier}.com/openapi.json",
            f"https://api.{identifier}.com/swagger.json",
            f"https://{identifier}.com/api/openapi.json",
            f"https://raw.githubusercontent.com/{identifier}/openapi.json",
        ]
        
        for url in common_urls:
            try:
                return await self._fetch_url(url)
            except:
                continue
        
        raise ValueError(f"Could not find OpenAPI spec for {identifier}")
```

### 2. Documentation Discovery

```python
class APIDocsFinder:
    async def find_docs(self, api_name: str, base_url: str) -> str:
        """Find API documentation URL."""
        # Try common doc patterns
        doc_patterns = [
            f"https://docs.{api_name}.com",
            f"https://{api_name}.com/docs",
            f"https://developers.{api_name}.com",
            f"https://developer.{api_name}.com",
            f"https://{api_name}.com/documentation",
        ]
        
        # Also extract from OpenAPI spec (info.description often has links)
        
        # Verify URL is accessible
        for url in doc_patterns:
            if await self._is_accessible(url):
                return url
        
        # Fallback: search for it
        results = await searcher.search(
            f"{api_name} API documentation official",
            category="general",
            max_results=3
        )
        
        return results[0].url if results else None
```

### 3. Endpoint Documentation Matching

```python
async def fetch_endpoint_docs(
    self, 
    doc_base_url: str, 
    endpoint: str
) -> str:
    """Fetch documentation for specific endpoint."""
    
    # Try direct endpoint URL
    endpoint_path = endpoint.strip('/').replace('/', '-')
    doc_urls = [
        f"{doc_base_url}/api/{endpoint_path}",
        f"{doc_base_url}/reference/{endpoint_path}",
        f"{doc_base_url}/api-reference/{endpoint_path}",
    ]
    
    for url in doc_urls:
        try:
            content = await crawler_client.fetch(url)
            return content
        except:
            continue
    
    # Fallback: search within docs
    results = await searcher.search(
        f"site:{doc_base_url} {endpoint}",
        max_results=2
    )
    
    if results:
        return await crawler_client.fetch(results[0].url)
    
    return None
```

### 4. Example Extraction

```python
def extract_examples(self, doc_content: str, spec: dict) -> list:
    """Extract code examples from documentation."""
    examples = []
    
    # Look for code blocks
    code_blocks = re.findall(
        r'```(\w+)\n(.*?)```', 
        doc_content, 
        re.DOTALL
    )
    
    for lang, code in code_blocks:
        examples.append({
            'language': lang,
            'code': code.strip()
        })
    
    # Also extract from OpenAPI spec examples
    if 'examples' in spec:
        examples.extend(spec['examples'])
    
    return examples
```

## Popular APIs to Support

**Common patterns to recognize:**

1. **Stripe** - `https://stripe.com/docs/api`, OpenAPI at GitHub
2. **GitHub** - `https://docs.github.com/rest`, OpenAPI public
3. **Twilio** - `https://www.twilio.com/docs/api`, OpenAPI available
4. **SendGrid** - `https://docs.sendgrid.com`, OpenAPI available
5. **OpenAI** - `https://platform.openai.com/docs`, No official OpenAPI (manually documented)
6. **Anthropic** - `https://docs.anthropic.com`, No OpenAPI
7. **Shopify** - `https://shopify.dev/docs/api`, GraphQL + REST
8. **Slack** - `https://api.slack.com`, OpenAPI available
9. **Discord** - `https://discord.com/developers/docs`, OpenAPI available
10. **AWS** - Service-specific docs, has service specs

## Success Criteria

1. ✅ Can fetch and parse OpenAPI/Swagger specs
2. ✅ Can locate and crawl official API documentation
3. ✅ Can match endpoint specs with their documentation
4. ✅ Can extract code examples from docs
5. ✅ Can display authentication requirements clearly
6. ✅ Response time < 5 seconds for standard APIs
7. ✅ Works for top 10 popular APIs

## Future Enhancements

1. **Schema Visualization** - Convert JSON schemas to readable formats
2. **Interactive Testing** - Generate curl commands with real API key
3. **Rate Limit Info** - Extract and display rate limit details
4. **Webhook Documentation** - Special handling for webhook endpoints
5. **API Comparison** - Compare similar endpoints across APIs
6. **Changelog Tracking** - Track API version changes

## Estimated Complexity

- **Phase 1 (Core):** Medium - OpenAPI parsing is well-defined, doc discovery needs heuristics
- **Phase 2 (Enhanced):** Medium - Smart doc matching and extraction
- **Phase 3 (Supplementary):** Low - Builds on existing search tools

## Estimated Value

- **Daily Use:** 3-5 times/day during integration work
- **Time Saved:** 10-15 minutes per lookup (vs manual browsing)
- **Impact:** High - Drastically speeds up API integration

---

**Recommendation:** Start with Phase 1 (core explorer) that combines OpenAPI spec + documentation crawling. This alone would provide massive value.
