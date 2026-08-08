## ADDED Requirements

### Requirement: Evaluator list page object
The system SHALL provide an evaluator list page object with methods for viewing evaluators and navigating to evaluator details.

#### Scenario: Evaluator list page object exists
- **WHEN** evaluator list page object is implemented
- **THEN** tests/e2e/pages/evaluators-list.page.ts exists
- **AND** page object includes getEvaluatorList() method
- **AND** page object includes clickEvaluator() method
- **AND** page object includes clickCreateEvaluator() method

### Requirement: Evaluator detail page object
The system SHALL provide an evaluator detail page object with methods for viewing and testing evaluators.

#### Scenario: Evaluator detail page object exists
- **WHEN** evaluator detail page object is implemented
- **THEN** tests/e2e/pages/evaluator-detail.page.ts exists
- **AND** page object includes getEvaluatorName() method
- **AND** page object includes getEvaluatorType() method
- **AND** page object includes clickTest() method

### Requirement: Create evaluator form page object
The system SHALL provide a create evaluator form page object with methods for filling out the form.

#### Scenario: Create evaluator form page object exists
- **WHEN** create evaluator form page object is implemented
- **THEN** tests/e2e/pages/evaluator-create.page.ts exists
- **AND** page object includes enterName() method
- **AND** page object includes selectType() method
- **AND** page object includes enterConfig() method
- **AND** page object includes clickSubmit() method

### Requirement: View evaluator list
The system SHALL test viewing the list of evaluators.

#### Scenario: User views evaluator list
- **WHEN** user is logged in
- **AND** user navigates to /evaluators
- **THEN** evaluator list page is displayed
- **AND** user sees list of evaluators
- **AND** each evaluator shows name, type, and description

### Requirement: Create new validator
The system SHALL test creating a new validator evaluator.

#### Scenario: User creates regex validator
- **WHEN** user navigates to /evaluators
- **AND** user clicks "Create Evaluator" button
- **AND** user enters name "Email Validator"
- **AND** user selects type "validator"
- **AND** user enters config with pattern "[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}"
- **AND** user clicks submit button
- **THEN** evaluator is created successfully
- **AND** user is redirected to evaluator detail page

### Requirement: Create new LLM judge
The system SHALL test creating a new LLM judge evaluator.

#### Scenario: User creates custom prompt judge
- **WHEN** user navigates to /evaluators
- **AND** user clicks "Create Evaluator" button
- **AND** user enters name "Helpfulness Judge"
- **AND** user selects type "llm_judge"
- **AND** user enters config with prompt template
- **AND** user clicks submit button
- **THEN** evaluator is created successfully
- **AND** evaluator type is displayed as "llm_judge"

### Requirement: Create new executor
The system SHALL test creating a new executor evaluator.

#### Scenario: User creates SQL executor
- **WHEN** user navigates to /evaluators
- **AND** user clicks "Create Evaluator" button
- **AND** user enters name "SQL Validator"
- **AND** user selects type "executor"
- **AND** user enters config with connection string
- **AND** user clicks submit button
- **THEN** evaluator is created successfully
- **AND** evaluator type is displayed as "executor"

### Requirement: Test evaluator
The system SHALL test testing an evaluator with sample input/output.

#### Scenario: User tests evaluator
- **WHEN** user is on evaluator detail page
- **AND** user clicks "Test" button
- **AND** user enters sample input "test@example.com"
- **AND** user enters sample output "Valid email"
- **AND** user clicks "Run Test" button
- **THEN** test result is displayed
- **AND** score is shown (e.g., 1.0)
- **AND** passed status is shown (true/false)
- **AND** reason is displayed

### Requirement: Edit evaluator
The system SHALL test editing an existing evaluator.

#### Scenario: User edits evaluator
- **WHEN** user is on evaluator detail page
- **AND** user clicks "Edit" button
- **AND** user changes name to "Updated Validator"
- **AND** user clicks "Save" button
- **THEN** evaluator is updated successfully
- **AND** updated name is displayed
- **AND** success message is shown

### Requirement: Delete evaluator
The system SHALL test deleting an evaluator.

#### Scenario: User deletes evaluator
- **WHEN** user is on evaluator detail page
- **AND** user clicks "Delete" button
- **AND** user confirms deletion
- **THEN** evaluator is deleted successfully
- **AND** user is redirected to evaluator list page
- **AND** deleted evaluator is no longer in the list

### Requirement: Evaluator config validation
The system SHALL test validation of evaluator configuration.

#### Scenario: User submits invalid config
- **WHEN** user is on create evaluator page
- **AND** user enters invalid JSON config
- **AND** user clicks submit button
- **THEN** error message "Invalid JSON format" is displayed
- **AND** evaluator is not created

### Requirement: Evaluator type filtering
The system SHALL test filtering evaluators by type.

#### Scenario: User filters evaluators by type
- **WHEN** user is on evaluator list page
- **AND** user selects type "validator"
- **THEN** only validator evaluators are displayed
- **AND** other evaluators are hidden

### Requirement: Evaluator search
The system SHALL test searching for evaluators by name.

#### Scenario: User searches for evaluator
- **WHEN** user is on evaluator list page
- **AND** user enters "Email" in search box
- **THEN** only evaluators with "Email" in name are displayed
- **AND** other evaluators are hidden
