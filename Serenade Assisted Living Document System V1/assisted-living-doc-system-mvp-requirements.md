# Serenade Assisted Living Documentation System — MVP Requirements (V1)

_Last updated: 2026-03-04 (UTC)_

## 1) Objective
Build a Telegram-first documentation system (via OpenClaw agent) for an Arizona assisted living operation that reduces charting time, improves consistency, and supports low-technical-skill caregivers.

## 2) Scope (MVP)
### In scope
- Medication Administration Record (MAR) charting
- Activities of Daily Living (ADL) charting
- Manager finalization workflow
- PDF export for paper filing
- Full audit trail and amendment model

### Out of scope (MVP)
- Family portal
- Multilingual support
- Complex external integrations unless explicitly added later

## 3) Operating Context
- State: Arizona
- Capacity: 10 residents (typically full)
- User roles: Caregivers, Managers
- Primary interface: Telegram chat with OpenClaw agent
- Language: English only

## 4) Role Permissions
### Caregiver
- Read/edit/sign MAR and ADL entries
- Submit entries for manager review
- Cannot finalize records

### Manager
- All caregiver permissions
- Review and finalize records
- Return entries for correction with required reason
- Process amendments after finalization

## 5) Core Functional Requirements

## 5.1 MAR Requirements
### Medication windows
- Pre-breakfast
- Breakfast
- Lunch
- Mid-afternoon
- Dinner
- Bedtime

### Charting model
- Group-pass default: “all meds in selected window given”
- Exception handling for abnormal events (refused/held/missed/other)

### Timestamp model
For each entry, store:
- `event_time` (when med administration/event occurred)
- `documented_time` (when chart was entered)
- `documentation_mode` (`now` or `late`)

User can choose:
- `Now` (auto current timestamp)
- `Earlier` (manual prior timestamp)

### Pre-breakfast special handling
- Accept singular phrasing by default (“pre-breakfast med”)
- If >1 pre-breakfast med exists, require med selection or explicit “all” confirmation

### Validation
- No future event times
- Reason required for refused/held/missed
- Confirmation required before save

## 5.2 ADL Requirements
### PSP-driven ADLs
- ADL obligations are derived from the resident’s active Personal Service Plan (PSP)
- PSP review frequency per resident: annual / semiannual / quarterly

### Grouped ADLs
Support grouped tasks (example: Shower Care includes Hair Care, Face Care, Full Body Check)

### Fast charting
- Group default completion from natural language (“John completed shower care”)
- Capture time (`Now` / `Earlier`)
- Exception flow for sub-item variance (partial/refused/unable/not done + reason)

### Due logic
- System computes due ADLs from active PSP
- Warn on not-due charting
- Allow not-due entry only with note (configurable)

## 6) Natural Language + Prompting Requirements
The Telegram agent must support natural language for:
- Full medication pass completion
- Full pass with explicit time
- Full pass with exceptions
- Single medication status updates
- Grouped ADL completion with optional exceptions

If any required entity is missing/ambiguous (resident/window/time/med), agent must issue concise fallback prompts with buttons where possible.

## 7) Data & Audit Requirements
- Immutable audit trail for create/edit/sign/finalize/amend actions
- No hard deletes for clinical records
- Finalized records are locked; amendments only
- Store actor identity and timestamps for every material change

## 8) Export & Printing Requirements
- Export all records to PDF for paper retention
- Export scopes:
  - Single entry
  - Resident date-range packet
  - Facility date-range packet
- Print layout must be consistent and readable for filing

## 9) Usability Requirements
- Designed for low-tech caregivers
- Minimize steps and free typing
- Use defaults + buttons + concise prompts
- Keep errors human-readable (non-technical language)

## 10) Non-Functional Requirements
- Reliable role enforcement (manager-only finalization)
- Basic privacy/security controls (least-privilege by role)
- Performance target: normal chart interaction should feel near real-time in chat

## 11) MVP Success Metrics (60-day)
- Reduced average charting time per caregiver
- High completion rate of required MAR/ADL documentation
- Increased accessibility/usability across caregiver team
- Zero unresolved finalization bottlenecks

## 12) Known Open Decisions
1. Late-charting threshold for automatic manager-review flag (e.g., >8h)
2. Canonical ADL code list (10–20 standardized ADLs)
3. Final NL synonym mapping policy (e.g., “morning meds” behavior)

## 13) Implementation Artifacts (already drafted)
- MAR Telegram-first flow
- MAR natural-language grammar + fallback prompts
- PSP schema draft (v1)

Source context file:
- `assisted-living-doc-system-context.md`
