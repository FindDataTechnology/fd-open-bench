# FD Open Bench - User Guide

Complete guide to using the FD Open Bench Agent Performance Evaluation Platform.

## Table of Contents

1. [Introduction](#introduction)
2. [Quick Start](#quick-start)
3. [Core Concepts](#core-concepts)
4. [Working with Agents](#working-with-agents)
5. [Creating Test Datasets](#creating-test-datasets)
6. [Configuring Evaluators](#configuring-evaluators)
7. [Running Evaluations](#running-evaluations)
8. [Analyzing Results](#analyzing-results)
9. [Cost Analysis](#cost-analysis)
10. [Best Practices](#best-practices)

---

## Introduction

FD Open Bench helps you evaluate AI agents by providing:

- **Multi-dimensional evaluation**: Technical quality + business value
- **Custom validators**: Regex, JSON schema, keywords, format checks
- **LLM judges**: DeepEval metrics and custom prompts
- **Domain executors**: SQL, API, code execution validation
- **Business modeling**: Cost tracking vs. ROI calculation
- **Full trace capture**: Token usage, timing, span hierarchy

---

## Quick Start

### Step 1: Install & Run

```bash
# Clone repository
git clone <your-repo-url>
cd fd-open-bench

# Configure environment
cp .env.example .env
# Edit .env with your database credentials and API keys

# Start services
docker-compose up -d

# Run migrations
docker-compose exec backend alembic upgrade head
```

### Step 2: Access Web UI

Open browser and navigate to `http://localhost:3000`

Login with default credentials (configure in `.env`).

---

## Core Concepts

### Agent

An agent is an AI system you want to evaluate. Examples:
- Customer support chatbot
- Sales outreach assistant
- Data analysis tool
- Code generation bot

Each agent has:
- **Adapter type**: How it executes (OpenAI, LangChain, custom)
- **Configuration**: Model settings, tools, prompts
- **Pricing**: Token costs, time-based costs

### Dataset (Test Cases)

A dataset contains multiple test cases (Goldens) used for batch evaluation.

Each Golden includes:
- **Input**: What to send to the agent
- **Expected output**: Optional ground truth for comparison
- **Expected tools**: Optional list of expected function calls
- **Business value**: Expected value if task succeeds ($ amount)

### Evaluator

An evaluator checks specific aspects of agent output. Three types:

1. **Validators**: Fast, deterministic checks (regex, JSON schema, keywords)
2. **LLM Judges**: Flexible, expensive evaluations using LLMs
3. **Executors**: Ground-truth validation (SQL queries, API calls, code execution)

### Evaluation Run

An evaluation run processes one agent against one dataset with configured evaluators.

Outputs:
- Individual results per test case
- Aggregated scores across all test cases
- Cost breakdown (tokens, time, infrastructure)
- Business value delivered and ROI

---

## Working with Agents

### Create an Agent

From the web UI:
1. Navigate to **Agents** → Click **+ Create Agent**
2. Fill in:
   - **Name**: Unique identifier
   - **Description**: Brief explanation
   - **Adapter Type**: Select from dropdown (OpenAI/LangChain/Custom)
   - **Configuration**: JSON object with model settings

Example OpenAI configuration:
```json
{
  "model": "gpt-4o",
  "temperature": 0.7,
  "max_tokens": 1000,
  "system_prompt": "You are a helpful customer service assistant."
}
```

### Configure Pricing

For each agent, set pricing to track costs accurately:

**Token-based pricing:**
```json
{
  "type": "tokens",
  "pricing": {
    "gpt-4o": {
      "input_per_1k": 0.0025,
      "output_per_1k": 0.01
    }
  }
}
```

**Time-based pricing:**
```json
{
  "type": "per_minute",
  "rate": 0.10  // $0.10 per minute
}
```

### View Agent Details

Click on any agent to view:
- Full configuration
- Evaluation history
- Performance trends
- Associated business model

---

## Creating Test Datasets

### Import Goldens via UI

1. Navigate to **Datasets** → **+ Create Dataset**
2. Enter name and description
3. Go to dataset detail page
4. Click **Import Goldens**

Supported formats:

**Single golden:**
```json
{
  "input": "Book a flight from NYC to Paris for March 15",
  "expected_output": "Flight XYZ booked for $450",
  "business_value": 50.0
}
```

**Bulk import (multiple):**
```json
[
  {
    "input": "...",
    "expected_output": "...",
    "business_value": ...
  },
  {...}
]
```

### Add Single Golden

From dataset detail page:
1. Click **Add Golden**
2. Fill fields:
   - **Input**: The prompt/question to send to agent
   - **Expected Output**: Acceptable response (optional)
   - **Business Value**: Revenue/value if task succeeds ($)
   - **Metadata**: Additional context (tags, category)

### Example Datasets

**Flight Booking:**
```json
[
  {
    "input": "Find cheapest flight from NYC to London next week",
    "expected_tools": ["search_flights"],
    "business_value": 50.0
  },
  {
    "input": "Book round-trip flight NYC-London April 1-8",
    "expected_tools": ["search_flights", "book_flight"],
    "business_value": 100.0
  }
]
```

**Customer Support:**
```json
[
  {
    "input": "My order #12345 hasn't arrived yet",
    "expected_output": "Track order status and explain delay",
    "business_value": 25.0
  },
  {
    "input": "I want to return item from order #12345",
    "expected_tools": ["lookup_order", "initiate_return"],
    "business_value": 10.0
  }
]
```

---

## Configuring Evaluators

### Validator Examples

**Email Format Check:**
```json
{
  "name": "email_validator",
  "type": "validator",
  "config": {
    "pattern": "[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}",
    "must_match": true
  }
}
```

**Required Keywords:**
```json
{
  "name": "support_phrases",
  "type": "validator",
  "config": {
    "keywords": ["apologize", "helpful", "understand"],
    "mode": "any"
  }
}
```

**JSON Schema Validation:**
```json
{
  "name": "response_schema",
  "type": "validator",
  "config": {
    "schema": {
      "type": "object",
      "required": ["status", "message"],
      "properties": {
        "status": {"enum": ["success", "error"]},
        "message": {"type": "string"}
      }
    }
  }
}
```

### LLM Judge Examples

**Helpfulness Rating:**
```json
{
  "name": "helpfulness_judge",
  "type": "llm_judge",
  "config": {
    "prompt": "Rate this response on helpfulness from 0-10:\n\nQuestion: {{input}}\nResponse: {{output}}\n\nReturn JSON: {\"score\": N, \"reason\": \"...\"}",
    "score_range": [0, 10],
    "threshold": 7,
    "model": "gpt-4o"
  }
}
```

**DeepEval Metric:**
```json
{
  "name": "answer_relevancy",
  "type": "llm_judge",
  "config": {
    "metric": "answer_relevancy",
    "threshold": 0.7,
    "model": "gpt-4o"
  }
}
```

### Executor Examples

**SQL Query Validator:**
```json
{
  "name": "sql_correctness",
  "type": "executor",
  "config": {
    "connection": "postgresql://...",
    "validation": {
      "match_mode": "exact",
      "expected_results": [{"id": 1, "name": "Alice"}]
    },
    "read_only": true
  }
}
```

**API Response Validator:**
```json
{
  "name": "api_response",
  "type": "executor",
  "config": {
    "validation": {
      "status_code": 200,
      "response_schema": {
        "type": "object",
        "required": ["user_id", "status"]
      }
    }
  }
}
```

### Testing Evaluators

Before using an evaluator in an evaluation run, test it:

1. Navigate to **Evaluators**
2. Click **Create Evaluator** (or select existing)
3. Click **Test** button
4. Enter sample input/output
5. Review result: score, passed, reason

---

## Running Evaluations

### Start New Evaluation

1. Navigate to **Evaluations** → **+ New Evaluation**
2. Select:
   - **Agent**: Which agent to evaluate
   - **Dataset**: Which test cases to use
   - **Evaluators**: List of evaluators to apply
3. Click **Create**

### Monitor Progress

From the dashboard:
- See active evaluations with live progress
- Watch completion count increase
- Monitor current cost accumulation

From evaluation detail page:
- Real-time progress bar
- Individual test case results
- Trace visualization
- Cost breakdown

### Cancel Evaluation

If you need to stop an evaluation:

1. Go to evaluation detail page
2. Click **Cancel**
3. Confirm cancellation

Note: Completed tests are preserved; only pending tests are cancelled.

### Retry Failed Tests

After an evaluation completes:

1. Go to evaluation detail page
2. Click **Retry Failed**
3. System re-runs only failed test cases
4. Merges new results with original

---

## Analyzing Results

### Viewing Individual Results

Navigate to an evaluation run:

**Summary view shows:**
- Total cost (token + time + infrastructure)
- Success rate
- Average score
- ROI calculation

**Per-test-case details show:**
- Input sent to agent
- Agent output generated
- Scores from each evaluator
- Token usage breakdown
- Execution time
- Cost for that test case

### Trace Visualization

For each test case, view detailed traces:

**Tree view:**
- Hierarchical display of spans
- Expand/collapse nested operations
- Color-coded status (green=success, red=error)

**Timeline view:**
- Gantt chart showing parallel execution
- Identify bottlenecks in execution flow

**Trace details include:**
- Exact input/output for each step
- Token counts per LLM call
- Tool execution arguments and results
- Timing for each component

### Exporting Results

**CSV Export:**
1. Go to evaluation detail page
2. Click **Export CSV**
3. Download file with:
   - All test case inputs/outputs
   - Scores and pass/fail status
   - Costs and timestamps

**PDF Report:**
1. Go to evaluation detail page
2. Click **Export PDF**
3. Receive formatted report with:
   - Executive summary
   - Score distributions
   - Charts and graphs
   - Recommendations

---

## Cost Analysis

### Understanding Cost Components

Total cost = **Token Cost** + **Time Cost** + **Infrastructure Cost**

**Token Cost:**
- Input tokens × input_price
- Output tokens × output_price
- Varies by model (gpt-4, claude, etc.)

**Time Cost:**
- Per-minute or per-hour pricing
- Based on total execution duration
- Useful for long-running agents

**Infrastructure Cost:**
- Server costs (if self-hosted)
- External API calls (flight search, etc.)
- Database operations

### Using Cost Analyzer

Navigate to **Cost Analyzer**:

1. Select agent and date range
2. View **Cost Breakdown** pie chart:
   - Percentage from each cost type
   - Dollar amounts

3. Review **ROI Trends** line chart:
   - Historical ROI over selected period
   - Identify improvement or degradation

4. Examine **Daily Costs** bar chart:
   - Stack of token/time/infra costs by day
   - Spot anomalies or spikes

### Calculating ROI

ROI formula:
```
ROI = (Business Value - Total Cost) / Total Cost
```

**Example interpretation:**
- ROI of 200% means you earn $3 for every $1 spent
- Negative ROI means costs exceed value
- Break-even at 0% ROI

### Cost Alerts

Configure alerts to monitor spending:

```json
{
  "type": "cost_per_task",
  "threshold": 1.00,  // Alert if > $1/task
  "action": "email"    // Send email notification
}
```

Navigate to agent configuration → **Alerts** tab to set these.

---

## Best Practices

### Testing Strategy

1. **Start small**: Begin with 5-10 test cases
2. **Validate quickly**: Use fast validators first
3. **Add LLM judges**: Once basic quality confirmed
4. **Scale up**: Gradually increase test count
5. **Automate**: Schedule regular evaluations

### Evaluator Selection

**Use validators when:**
- Checking data formats (emails, URLs, dates)
- Validating required fields present
- Enforcing length constraints

**Use LLM judges when:**
- Assessing semantic quality (helpfulness, tone)
- Comparing multiple acceptable answers
- Evaluating creativity or reasoning

**Use executors when:**
- Validating against ground truth (SQL results)
- Testing code correctness (run tests)
- Verifying API contract compliance

### Dataset Design

**Cover edge cases:**
- Missing parameters
- Ambiguous requests
- Error conditions
- Boundary values

**Include business diversity:**
- Different customer segments
- Various price points
- Multiple domains/products

**Balance coverage:**
- High-value scenarios (more weight)
- Common scenarios (representative)
- Rare scenarios (edge cases)

### Cost Optimization

**Monitor token usage:**
- Track which prompts consume most tokens
- Optimize system prompts for conciseness
- Use smaller models where appropriate

**Review execution patterns:**
- Identify redundant LLM calls
- Cache repeated responses
- Parallelize independent operations

**Set budgets:**
- Define monthly spend limits
- Enable cost alerts at 80% threshold
- Review regularly and adjust pricing

### Evaluation Frequency

**Recommended schedule:**
- **New agents**: Daily evaluations during development
- **Stable agents**: Weekly evaluations for regression detection
- **Production changes**: Pre-deployment + post-deployment
- **Business metrics**: Monthly trend analysis

---

## Troubleshooting

### Common Issues

**Issue: Evaluation hangs**
- Cause: Agent not returning response
- Solution: Check timeout settings, verify agent health

**Issue: High costs**
- Cause: Too many LLM calls, inefficient prompts
- Solution: Enable caching, optimize prompts, reduce iteration loops

**Issue: Low scores**
- Cause: Agent quality, inappropriate evaluators
- Solution: Review evaluator thresholds, improve agent prompt

**Issue: Missing trace data**
- Cause: Tracing not enabled in adapter
- Solution: Verify @observe decorators are applied

---

## Next Steps

After completing this guide:
1. Review API documentation at `/docs`
2. Explore code examples in `/examples`
3. Join community forum for support
4. Attend quarterly training sessions

For advanced topics:
- Custom evaluator development
- Multi-agent coordination evaluation
- Production monitoring setup
- Custom integrations

---

*This guide is version 1.0 and reflects the current feature set. Updates will be posted as new capabilities are added.*
