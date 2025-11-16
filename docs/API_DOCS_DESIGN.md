# API Documentation Explorer - Redesigned (Documentation-First Approach)

## The Real Problem

**OpenAPI specs are often insufficient:**
- ❌ Missing context and explanations
- ❌ No examples or only trivial ones
- ❌ Incomplete parameter descriptions
- ❌ No usage guidelines or best practices
- ❌ Often outdated or auto-generated poorly
- ❌ Doesn't explain the "why" - only the "what"

**What developers actually need:**
- ✅ Human-written explanations of what endpoints do
- ✅ Real-world examples with context
- ✅ Authentication flows with examples
- ✅ Common use cases and patterns
- ✅ Gotchas and limitations
- ✅ Rate limits and best practices

## New Approach: Documentation-First

**Priority 1:** Fetch and parse the official human-written documentation  
**Priority 2:** Extract examples and usage patterns  
**Priority 3:** Use OpenAPI spec only to fill gaps (if available)

## Proposed Tools

### Tool 1: `api_docs` (Primary - Documentation Search)

**Purpose:** Search and fetch specific API documentation with examples

```python
api_docs(
    api_name="stripe",
    topic="create customer",  # or "webhooks", "authentication", etc.
    reasoning="Setting up payment integration"
)
```

**What it does:**
1. **Find official docs** - Smart detection of official doc sites
2. **Search within docs** - Find relevant pages for the topic
3. **Crawl & extract** - Get the full content with examples
4. **Format nicely** - Clean up HTML, preserve code examples
5. **Include related pages** - Find "see also" and related endpoints

**Example output:**
```
Stripe API Documentation: Create a Customer
════════════════════════════════════════════════════════════════════

📖 Overview (from docs.stripe.com):
   Creating a customer object allows you to track multiple charges
   for the same customer and perform recurring charges. You can also
   track metadata and payment methods associated with the customer.
   
🔐 Authentication:
   Use your secret API key. Include it in the Authorization header:
   Authorization: Bearer sk_test_4eC39HqLyjWDarjtT1zdp7dc

📍 Endpoint: POST /v1/customers

📋 Parameters (with explanations from docs):
   
   email (string, optional)
     The customer's email address. This is used for sending receipts
     and can be used to identify the customer in your dashboard.
     Best practice: Always collect email for better fraud prevention.
     Example: "jenny.rosen@example.com"
   
   name (string, optional)  
     The customer's full name or business name.
     Example: "Jenny Rosen"
   
   description (string, optional)
     An arbitrary string for your own use. Often useful for displaying
     to users. Can be updated later.
     Example: "Customer for jenny.rosen@example.com"
   
   payment_method (string, optional)
     ID of the PaymentMethod to attach to the customer. When provided,
     the PaymentMethod is automatically set as the default.
     See: https://stripe.com/docs/api/payment_methods
     Example: "pm_1MqLiJLkdIwHu7ixUEgbIdZF"
   
   metadata (object, optional)
     Set of key-value pairs for storing additional information.
     Limit: 50 keys, key names ≤ 40 chars, values ≤ 500 chars.
     Example: {"order_id": "6735", "internal_customer_id": "user_12345"}

💡 Common Use Cases:

1. Create customer for one-time purchase:
   ```python
   customer = stripe.Customer.create(
       email=email,
       payment_method=payment_method_id,
       invoice_settings={
           'default_payment_method': payment_method_id
       }
   )
   ```

2. Create customer with subscription:
   ```python
   customer = stripe.Customer.create(
       email="jenny@example.com",
       name="Jenny Rosen",
       payment_method="pm_card_visa",
       invoice_settings={
           'default_payment_method': "pm_card_visa"
       },
   )
   
   subscription = stripe.Subscription.create(
       customer=customer.id,
       items=[{"price": "price_1MqLiJLkdIwHu7ix"}]
   )
   ```

3. Create customer and save payment method for later:
   ```python
   # First, create the customer
   customer = stripe.Customer.create(email="customer@example.com")
   
   # Then attach payment method
   payment_method = stripe.PaymentMethod.attach(
       "pm_1234567890",
       customer=customer.id,
   )
   ```

💡 Working Example (curl):
   ```bash
   curl https://api.stripe.com/v1/customers \
     -u sk_test_4eC39HqLyjWDarjtT1zdp7dc: \
     -d email="jenny.rosen@example.com" \
     -d name="Jenny Rosen" \
     -d "metadata[order_id]"=6735
   ```

⚠️ Important Notes:
   - Customer IDs are prefixed with "cus_"
   - Customers can have multiple payment methods
   - Use `default_payment_method` to set which one is charged
   - Deleting a customer cancels all subscriptions
   - See "Testing" docs for test email addresses

🔗 Related Documentation:
   - Update a customer: https://stripe.com/docs/api/customers/update
   - List customers: https://stripe.com/docs/api/customers/list  
   - Payment Methods: https://stripe.com/docs/api/payment_methods
   - Subscriptions: https://stripe.com/docs/billing/subscriptions/creating

📚 Guides & Tutorials:
   - Save payment details: https://stripe.com/docs/payments/save-during-payment
   - Customer portal: https://stripe.com/docs/billing/subscriptions/customer-portal
   - Best practices: https://stripe.com/docs/payments/best-practices
```

### Tool 2: `api_examples` (Code Examples)

**Purpose:** Find real-world code examples from multiple sources

```python
api_examples(
    api_name="stripe",
    operation="create subscription with trial",
    language="python",  # optional
    reasoning="Need working example for trial period implementation"
)
```

**What it does:**
1. **Search official docs** for examples
2. **Search GitHub** for real implementations  
3. **Search Stack Overflow** for working solutions
4. **Rank by quality** (stars, votes, recency)
5. **Extract code snippets** with context

**Example output:**
```
Code Examples: Stripe - Create Subscription with Trial
════════════════════════════════════════════════════════════════════

📖 Official Documentation Examples
────────────────────────────────────────────────────────────────────

Example 1: Basic trial period (from Stripe Docs)
   ```python
   subscription = stripe.Subscription.create(
       customer="cus_Na6dX7aXxi11N4",
       items=[{"price": "price_1MowQVLkdIwHu7ixraBm864y"}],
       trial_period_days=14,
   )
   ```
   Source: https://stripe.com/docs/billing/subscriptions/trials

Example 2: Trial end date (from Stripe Docs)
   ```python
   import time
   
   # Trial ends on a specific date
   trial_end = int(time.time()) + (30 * 24 * 60 * 60)  # 30 days
   
   subscription = stripe.Subscription.create(
       customer="cus_Na6dX7aXxi11N4",
       items=[{"price": "price_1MowQVLkdIwHu7ixraBm864y"}],
       trial_end=trial_end,
   )
   ```
   Source: https://stripe.com/docs/billing/subscriptions/trials

💻 GitHub Examples (Real Implementations)
────────────────────────────────────────────────────────────────────

Example 3: Production implementation (⭐ 2.3k stars)
   Repository: https://github.com/example/saas-boilerplate
   
   ```python
   def create_trial_subscription(user, plan_id):
       """Create a subscription with a 14-day trial period."""
       try:
           # Create customer if doesn't exist
           if not user.stripe_customer_id:
               customer = stripe.Customer.create(
                   email=user.email,
                   metadata={'user_id': str(user.id)}
               )
               user.stripe_customer_id = customer.id
               user.save()
           
           # Create subscription with trial
           subscription = stripe.Subscription.create(
               customer=user.stripe_customer_id,
               items=[{'price': plan_id}],
               trial_period_days=14,
               payment_behavior='default_incomplete',
               payment_settings={
                   'save_default_payment_method': 'on_subscription'
               },
               expand=['latest_invoice.payment_intent']
           )
           
           return {
               'subscription_id': subscription.id,
               'client_secret': subscription.latest_invoice.payment_intent.client_secret
           }
       except stripe.error.StripeError as e:
           logger.error(f"Stripe error: {str(e)}")
           raise
   ```
   
   Notes from code:
   - Uses `payment_behavior='default_incomplete'` to collect payment method during trial
   - Saves payment method for when trial ends
   - Expands invoice to get client_secret for frontend
   - Proper error handling

💬 Stack Overflow Solutions
────────────────────────────────────────────────────────────────────

Example 4: Trial without credit card (✓ Accepted, 156 votes)
   Question: "How to create Stripe subscription trial without requiring credit card?"
   Source: https://stackoverflow.com/questions/12345678
   
   ```python
   # Option 1: Use trial_end instead of trial_period_days
   # and don't require payment method upfront
   subscription = stripe.Subscription.create(
       customer=customer_id,
       items=[{"price": price_id}],
       trial_end=trial_end_timestamp,
       # Don't pass payment_method or default_payment_method
   )
   
   # Option 2: Use billing_cycle_anchor to delay first charge
   subscription = stripe.Subscription.create(
       customer=customer_id,
       items=[{"price": price_id}],
       billing_cycle_anchor=trial_end_timestamp,
       proration_behavior='none'
   )
   ```
   
   Important: After trial, user must add payment method before charge attempt.
   Use webhooks to detect `invoice.payment_failed` and pause subscription.

🎯 Best Practices (from examples):
   1. Always use `payment_behavior='default_incomplete'` for trials
   2. Collect payment method during trial to reduce churn
   3. Use webhooks to handle trial ending scenarios
   4. Store subscription ID in your database immediately
   5. Set metadata to link back to your user records

⚠️ Common Pitfalls (from Stack Overflow):
   1. Not handling trial_end = 'now' for immediate charge
   2. Forgetting to expand invoice.payment_intent
   3. Missing webhook handlers for subscription.trial_will_end
   4. Not validating payment method before trial ends
```

### Tool 3: `api_quickstart` (Getting Started Guide)

**Purpose:** Get the quickstart/getting started guide for an API

```python
api_quickstart(
    api_name="stripe",
    use_case="accept payments",  # optional: "webhooks", "subscriptions", etc.
    language="python",  # optional
    reasoning="First time integration, need setup guide"
)
```

**What it does:**
1. **Find quickstart docs** - Getting started, tutorials, guides
2. **Extract setup steps** - Installation, configuration, first API call
3. **Include authentication setup** - API keys, OAuth, etc.
4. **Show "Hello World" example** - Simplest possible working code
5. **Link to next steps** - Where to go after basics

## Implementation Strategy

### Phase 1: Core Documentation Search ✅ START HERE

Build `api_docs` tool:
- Smart API documentation URL detection
- Site-specific search (`site:docs.stripe.com create customer`)
- Crawl top 2-3 results
- Extract and format content
- Preserve code examples
- Find related pages

**No OpenAPI dependency** - works even if spec doesn't exist!

### Phase 2: Example Aggregation

Build `api_examples` tool:
- Search official docs
- Search GitHub code
- Search Stack Overflow
- Rank and deduplicate
- Extract snippets with context

### Phase 3: Quickstart Guide

Build `api_quickstart` tool:
- Find getting started pages
- Extract step-by-step instructions
- Format as actionable guide

## How It Finds Documentation

### Smart URL Detection

```python
class APIDocsDetector:
    """Intelligently find API documentation."""
    
    PATTERNS = {
        # Official doc sites
        'docs': [
            'https://docs.{api}.com',
            'https://{api}.com/docs',
            'https://developers.{api}.com',
            'https://developer.{api}.com',
            'https://{api}.com/documentation',
            'https://api.{api}.com/docs',
        ],
        
        # Known APIs with custom domains
        'known_apis': {
            'stripe': 'https://stripe.com/docs/api',
            'github': 'https://docs.github.com/rest',
            'openai': 'https://platform.openai.com/docs/api-reference',
            'anthropic': 'https://docs.anthropic.com',
            'twilio': 'https://www.twilio.com/docs/usage/api',
            'sendgrid': 'https://docs.sendgrid.com/api-reference',
            'slack': 'https://api.slack.com/methods',
            'discord': 'https://discord.com/developers/docs/reference',
            'aws': 'https://docs.aws.amazon.com/',
            'google': 'https://developers.google.com/',
        }
    }
    
    async def find_docs_url(self, api_name: str) -> str:
        """Find the official documentation URL."""
        api_lower = api_name.lower()
        
        # Check known APIs first
        if api_lower in self.PATTERNS['known_apis']:
            return self.PATTERNS['known_apis'][api_lower]
        
        # Try common patterns
        for pattern in self.PATTERNS['docs']:
            url = pattern.format(api=api_lower)
            if await self._is_valid_docs_site(url):
                return url
        
        # Fallback: Search for official docs
        results = await searcher.search(
            f"{api_name} API official documentation",
            category="general",
            max_results=5
        )
        
        # Filter for official-looking URLs
        for result in results:
            if any(indicator in result.url for indicator in ['docs', 'developer', 'api']):
                return result.url
        
        return None
```

### Content Extraction

```python
class APIDocsExtractor:
    """Extract useful content from API documentation."""
    
    async def extract_endpoint_docs(
        self,
        docs_url: str,
        topic: str
    ) -> dict:
        """Extract documentation for a specific topic/endpoint."""
        
        # Search within the docs site
        search_query = f"site:{docs_url} {topic}"
        results = await searcher.search(search_query, max_results=3)
        
        if not results:
            # Fallback: Try common URL patterns
            results = await self._try_common_paths(docs_url, topic)
        
        # Crawl top results
        docs_content = []
        for result in results[:2]:  # Top 2 for completeness
            content = await crawler_client.fetch(result.url, max_chars=12000)
            docs_content.append({
                'url': result.url,
                'title': result.title,
                'content': content
            })
        
        # Extract structured information
        return {
            'overview': self._extract_overview(docs_content),
            'parameters': self._extract_parameters(docs_content),
            'examples': self._extract_examples(docs_content),
            'related_links': self._extract_links(docs_content),
            'notes': self._extract_notes(docs_content),
        }
    
    def _extract_examples(self, docs_content: list) -> list:
        """Extract code examples from documentation."""
        examples = []
        
        for doc in docs_content:
            content = doc['content']
            
            # Find code blocks with language hints
            code_blocks = re.findall(
                r'```(\w+)\n(.*?)```',
                content,
                re.DOTALL
            )
            
            # Also look for <code> or <pre> tags
            # Handle syntax highlighting classes
            
            for lang, code in code_blocks:
                examples.append({
                    'language': lang,
                    'code': code.strip(),
                    'source': doc['url']
                })
        
        return examples
```

## Why This Approach is Better

### Comparison: Spec-First vs Docs-First

| Aspect | OpenAPI Spec | Documentation-First |
|--------|--------------|---------------------|
| Coverage | Often incomplete | Usually comprehensive |
| Quality | Auto-generated, terse | Human-written, explanatory |
| Examples | Minimal/trivial | Real-world, contextual |
| Best practices | Missing | Included |
| Gotchas | Not mentioned | Highlighted |
| Use cases | Not covered | Common patterns shown |
| Updates | Often outdated | Usually current |
| Context | None | Rich explanations |

### Real-World Example

**OpenAPI spec for Stripe customer creation:**
```json
{
  "parameters": {
    "email": {"type": "string"},
    "name": {"type": "string"},
    "metadata": {"type": "object"}
  }
}
```

**Actual documentation:**
```
email: The customer's email address. This is shown in receipts 
       and used for fraud prevention. Best practice: Always collect.

name: The customer's full name. Shown in the Dashboard and receipts.

metadata: Key-value pairs (max 50 keys, key names ≤ 40 chars, 
          values ≤ 500 chars). Useful for storing IDs from your system.
          Example: {"user_id": "12345", "plan": "premium"}
```

**Huge difference in usefulness!**

## Success Criteria

1. ✅ Can find official docs for top 20 APIs
2. ✅ Can search within API docs for specific topics
3. ✅ Can extract and format endpoint documentation
4. ✅ Can preserve code examples from docs
5. ✅ Can find related documentation pages
6. ✅ Can handle APIs without OpenAPI specs
7. ✅ Response time < 5 seconds
8. ✅ Works for APIs you've never heard of (generic detection)

## Estimated Value

- **Daily Use:** 3-5 times/day
- **Time Saved:** 5-10 minutes per lookup
- **Quality:** Much better than spec-only approach
- **Coverage:** Works for more APIs (many don't have good specs)

---

**This is the right approach!** Documentation-first gives you what you actually need to integrate APIs successfully, not just the technical schema.
