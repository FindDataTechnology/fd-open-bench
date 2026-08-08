# batch-evaluation-system Specification

## Purpose
TBD - created by archiving change fd-open-bench. Update Purpose after archive.
## Requirements
### Requirement: System supports queue-based batch evaluation
The system SHALL support queue-based batch evaluation using Redis as the message broker and Celery as the task queue. Users SHALL be able to submit batch evaluation jobs that are queued and processed asynchronously. The system SHALL support prioritization (high/medium/low priority queues) and rate limiting (max concurrent evaluations per agent).

#### Scenario: Submit batch evaluation job
- **WHEN** a user submits a batch evaluation job with agent_id="travel-agent", dataset_id="flight-tests" (100 test cases), and evaluators=[task_completion, regex_validator]
- **THEN** the system SHALL create an EvaluationRun record with status="pending", enqueue 100 Celery tasks (one per test case), and return a run_id to the user

#### Scenario: Priority queue processing
- **WHEN** there are two evaluation jobs in the queue: job_a with priority="low" and job_b with priority="high"
- **THEN** the system SHALL process job_b's tasks before job_a's tasks

### Requirement: System supports parallel evaluation execution
The system SHALL support parallel execution of evaluation tasks. The system SHALL configure a Celery worker pool with configurable concurrency (default: 4 workers). Each worker SHALL process one test case at a time. The system SHALL respect rate limits for LLM API calls (configurable max_calls_per_minute per model).

#### Scenario: Parallel task execution
- **WHEN** a batch evaluation has 100 test cases and the worker pool has concurrency=4
- **THEN** the system SHALL process up to 4 test cases concurrently, reducing total execution time by ~4× (assuming I/O-bound workload)

#### Scenario: Rate limiting for LLM API calls
- **WHEN** an evaluation run uses an LLM judge with rate_limit=60 calls/minute
- **THEN** the system SHALL throttle LLM API calls to not exceed 60 calls per minute, queuing excess calls

### Requirement: System tracks evaluation progress
The system SHALL track evaluation progress in real-time. The system SHALL update the EvaluationRun record with: tasks_completed (count), tasks_failed (count), current_cost (sum of costs for completed tasks), estimated_time_remaining (based on average task duration), and status (pending/running/completed/failed/partially_completed).

#### Scenario: Progress tracking
- **WHEN** a batch evaluation has 100 test cases, 50 completed, 2 failed, average task duration=10 seconds
- **THEN** the system SHALL update the run with tasks_completed=50, tasks_failed=2, estimated_time_remaining=(50 remaining × 10s) = 500 seconds, and status="running"

#### Scenario: Progress notification via WebSocket
- **WHEN** a batch evaluation is running and the user has the web UI open
- **THEN** the system SHALL push progress updates via WebSocket every 5 seconds, displaying tasks_completed, tasks_failed, current_cost, and estimated_time_remaining

### Requirement: System aggregates results across test cases
The system SHALL aggregate results across all test cases in a batch evaluation. Aggregation SHALL include: average_score, median_score, min_score, max_score, score_distribution (histogram), success_rate (percentage of test cases with score >= threshold), total_cost, average_cost_per_task, total_business_value_delivered, aggregate_roi, and evaluator_breakdown (average score per evaluator).

#### Scenario: Result aggregation
- **WHEN** a batch evaluation completes with 100 test cases, scores ranging from 0.5 to 1.0, average_score=0.82, success_rate=85%
- **THEN** the system SHALL persist the aggregated metrics in the EvaluationRun's results_summary field

### Requirement: System supports evaluation run cancellation
The system SHALL support cancelling a running evaluation run. On cancellation, the system SHALL: revoke pending Celery tasks, allow in-progress tasks to complete (or terminate them if force_cancel=true), mark the run as status="cancelled", and aggregate results from completed tasks.

#### Scenario: Graceful cancellation
- **WHEN** a user cancels a running evaluation run with force_cancel=false
- **THEN** the system SHALL revoke pending tasks, wait for in-progress tasks to complete (up to 60 seconds), mark the run as status="cancelled", and aggregate results from completed tasks

#### Scenario: Force cancellation
- **WHEN** a user cancels a running evaluation run with force_cancel=true
- **THEN** the system SHALL immediately terminate all in-progress tasks, revoke pending tasks, mark the run as status="cancelled", and aggregate results from completed tasks

### Requirement: System supports evaluation run retry
The system SHALL support retrying failed test cases within an evaluation run. On retry, the system SHALL: re-execute only the failed test cases, merge results with existing successful results, and update the run's aggregated metrics.

#### Scenario: Retry failed test cases
- **WHEN** a batch evaluation has 10 failed test cases out of 100, and the user clicks "Retry Failed"
- **THEN** the system SHALL re-execute the 10 failed test cases, merge the new results with the 90 successful results, and update the aggregated metrics

### Requirement: System sends notifications on completion
The system SHALL send notifications when a batch evaluation completes (or fails). Notifications SHALL be sent via: webhook (POST to configured URL with run results), email (to configured recipients with summary), and in-app notification (displayed in the web UI). Notification content SHALL include: run_id, agent_id, status, total_test_cases, success_rate, total_cost, aggregate_roi, and link to detailed results.

#### Scenario: Webhook notification on completion
- **WHEN** a batch evaluation completes and the user has configured a webhook URL
- **THEN** the system SHALL POST a JSON payload to the webhook URL with run summary and results link

#### Scenario: Email notification on failure
- **WHEN** a batch evaluation fails (e.g., agent crashes on all test cases) and the user has configured email notifications
- **THEN** the system SHALL send an email to the configured recipients with failure details and troubleshooting suggestions

### Requirement: System implements durable queueing
The system SHALL implement durable queueing so that evaluation jobs survive backend restarts. Celery tasks SHALL be persisted to Redis with expiration (default: 24 hours). On backend restart, the system SHALL resume processing pending tasks.

#### Scenario: Backend restart during evaluation
- **WHEN** the backend restarts while a batch evaluation is running with 50/100 tasks completed
- **THEN** the system SHALL resume processing the remaining 50 tasks from where it left off, without losing progress

### Requirement: System supports scheduled evaluations
The system SHALL support scheduling evaluation runs to execute at a specific time or on a recurring schedule (cron expression). Scheduled runs SHALL be queued at the scheduled time and executed like normal batch evaluations.

#### Scenario: One-time scheduled evaluation
- **WHEN** a user schedules an evaluation run to execute at "2025-03-20 09:00:00"
- **THEN** the system SHALL queue the evaluation at the scheduled time and execute it

#### Scenario: Recurring evaluation
- **WHEN** a user schedules a recurring evaluation with cron="0 9 * * 1" (every Monday at 9 AM)
- **THEN** the system SHALL queue and execute the evaluation every Monday at 9 AM until the schedule is cancelled

