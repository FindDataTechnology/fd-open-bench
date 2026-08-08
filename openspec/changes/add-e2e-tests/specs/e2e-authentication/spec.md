## ADDED Requirements

### Requirement: Login page object
The system SHALL provide a login page object with methods for entering credentials and submitting the login form.

#### Scenario: Login page object exists
- **WHEN** login page object is implemented
- **THEN** tests/e2e/pages/login.page.ts exists
- **AND** page object includes enterEmail() method
- **AND** page object includes enterPassword() method
- **AND** page object includes clickLogin() method
- **AND** page object includes waitForDashboard() method

### Requirement: Successful login flow
The system SHALL test the complete login flow from entering credentials to reaching the dashboard.

#### Scenario: User logs in with valid credentials
- **WHEN** user navigates to /login
- **AND** user enters email "admin@example.com"
- **AND** user enters password "admin123"
- **AND** user clicks login button
- **THEN** user is redirected to /dashboard
- **AND** dashboard page is displayed
- **AND** user sees welcome message

### Requirement: Failed login flow
The system SHALL test login failure with invalid credentials.

#### Scenario: User logs in with invalid password
- **WHEN** user navigates to /login
- **AND** user enters email "admin@example.com"
- **AND** user enters password "wrongpassword"
- **AND** user clicks login button
- **THEN** user remains on /login page
- **AND** error message "Invalid email or password" is displayed
- **AND** password field is cleared

### Requirement: Login form validation
The system SHALL test login form validation for empty fields.

#### Scenario: User submits empty login form
- **WHEN** user navigates to /login
- **AND** user clicks login button without entering credentials
- **THEN** form shows validation errors
- **AND** email field shows "Email is required"
- **AND** password field shows "Password is required"
- **AND** form is not submitted

### Requirement: Logout flow
The system SHALL test the complete logout flow from authenticated state to login page.

#### Scenario: User logs out
- **WHEN** user is logged in and on dashboard
- **AND** user clicks logout button
- **THEN** user is redirected to /login
- **AND** session is cleared
- **AND** accessing protected routes redirects to /login

### Requirement: Session persistence
The system SHALL test that user session persists across page refreshes.

#### Scenario: User session persists after refresh
- **WHEN** user is logged in and on dashboard
- **AND** user refreshes the page
- **THEN** user remains logged in
- **AND** user stays on dashboard
- **AND** session token is still valid

### Requirement: Protected route access
The system SHALL test that unauthenticated users cannot access protected routes.

#### Scenario: Unauthenticated user accesses dashboard
- **WHEN** user is not logged in
- **AND** user navigates to /dashboard
- **THEN** user is redirected to /login
- **AND** user sees login page

### Requirement: Authentication test data
The system SHALL provide test users for authentication tests with different roles.

#### Scenario: Test users exist
- **WHEN** authentication tests run
- **THEN** admin user exists with email "admin@example.com" and role "admin"
- **AND** regular user exists with email "user@example.com" and role "user"
- **AND** inactive user exists with email "inactive@example.com" and is_active=false

### Requirement: Login error handling
The system SHALL test error handling for network failures during login.

#### Scenario: Network failure during login
- **WHEN** user submits login form
- **AND** backend API is unreachable
- **THEN** user sees error message "Unable to connect to server"
- **AND** user can retry login
- **AND** form is not submitted successfully

### Requirement: Password masking
The system SHALL test that password field is properly masked.

#### Scenario: Password is masked
- **WHEN** user enters password in login form
- **THEN** password characters are masked (shown as dots)
- **AND** password is not visible in plain text
- **AND** password field has type="password"
