# FD Open Bench - User Guide

Complete guide to the FD Open Bench Agent Benchmark Platform.

## Table of Contents

1. [Introduction](#introduction)
2. [Quick Start](#quick-start)
3. [Core Concepts](#core-concepts)
4. [Working with Agents](#working-with-agents)
5. [Creating Test Datasets](#creating-test-datasets)
6. [Creating Benchmarks](#creating-benchmarks)
7. [Running Batch Evaluations](#running-batch-evaluations)
8. [Reading the Leaderboard](#reading-the-leaderboard)
9. [Business Metrics Explained](#business-metrics-explained)
10. [Best Practices](#best-practices)

---

## Introduction

FD Open Bench helps small teams answer one question: **which agent should we
ship?** It compares agents on the same benchmark and reports both:

- **Technical quality**: success rate, per-metric scores (avg/stddev)
- **Business value**: cost per successful task, ROI, human replacement ratio,
  time cost

Everything runs locally: a FastAPI backend (SQLite), a React web UI, and an
MCP server that drives the same API from the terminal or Claude Desktop.

---

## Quick Start

### Step 1: Start the stack

```bash
./start.sh        # backend on :8999, frontend on :3118
```

No login required by default. (Set `FD_BENCH_API_TOKEN` on the backend to
require a bearer token; empty = open.)

### Step 2: Open the UI

Navigate to `http://localhost:3118` — you land on the **Leaderboard**.

### Step 3: Your first comparison

1. **Datasets** → create a dataset, import goldens (test cases)
2. **Benchmarks** → create a benchmark on that dataset
3. Benchmark detail → **Run New Batch** → select 2+ agents → run
4. **Leaderboard** → pick the benchmark → see the comparison table

The same flow works from the CLI:

```bash
fd-bench run-benchmark --benchmark paybot_v2 --agents paybot,gpt4o-bot
fd-bench leaderboard --benchmark paybot_v2
fd-bench report <run_id> --format markdown
```

---

## Core Concepts

### Agent

An AI system you want to evaluate: a customer-support bot, a coding assistant,
etc. Each agent has:

- **Adapter type**: how it executes (OpenAI-compatible, HTTP, custom)
- **Configuration**: model settings, tools, prompts
- **Pricing config**: token/time costs used for business metrics

### Dataset & Golden

A dataset is a set of test cases (**goldens**). Each golden has:

- **Input**: what to send to the agent
- **Expected output** (optional): ground truth for comparison
- **Business value** (optional): $ value if this task succeeds — drives ROI
- **Human cost** (optional): $ cost for a human to do this task once — drives
  the human-replacement ratio
- **Human minutes** (optional): time a human needs for this task

The three business fields are what unlock the business layer. Fill them in per
golden when you import; missing values are skipped (and counted), never
treated as zero.

### Benchmark

A benchmark pins down **how** a dataset is scored and valued:

- **Dataset**: which goldens to run
- **Metric suite**: which metrics to compute (accuracy, relevance, coherence,
  completeness, custom)
- **Value formula**: how per-task business value is computed from scores.
  Default: `business_value * success_score`. Available variables:
  `business_value`, `success_score`, metric scores; operators `+ - * /`,
  comparisons, `min/max/abs/round`. Unsafe expressions are rejected (AST
  whitelist, no attribute access, no imports).
- **Time value rate** ($/hour): converts agent latency into a dollar cost

> **Comparisons only ever happen within one benchmark.** Metric suites, value
> formulas, and dataset difficulty differ across benchmarks, so cross-benchmark
> "who's better" is meaningless by design.

### Batch & Evaluation Run

One **batch** = N agents × 1 benchmark. Each agent gets its own **evaluation
run** sharing the same `batch_id`; runs execute concurrently in the background
(semaphore-limited, default 2). A run produces one result per golden.

---

## Working with Agents

### Create an Agent

From the web UI: **Agents** → **+ Create Agent**, fill in:

- **Name**: unique identifier
- **Adapter Type**: e.g. `openai`, `http`
- **Configuration**: JSON with model settings

Example OpenAI-compatible configuration:

```json
{
  "model": "gpt-4o",
  "temperature": 0.7,
  "max_tokens": 1000,
  "system_prompt": "You are a helpful customer service assistant."
}
```

### Configure Pricing

Accurate pricing = accurate business metrics. Example token-based pricing:

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

---

## Creating Test Datasets

### Import Goldens

**Datasets** → dataset detail → **Import Goldens** accepts JSON with the
business fields:

```json
[
  {
    "input": "Find cheapest flight from NYC to London next week",
    "expected_tools": ["search_flights"],
    "business_value": 50.0,
    "human_cost": 12.0,
    "human_minutes": 20
  },
  {
    "input": "My order #12345 hasn't arrived yet",
    "expected_output": "Track order status and explain delay",
    "business_value": 25.0,
    "human_cost": 6.0,
    "human_minutes": 10
  }
]
```

Fields may be omitted — the leaderboard will show "需人工数据" for metrics that
can't be computed rather than fabricating zeros.

---

## Creating Benchmarks

**Benchmarks** → create form:

- **Name / description**
- **Dataset**: pick the goldens to run
- **Metric suite**: check the metrics to compute
- **Value formula**: e.g. `business_value * success_score`, or
  `business_value * min(1, success_score / 0.8)` to cap credit at 0.8
- **Time value rate**: your $/hour valuation of agent time (e.g. `50`)

The benchmark detail page shows the config, the goldens (with business
fields), batch history, and the **Run New Batch** entry point.

---

## Running Batch Evaluations

From benchmark detail → **Run New Batch**:

1. Check the agents to compare
2. Submit — this creates one run per agent under a shared `batch_id`
3. You land on the batch page (`/runs/:batchId`) with live progress per agent

From the CLI:

```bash
fd-bench run-benchmark --benchmark paybot_v2 --agents paybot,gpt4o-bot
fd-bench raw GET /api/v1/batches/<batch_id>     # poll progress
```

Runs execute concurrently (default 2 at a time) in the background.

---

## Reading the Leaderboard

The home page (`/`) is the leaderboard. Pick a benchmark; the table shows one
row per agent that has runs on it:

| Column | Meaning |
|--------|---------|
| Success Rate | succeeded tasks / total tasks |
| Avg Score | mean ± stddev across metric scores |
| Cost per Success | total cost / successful tasks (null if no successes) |
| ROI | (business value − cost − time cost) / (cost + time cost) |
| vs Human | cost per success / avg human cost — **green < 1× = cheaper than human** |
| Time Cost | total latency (s) × time value rate / 3600 |

Sort by any business column. Click through to batch/run detail for per-golden
results and traces. Cells that can't be computed show a hint ("补全人工成本数
据后可用") instead of a fake zero.

---

## Business Metrics Explained

```
cost_per_success  = total_cost / success_count          (null at 0 successes)
human_replacement = cost_per_success / avg(human_cost)  (over goldens that have it)
time_cost         = total_latency_s × time_value_rate / 3600
net_value         = total_business_value − total_cost − time_cost
roi               = net_value / (total_cost + time_cost)
```

- `total_business_value` sums the benchmark's **value formula** evaluated per
  golden (formula errors fall back to `business_value * success_score` and are
  recorded in metadata as `formula_error`).
- Goldens missing `human_cost` are skipped from the human-cost average and
  counted — a missing average yields a null `human_replacement`, not zero.
- The `export_report` MCP tool / `fd-bench report` includes a **Business
  Conclusion** section: recommended agent, reasons, and data-gap hints.

---

## Best Practices

### Dataset Design

- Cover edge cases: missing parameters, ambiguous requests, error conditions
- Fill `business_value` / `human_cost` / `human_minutes` per golden — without
  them the business layer stays empty
- Balance high-value scenarios with common ones

### Benchmark Hygiene

- One benchmark per decision ("which support bot to ship"), not per experiment
- Keep the metric suite stable once you start comparing — changing it
  mid-stream makes old runs incomparable
- Write the value formula to match how your business actually counts value

### Cost Optimization

- Track which prompts consume the most tokens
- Use smaller models where quality allows; compare them on the same benchmark
  to prove it
- Re-run batches after agent changes; the leaderboard aggregates all runs per
  agent on the benchmark

---

## Troubleshooting

**Evaluation hangs**
- Cause: agent not returning a response
- Solution: check timeout settings, verify agent health

**Business columns empty**
- Cause: goldens lack `business_value` / `human_cost`
- Solution: re-import goldens with the business fields filled

**All runs fail immediately**
- Cause: agent config missing/invalid (no real model behind the adapter)
- Solution: verify the agent's adapter config; test with a direct API call

---

*This guide reflects the current benchmark-centric workflow.*
