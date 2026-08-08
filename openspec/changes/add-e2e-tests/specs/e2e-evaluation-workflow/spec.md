## ADDED Requirements

### Requirement: Evaluation list page object
The system SHALL provide an evaluation list page object with methods for viewing evaluations and navigating to evaluation details.

#### Scenario: Evaluation list page object exists
- **WHEN** evaluation list page object is implemented
- **THEN** tests/e2e/pages/evaluations-list.page.ts exists
- **AND** page object includes getEvaluationList() method
- **AND** page object includes clickEvaluation() method
- **AND** page object includes clickCreateEvaluation() method

### Requirement: Evaluation detail page object
The system SHALL provide an evaluation detail page object with methods for viewing evaluation results and traces.

#### Scenario: Evaluation detail page object exists
- **WHEN** evaluation detail page object is implemented
- **THEN** tests/e2e/pages/evaluation-detail.page.ts exists
- **AND** page object includes getEvaluationStatus() method
- **AND** page object includes getResultsList() method
- **AND** page object includes clickViewTrace() method

### Requirement: Create evaluation form page object
The system SHALL provide a create evaluation form page object with methods for selecting agent, dataset, and evaluators.

#### Scenario: Create evaluation form page object exists
- **WHEN** create evaluation form page object is implemented
- **THEN** tests/e2e/pages/evaluation-create.page.ts exists
- **AND** page object includes selectAgent() method
- **AND** page object includes selectDataset() method
- **AND** page object includes selectEvaluators() method
- **AND** page object includes clickSubmit() method

### Requirement: View evaluation list
The system SHALL test viewing the list of evaluations.

#### Scenario: User views evaluation list
- **WHEN** user is logged in
- **AND** user navigates to /evaluations
- **THEN** evaluation list page is displayed
- **AND** user sees list of evaluations
- **AND** each evaluation shows agent, dataset, status, and progress

### Requirement: Create new evaluation
The system SHALL test creating a new evaluation through the web UI.

#### Scenario: User creates new evaluation
- **WHEN** user navigates to /evaluations
- **AND** user clicks "Create Evaluation" button
- **AND** user selects agent "Test Agent"
- **AND** user selects dataset "Test Dataset"
- **AND** user selects evaluators ["validator1", "llm_judge1"]
- **AND** user clicks submit button
- **THEN** evaluation is created successfully
- **AND** user is redirected to evaluation detail page
- **AND** evaluation status is "running"

### Requirement: Monitor evaluation progress
The system SHALL test monitoring evaluation progress in real-time.

#### Scenario: User monitors evaluation progress
- **WHEN** user is on evaluation detail page
- **AND** evaluation is running
- **THEN** progress bar is displayed
- **AND** progress updates in real-time
- **AND** completed count increases
- **AND** current cost is displayed

### Requirement: View evaluation results
The system SHALL test viewing evaluation results after completion.

#### Scenario: User views evaluation results
- **WHEN** evaluation is completed
- **AND** user is on evaluation detail page
- **THEN** results list is displayed
- **AND** each result shows golden, score, and status
- **AND** overall statistics are displayed

### Requirement: View evaluation trace
The system SHALL test viewing trace for a specific evaluation result.

#### Scenario: User views evaluation trace
- **WHEN** user is on evaluation detail page
- **AND** user clicks "View Trace" for a result
- **THEN** trace visualization is displayed
- **AND** trace shows spans in tree view
- **AND** trace shows timing information
- **AND** trace shows token usage

### Requirement: Cancel running evaluation
The system SHALL test cancelling a running evaluation.

#### Scenario: User cancels evaluation
- **WHEN** evaluation is running
- **AND** user clicks "Cancel" button
- **AND** user confirms cancellation
- **THEN** evaluation is cancelled
- **AND** status changes to "cancelled"
- **AND** completed results are preserved

### Requirement: Retry failed evaluation
The system SHALL test retrying a failed evaluation.

#### Scenario: User retries evaluation
- **WHEN** evaluation has failed
- **AND** user clicks "Retry" button
- **THEN** new evaluation is created
- **AND** new evaluation uses same configuration
- **AND** user is redirected to new evaluation

### Requirement: Export evaluation results
The system SHALL test exporting evaluation results.

#### Scenario: User exports results as CSV
- **WHEN** evaluation is completed
- **AND** user clicks "Export CSV" button
- **THEN** CSV file is downloaded
- **AND** CSV contains all evaluation results
- **AND** CSV includes scores and metadata

### Requirement: Evaluation status filtering
The system SHALL test filtering evaluations by status.

#### Scenario: User filters evaluations by status
- **WHEN** user is on evaluation list page
- **AND** user selects status "completed"
- **THEN** only completed evaluations are displayed
- **AND** other evaluations are hidden

### Requirement: Evaluation sorting
The system SHALL test sorting evaluations by different columns.

#### Scenario: User sorts evaluations by date
- **WHEN** user is on evaluation list page
- **AND** user clicks "Date" column header
- **THEN** evaluations are sorted by date
- **AND** sort order toggles between ascending and descending

### Requirement: Evaluation progress WebSocket
The system SHALL test real-time progress updates via WebSocket.

#### Scenario: WebSocket provides progress updates
- **WHEN** evaluation is running
- **AND** user is on evaluation detail page
- **THEN** progress updates are received via WebSocket
- **AND** progress bar updates in real-time
- **AND** no page refresh is needed
