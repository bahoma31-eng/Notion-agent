# Strategy Plan — Issue \#6

## Goal
Implement an end-to-end automation flow:
1) Qualifying email → GitHub Issue.
2) Create a detailed strategy plan file under `plans/`.
3) Convert Phase 1 of that plan into a JSON task file under `input/`.
4) Send an HTML email report describing what was created.

## Assumptions
- Default branch is `main`.
- The repository will contain two folders:
  - `plans/` for markdown plans.
  - `input/` for JSON task inputs.
- The “Phase 1 JSON” is a structured representation of Phase 1 tasks, designed for downstream automation.
- If sensitive data appears in inbound email, it must be redacted as `[REDACTED]` in all outputs.

## Phases

### 1) Analysis & Specification
**Description**
Clarify requirements and define stable conventions for file locations, naming, and JSON schema.

**Tasks**
- [ ] Confirm the exact email matching conditions (recipient, sender) and whether subject filters are needed
- [ ] Define the canonical plan file path:
  - [ ] `plans/plan_strategy_[ISSUE_NUMBER].md`
- [ ] Define the canonical JSON task file path:
  - [ ] `input/task_phase1_issue_[ISSUE_NUMBER].json`
- [ ] Define the JSON schema for Phase 1 tasks
	- [ ] Include metadata fields (issue number, createdAt, links)
	- [ ] Include a tasks checklist array
	- [ ] Include expected output
- [ ] Decide label mapping rules (bug/enhancement/docs/ci/task)
- [ ] Define the HTML report template sections
- [ ] Define how to handle redactions in report + files

**Expected Output**
- A documented, consistent file naming convention.
- A fixed JSON schema for Phase 1 tasks.
- A fixed HTML report format.

### 2) Implementation
**Description**
Implement the automation in code (or workflow) so it runs automatically per qualifying email.

**Tasks**
- [ ] Implement Issue creation logic (title + body format in English)
- [ ] Implement plan generation logic and write markdown file under `plans/`
- [ ] Implement Phase 1 extraction logic from the plan
- [ ] Write JSON file to `input/` using the defined schema
- [ ] Implement HTML email report generation
- [ ] Add tests or dry-run mode (if possible)

**Expected Output**
- Automation produces: Issue + plan file + JSON task file + HTML report.

### 3) Validation & Hardening
**Description**
Verify the flow works and is robust to edge cases.

**Tasks**
- [ ] Test with short emails and long emails
- [ ] Test with missing details (ensure safe behavior)
- [ ] Test redaction behavior
- [ ] Confirm file links are correct
- [ ] Verify repo labels exist or are handled gracefully

**Expected Output**
- Reliable runs with correct artifacts produced.

### 4) Documentation
**Description**
Document how the flow works and how to modify it.

**Tasks**
- [ ] Update README/docs with a high-level overview
- [ ] Document JSON schema and file locations
- [ ] Provide examples of generated artifacts

**Expected Output**
- Clear usage and maintenance documentation.

## Risks / Notes
- Email sending may require enabling send permissions for the mail integration.
- Repo branch name might differ from `main`.
- Labels may not exist; plan should handle missing labels.
