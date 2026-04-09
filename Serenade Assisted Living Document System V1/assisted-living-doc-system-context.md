# Assisted Living Documentation System — Project Context

_Last updated: 2026-03-04 (UTC)_

## Project Goal
Design a documentation system for an Arizona assisted living business that is fast for low-tech caregivers and managers, with Telegram as the primary interface via an OpenClaw agent.

## Business / Operational Context
- State: Arizona
- Capacity: Licensed for up to 10 residents (usually full)
- Primary users: Caregivers and Managers
- Current state: Mostly paper documentation; only templates are digital
- Language: English only
- Family portal: Not needed

## Success Criteria
- Lower charting time
- Make documentation easy and accessible for all caregivers (including low technical skill)
- Keep export/print capability for paper records

## Access & Permissions
- Caregivers + Managers: read / edit / sign
- Manager only: finalization checks and final record finalization
- No silent overwrites after finalization (amendment flow)

## Required Outputs
- All documents exportable (especially PDF) for paper filing

## Core Daily Documentation Scope
1. MAR (Medication Administration Record)
2. ADL documentation

---

## MAR Design Decisions (Agreed)

### Workflow style
- Telegram-first, agent-guided
- Fast default + exception handling
- No shift model

### Timestamp behavior
- For charting: caregiver chooses
  - `Now` (current timestamp)
  - `Earlier` (prior timestamp entry)
- System stores:
  - `event_time` (when care happened)
  - `documented_time` (when entered)
  - `documentation_mode` (`now` or `late`)

### Medication grouping windows
- Pre-breakfast
- Breakfast
- Lunch
- Mid-afternoon
- Dinner
- Bedtime

### Group-pass optimization
Natural language example:
- “John has been given his breakfast meds”

System behavior:
1. Resolve resident + med window
2. Assume all meds in that window = `Given`
3. Ask only for administration time (`Now` or `Earlier`) if missing
4. Present confirmation summary
5. Save batch

### Exception flow
If abnormal event exists:
- Refused / Held / Missed / Other note
- Require reason for non-given statuses
- Optional manager notification capture
- Overwrite only affected meds; leave rest as `Given`

### Pre-breakfast special rule
- Pre-breakfast meds are normally singular
- Singular phrasing should be accepted by default
  - e.g., “John got his pre-breakfast med”
- If more than one pre-breakfast med exists, system asks which med (or allows “all pre-breakfast meds”)

### Natural-language intent support (v1)
- Full pass done: “Gave John breakfast meds”
- Full pass with time: “John breakfast meds given at 8:15 AM”
- Full pass with exception: “...except metformin refused”
- Single med update: “John refused metformin at breakfast”

### Validation / control rules
- Future times not allowed
- Reason required for refused/held/missed
- Caregiver cannot finalize
- No hard delete; amendment/audit trail required

---

## ADL Design Decisions (Agreed)

### PSP-driven requirements
- ADL requirements are determined by each resident’s Personal Service Plan (PSP)
- PSP review cadence per resident:
  - Annual (1x/year)
  - Semiannual (2x/year)
  - Quarterly (4x/year)

### ADL grouping
Example group: Shower care includes
- Hair care
- Face care
- Full body check

### ADL charting behavior
- Group default completion supported (“John completed shower care”)
- Agent auto-expands sub-items and marks complete
- Ask time (`Now` / `Earlier`)
- If exception, capture sub-item + status + reason + optional note

### Due logic
- Show/calculate ADLs due from active PSP
- Warn if charting ADL not due per PSP
- Allow charting not-due with required note (configurable)

---

## PSP Schema Draft (v1)

### ResidentPSP
- `psp_id`, `resident_id`, `effective_date`
- `review_frequency` (`annual|semiannual|quarterly`)
- `next_review_due`
- `status` (`draft|active|superseded`)
- `created_by`, `approved_by_manager`, `approved_at`, `notes`
- Rule: only one active PSP per resident

### PSP_ADL_Requirement
- `requirement_id`, `psp_id`, `adl_code`
- `is_group`
- `frequency_type` (`daily|x_per_week|specific_weekdays|every_n_days|prn`)
- `frequency_value`, `weekdays`, `times_of_day`
- `required`, `start_date`, `end_date`
- `instructions`, `exception_requires_note`

### ADL group templates
- `ADL_Group_Template` (e.g., `SHOWER_CARE`)
- `ADL_Group_Items` (e.g., hair care / face care / full body check)

### Charting records
- `ADL_Chart_Entry` with status/sign/finalization fields
- `ADL_Chart_Item_Entry` for grouped sub-item statuses

---

## Open Questions / Next Steps
1. Set late-charting review threshold (e.g., >8 hours auto-manager review flag)
2. Define canonical ADL code list (10–20 terms)
3. Finalize NL synonym policy (e.g., “morning meds” mapping)
4. Draft ADL natural-language grammar + fallback prompts (next design artifact)

---

## Where to point a new session
Tell a new session to read:
- `/home/sandon/.openclaw/workspace/assisted-living-doc-system-context.md`

Suggested handoff line:
- “Please load project context from `assisted-living-doc-system-context.md` in the workspace and continue system design from there.”
