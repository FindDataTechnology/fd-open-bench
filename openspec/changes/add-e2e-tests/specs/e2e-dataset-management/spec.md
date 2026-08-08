## ADDED Requirements

### Requirement: Dataset list page object
The system SHALL provide a dataset list page object with methods for viewing datasets and navigating to dataset details.

#### Scenario: Dataset list page object exists
- **WHEN** dataset list page object is implemented
- **THEN** tests/e2e/pages/datasets-list.page.ts exists
- **AND** page object includes getDatasetList() method
- **AND** page object includes clickDataset() method
- **AND** page object includes clickCreateDataset() method

### Requirement: Dataset detail page object
The system SHALL provide a dataset detail page object with methods for viewing dataset details and goldens.

#### Scenario: Dataset detail page object exists
- **WHEN** dataset detail page object is implemented
- **THEN** tests/e2e/pages/dataset-detail.page.ts exists
- **AND** page object includes getDatasetName() method
- **AND** page object includes getGoldenList() method
- **AND** page object includes clickImportGoldens() method

### Requirement: Create dataset form page object
The system SHALL provide a create dataset form page object with methods for filling out the form.

#### Scenario: Create dataset form page object exists
- **WHEN** create dataset form page object is implemented
- **THEN** tests/e2e/pages/dataset-create.page.ts exists
- **AND** page object includes enterName() method
- **AND** page object includes enterDescription() method
- **AND** page object includes clickSubmit() method

### Requirement: View dataset list
The system SHALL test viewing the list of datasets.

#### Scenario: User views dataset list
- **WHEN** user is logged in
- **AND** user navigates to /datasets
- **THEN** dataset list page is displayed
- **AND** user sees list of datasets
- **AND** each dataset shows name, description, and golden count

### Requirement: Create new dataset
The system SHALL test creating a new dataset through the web UI.

#### Scenario: User creates new dataset
- **WHEN** user navigates to /datasets
- **AND** user clicks "Create Dataset" button
- **AND** user enters name "Test Dataset"
- **AND** user enters description "Test description"
- **AND** user clicks submit button
- **THEN** dataset is created successfully
- **AND** user is redirected to dataset detail page
- **AND** dataset details are displayed correctly

### Requirement: View dataset details
The system SHALL test viewing dataset details.

#### Scenario: User views dataset details
- **WHEN** user is on dataset list page
- **AND** user clicks on a dataset
- **THEN** user is redirected to dataset detail page
- **AND** dataset name is displayed
- **AND** dataset description is displayed
- **AND** golden count is displayed

### Requirement: View golden list
The system SHALL test viewing the list of goldens in a dataset.

#### Scenario: User views golden list
- **WHEN** user is on dataset detail page
- **THEN** golden list is displayed
- **AND** each golden shows input, expected output, and business value
- **AND** golden count matches dataset metadata

### Requirement: Import goldens from JSON
The system SHALL test importing goldens from a JSON file.

#### Scenario: User imports goldens from JSON
- **WHEN** user is on dataset detail page
- **AND** user clicks "Import Goldens" button
- **AND** user uploads a JSON file with goldens
- **AND** user clicks "Import" button
- **THEN** goldens are imported successfully
- **AND** golden list is updated
- **AND** golden count is updated

### Requirement: Import goldens validation
The system SHALL test validation when importing invalid JSON.

#### Scenario: User imports invalid JSON
- **WHEN** user is on dataset detail page
- **AND** user uploads an invalid JSON file
- **AND** user clicks "Import" button
- **THEN** error message "Invalid JSON format" is displayed
- **AND** no goldens are imported

### Requirement: Edit dataset
The system SHALL test editing an existing dataset.

#### Scenario: User edits dataset
- **WHEN** user is on dataset detail page
- **AND** user clicks "Edit" button
- **AND** user changes name to "Updated Dataset"
- **AND** user clicks "Save" button
- **THEN** dataset is updated successfully
- **AND** updated name is displayed
- **AND** success message is shown

### Requirement: Delete dataset
The system SHALL test deleting a dataset.

#### Scenario: User deletes dataset
- **WHEN** user is on dataset detail page
- **AND** user clicks "Delete" button
- **AND** user confirms deletion
- **THEN** dataset is deleted successfully
- **AND** all goldens in dataset are deleted
- **AND** user is redirected to dataset list page
- **AND** deleted dataset is no longer in the list

### Requirement: Create dataset validation
The system SHALL test form validation when creating a dataset.

#### Scenario: User submits empty dataset form
- **WHEN** user is on create dataset page
- **AND** user clicks submit without filling form
- **THEN** form shows validation errors
- **AND** name field shows "Name is required"
- **AND** form is not submitted

### Requirement: Duplicate dataset name validation
The system SHALL test validation for duplicate dataset names.

#### Scenario: User creates dataset with duplicate name
- **WHEN** user creates dataset with name "Existing Dataset"
- **AND** another dataset with name "Existing Dataset" already exists
- **THEN** error message "Dataset with this name already exists" is displayed
- **AND** dataset is not created
