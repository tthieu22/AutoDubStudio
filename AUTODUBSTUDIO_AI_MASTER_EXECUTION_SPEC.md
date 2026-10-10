# AUTODUBSTUDIO

# AI MASTER EXECUTION & AUTONOMOUS DEVELOPMENT SPECIFICATION

**Document:** AUTODUBSTUDIO_AI_MASTER_EXECUTION_SPEC.md
**Project:** AutoDubStudio
**Role of AI:** Senior Software Architect + Technical Lead + QA Engineer + DevOps Engineer + Project Manager
**Execution Mode:** Autonomous but controlled
**Primary Goal:** Analyze → Plan → Implement → Test → Verify → Report → Continue
**Quality Goal:** Production-grade Desktop AI Video Dubbing & Video Editing Application

---

# 1. MANDATORY AI ROLE

You are not a code-generation assistant.

You are the autonomous technical lead responsible for completing the AutoDubStudio project.

You must:

1. Analyze the existing codebase before changing anything.
2. Never assume that a feature is implemented merely because documentation says it is.
3. Verify implementation directly from source code, tests, runtime behavior, configuration, and generated artifacts.
4. Detect missing functionality.
5. Detect incomplete functionality.
6. Detect technically incorrect implementations.
7. Detect architectural inconsistencies.
8. Detect duplicated logic.
9. Detect dead code.
10. Detect broken dependencies.
11. Detect missing tests.
12. Detect missing error handling.
13. Detect missing checkpoint/recovery logic.
14. Detect performance bottlenecks.
15. Detect production-readiness problems.
16. Create a complete implementation roadmap.
17. Execute the roadmap phase by phase.
18. Automatically create tests for every new feature.
19. Run existing tests after every significant modification.
20. Never declare a phase complete without objective verification.
21. Produce a detailed report after every phase.
22. Maintain a persistent project execution state.
23. Resume safely after interruption.
24. Never destroy working functionality while implementing new features.

---

# 2. PROJECT VISION

AutoDubStudio must evolve into a production-grade local desktop application capable of:

## AI VIDEO DUBBING

Video input:

```text
Video
 ↓
Audio Extraction
 ↓
Speech-to-Text
 ↓
Transcript
 ↓
Translation
 ↓
Text-to-Speech
 ↓
Audio Synchronization
 ↓
Audio Mixing
 ↓
Video Rendering
```

## VIDEO EDITING

The application must eventually support:

* Video timeline
* Audio timeline
* Subtitle timeline
* Text layers
* Title layers
* Image layers
* Logo layers
* Watermark layers
* Multiple video layers
* Layer ordering
* Drag and drop
* Position editing
* Resize
* Rotation
* Opacity
* Visibility
* Locking
* Duplication
* Deletion
* Undo
* Redo
* Snap
* Guides
* Timeline trimming
* Timeline splitting
* Timeline moving
* Subtitle editing
* Subtitle styling
* Text styling
* Image manipulation
* Logo placement
* Preview
* Final rendering

## AI FEATURES

The architecture should be capable of supporting:

* Local STT
* Local translation
* Local TTS
* Speaker detection
* Speaker diarization
* Multi-speaker voice mapping
* Subtitle generation
* Subtitle correction
* Translation quality checking
* Audio synchronization
* Automatic subtitle timing
* AI-assisted video editing

## PRIVACY

Default behavior:

```text
NO CLOUD UPLOAD
NO PAID API
LOCAL PROCESSING
LOCAL MODELS
LOCAL FILES
```

The application must not claim that adding a logo/watermark makes copyrighted material legally safe.

---

# 3. CURRENT ARCHITECTURE BASELINE

The current architecture is based on:

```text
React + TypeScript
        │
        ↓
Tauri
        │
        ↓
Rust Core
        │
        ↓
Python CLI Engine
        │
 ┌──────┼──────────┐
 ↓      ↓          ↓
Whisper Ollama     Piper
        │
        ↓
      FFmpeg
        │
        ↓
   Final Video
```

Known completed phases must NOT automatically be trusted.

The AI must independently verify them.

Known baseline:

```text
Phase 1  → Completed
Phase 2  → Project Manager / Pipeline State Machine
Phase 3  → FFmpeg Audio Extraction
Phase 4  → faster-whisper STT
Phase 5  → Ollama Translation
Phase 6  → Piper TTS
Phase 7  → Audio Synchronization
Phase 8  → Audio Mixing + Final Rendering
Phase 9  → End-to-End CLI Pipeline
Phase 10 → Tauri Desktop GUI Integration
```

Known historical test baselines:

```text
Phase 4 → 27/27
Phase 6 → 58/58
Phase 7 → 95/95
Phase 8 → 144/144
Phase 9 → 180/180
```

These numbers are historical information only.

The AI MUST rerun the tests and verify current reality.

---

# 4. HARDWARE BASELINE

Known development/test machine:

```text
CPU:
Intel Core i5-10300H
4 cores / 8 threads

RAM:
16 GB

GPU:
NVIDIA GeForce GTX 1650 Ti
4 GB VRAM

OS:
Windows

Target:
Desktop application
```

The AI must optimize for constrained hardware.

Do not design features that require:

* 24 GB VRAM
* 64 GB RAM
* cloud GPU
* paid APIs

unless an optional fallback is explicitly documented.

---

# 5. NON-NEGOTIABLE DEVELOPMENT PRINCIPLES

## RULE 1 — INSPECT BEFORE IMPLEMENT

Before writing code:

```text
Inspect repository
        ↓
Understand architecture
        ↓
Find existing implementation
        ↓
Find tests
        ↓
Run tests
        ↓
Identify gaps
        ↓
Create plan
        ↓
Implement
```

Never skip inspection.

---

# 6. NEVER TRUST DOCUMENTATION BLINDLY

If documentation says:

```text
Feature X = COMPLETE
```

but source code shows:

```text
Feature X = partial
```

the source code wins.

If tests say:

```text
PASS
```

but runtime behavior is broken:

```text
Feature = NOT COMPLETE
```

Runtime evidence wins.

---

# 7. EVIDENCE-BASED COMPLETION

Every feature must have evidence.

Accepted evidence:

```text
Source implementation
+
Unit tests
+
Integration tests
+
E2E tests
+
Runtime verification
+
Performance measurement
```

A feature cannot be marked COMPLETE simply because:

* code compiles
* UI exists
* function exists
* test file exists
* mock passes

---

# 8. PHASE STATUS SYSTEM

Every phase must use exactly one status:

```text
NOT_STARTED
ANALYZING
PLANNED
IMPLEMENTING
TESTING
FAILED
BLOCKED
PARTIAL
VERIFIED
COMPLETE
```

Definitions:

## COMPLETE

Only when:

```text
Implementation = complete
Tests = pass
Integration = pass
Runtime = verified
Regression = pass
Documentation = updated
```

## PARTIAL

Some functionality works but requirements remain.

## BLOCKED

Cannot proceed because of external/environmental dependency.

## FAILED

Implementation exists but verification fails.

---

# 9. MASTER PROJECT AUDIT

Before creating Phase 11+, perform a complete audit.

Audit:

```text
1. Repository structure
2. Frontend
3. Tauri
4. Rust
5. Python engine
6. FFmpeg
7. STT
8. Translation
9. TTS
10. Audio sync
11. Rendering
12. IPC
13. State management
14. Project persistence
15. Checkpoint system
16. Logging
17. Error handling
18. Tests
19. Performance
20. Packaging
21. Installer
22. Documentation
23. Security/privacy
24. Dependency health
25. Hardware compatibility
```

---

# 10. AUTOMATIC GAP ANALYSIS

After auditing the project, generate:

```text
IMPLEMENTED
PARTIALLY_IMPLEMENTED
MISSING
BROKEN
TECH_DEBT
RISK
OPTIMIZATION
```

Example:

```text
Feature                  Status              Evidence
-------------------------------------------------------------
STT                      VERIFIED            tests + runtime
Translation              VERIFIED            tests
TTS                      VERIFIED            tests
Project persistence      PARTIAL             source only
Timeline                 MISSING             no implementation
Subtitle editor          PARTIAL             UI only
Layer engine             MISSING
Undo/Redo                MISSING
Preview                  PARTIAL
Installer                MISSING
E2E desktop tests        MISSING
```

---

# 11. REQUIREMENT TRACEABILITY MATRIX

Create and maintain:

```text
Requirement
    ↓
Architecture component
    ↓
Implementation
    ↓
Unit tests
    ↓
Integration tests
    ↓
E2E tests
    ↓
Runtime verification
```

Every important requirement must have traceability.

Example:

```text
REQ-EDITOR-001
Drag subtitle position

Implementation:
SubtitleLayer.tsx

Unit Test:
subtitle-layer.test.ts

Integration:
timeline-editor.test.ts

E2E:
editor-drag-subtitle.spec.ts

Runtime:
Verified manually/automatically
```

---

# 12. MASTER ROADMAP GENERATION

After audit, AI must generate the remaining phases.

Do not blindly follow an old roadmap.

The roadmap must be based on actual repository state.

Each phase must contain:

```text
Phase ID
Title
Objective
Dependencies
Architecture changes
Files affected
New modules
Modified modules
API changes
UI changes
Data model changes
Tests
Benchmarks
Risks
Rollback strategy
Acceptance criteria
```

---

# 13. RECOMMENDED PRODUCT ARCHITECTURE

The final architecture should evolve toward:

```text
                         AUTODUBSTUDIO
                               │
              ┌────────────────┴────────────────┐
              │                                 │
          AI ENGINE                        VIDEO EDITOR
              │                                 │
       ┌──────┼──────┐                ┌────────┼────────┐
       │      │      │                │        │        │
      STT   LLM     TTS            Timeline  Layers  Preview
       │      │      │                │        │        │
       └──────┼──────┘                └────────┼────────┘
              │                                 │
              └────────────────┬────────────────┘
                               ↓
                      COMPOSITION ENGINE
                               ↓
                         RENDER ENGINE
                               ↓
                            FFmpeg
                               ↓
                         FINAL VIDEO
```

---

# 14. COMPOSITION ENGINE

The editor must use a structured composition model.

Example conceptual model:

```json
{
  "project": {
    "width": 1920,
    "height": 1080,
    "fps": 30,
    "duration": 120
  },
  "layers": [
    {
      "id": "video-1",
      "type": "video",
      "source": "input.mp4",
      "start": 0,
      "duration": 120
    },
    {
      "id": "subtitle-1",
      "type": "subtitle",
      "text": "Xin chào mọi người",
      "start": 2.0,
      "duration": 3.5,
      "x": 960,
      "y": 900
    },
    {
      "id": "title-1",
      "type": "text",
      "text": "AUTO DUB STUDIO",
      "start": 0,
      "duration": 5,
      "x": 960,
      "y": 100
    },
    {
      "id": "logo-1",
      "type": "image",
      "source": "logo.png",
      "x": 1750,
      "y": 80,
      "scale": 0.2,
      "opacity": 0.8
    }
  ]
}
```

This is conceptual only.

The AI must adapt the exact implementation to the existing architecture.

---

# 15. EDITOR REQUIREMENTS

The editor architecture must eventually support:

## Timeline

```text
Video
Audio
Subtitle
Text
Image
Logo
```

## Layer operations

```text
Add
Delete
Move
Resize
Duplicate
Lock
Hide
Rename
Reorder
```

## Transform

```text
X
Y
Width
Height
Scale
Rotation
Opacity
```

## Editing

```text
Split
Trim
Move
Copy
Paste
Undo
Redo
```

## Preview

```text
Play
Pause
Seek
Zoom
Fullscreen
```

---

# 16. SUBTITLE REQUIREMENTS

Must support:

```text
Create
Edit
Delete
Split
Merge
Move
Resize duration
Style
Position
Import
Export
```

Formats should be designed for:

```text
SRT
VTT
ASS
```

The AI must determine which are actually implemented and which are missing.

---

# 17. TEXT / TITLE REQUIREMENTS

Support:

```text
Text content
Font
Size
Weight
Italic
Color
Stroke
Shadow
Opacity
Alignment
Position
Rotation
Animation
Duration
```

---

# 18. IMAGE / LOGO REQUIREMENTS

Support:

```text
Import image
Position
Scale
Crop
Rotation
Opacity
Duration
Layer order
Delete
Duplicate
```

Watermark functionality must never be described as a legal mechanism to bypass copyright.

---

# 19. AUDIO EDITOR REQUIREMENTS

Support:

```text
Original audio
Dubbed audio
Music
Sound effects
Volume
Mute
Fade in
Fade out
Trim
Split
Move
Ducking
```

---

# 20. UNDO / REDO

All destructive editor operations must be undoable.

Minimum:

```text
Ctrl+Z
Ctrl+Shift+Z
```

The AI must create automated tests for history behavior.

---

# 21. CHECKPOINT / RECOVERY

Long-running jobs must support:

```text
START
RUNNING
PAUSED
CANCELLED
FAILED
RECOVERABLE
COMPLETED
```

After crash:

```text
Open project
 ↓
Detect incomplete job
 ↓
Load checkpoint
 ↓
Validate artifacts
 ↓
Resume from safest valid stage
```

Never blindly reuse corrupted artifacts.

---

# 22. TESTING STRATEGY

Every implementation phase MUST include:

## Unit Tests

Test isolated functions.

## Integration Tests

Test module interaction.

## E2E Tests

Test real workflow.

## Regression Tests

Ensure old features still work.

## Stress Tests

Use long videos and large files where appropriate.

## Failure Tests

Test:

```text
missing file
invalid video
corrupted audio
missing model
FFmpeg failure
TTS failure
translation failure
disk full
process crash
cancel
pause
resume
```

---

# 23. TEST AUTOMATION REQUIREMENT

Whenever a feature is implemented:

```text
Implement
 ↓
Write test
 ↓
Run test
 ↓
Fix failure
 ↓
Run regression suite
 ↓
Verify
```

Never postpone tests until the end of the project.

---

# 24. TEST QUALITY RULE

Do not create fake tests such as:

```text
expect(true).toBe(true)
```

Do not test only mocks when real integration behavior can be tested.

Tests must validate actual behavior.

---

# 25. E2E TEST PRINCIPLE

The most important E2E workflow must eventually be:

```text
Launch application
 ↓
Create project
 ↓
Import video
 ↓
Select source language
 ↓
Select target language
 ↓
Run STT
 ↓
Translate
 ↓
Generate TTS
 ↓
Synchronize audio
 ↓
Generate subtitles
 ↓
Open editor
 ↓
Modify subtitle
 ↓
Add text
 ↓
Add image/logo
 ↓
Move layer
 ↓
Save project
 ↓
Render
 ↓
Validate output
```

---

# 26. OUTPUT VALIDATION

Do not only check:

```text
file exists
```

Validate:

```text
File exists
File readable
Correct codec
Correct resolution
Correct duration
Audio exists
Audio duration matches
Subtitle timing valid
No unexpected corruption
```

Where possible use FFprobe/media metadata validation.

---

# 27. PERFORMANCE TESTING

Track:

```text
Execution time
CPU usage
RAM usage
VRAM usage
Disk usage
GPU usage
Peak memory
Real-time factor
```

Test:

```text
5 min
30 min
60 min
180 min
```

where hardware permits.

---

# 28. HARDWARE SAFETY

The application must not blindly consume all RAM or VRAM.

Implement resource-aware behavior:

```text
Detect hardware
 ↓
Select profile
 ↓
Limit concurrency
 ↓
Monitor resource usage
 ↓
Reduce workload if necessary
```

---

# 29. CRASH SAFETY

For every long-running process:

```text
Start
 ↓
Write checkpoint
 ↓
Run
 ↓
Write progress
 ↓
Write artifact
 ↓
Validate artifact
 ↓
Mark stage complete
```

Never mark a stage complete before artifact validation.

---

# 30. DATABASE / PROJECT STORAGE

If a database is not necessary, prefer a robust project-file format.

The AI must decide based on actual requirements.

Potential:

```text
project.json
```

plus:

```text
assets/
cache/
checkpoints/
logs/
outputs/
```

Avoid introducing a database simply for complexity.

---

# 31. PERFORMANCE RULE

Do not optimize blindly.

First:

```text
Measure
 ↓
Identify bottleneck
 ↓
Optimize
 ↓
Measure again
 ↓
Compare
```

Every meaningful optimization must have benchmark evidence.

---

# 32. ARCHITECTURE RULE

Avoid:

```text
God components
God services
Huge functions
Duplicated state
Circular dependencies
Hardcoded paths
Hardcoded model locations
Hardcoded machine assumptions
```

Prefer:

```text
small modules
clear interfaces
dependency injection
typed contracts
testable services
```

---

# 33. API / IPC RULE

Every IPC command must define:

```text
Input
Output
Errors
Validation
Timeout behavior
Cancellation behavior
```

No silent errors.

---

# 34. ERROR HANDLING

Every error must provide:

```text
Error code
Human-readable message
Technical details
Recovery suggestion
Log reference
```

Example:

```text
E_FFMPEG_RENDER_FAILED

Rendering failed.

Possible causes:
- insufficient disk space
- invalid media stream
- unsupported codec

Recovery:
Check logs and retry rendering.
```

---

# 35. LOGGING

Logs must include:

```text
timestamp
project ID
job ID
phase
component
severity
message
error code
```

Levels:

```text
DEBUG
INFO
WARNING
ERROR
CRITICAL
```

---

# 36. SECURITY / PRIVACY

Check for:

```text
Unexpected network calls
Secret leakage
API keys in source
Unsafe shell commands
Path traversal
Untrusted file execution
Command injection
Temporary-file leaks
```

All external processes must use safe argument handling.

---

# 37. PACKAGING

Eventually produce:

```text
Windows installer
Portable build
```

The AI must verify:

```text
Fresh machine
No development environment
No IDE
No source repository
```

The application must still start and run according to documented requirements.

---

# 38. FIRST-RUN EXPERIENCE

Eventually implement:

```text
First Launch
 ↓
Hardware Detection
 ↓
Dependency Detection
 ↓
Model Detection
 ↓
Performance Profile
 ↓
Storage Location
 ↓
Ready
```

---

# 39. PHASE EXECUTION PROTOCOL

For every phase:

## STEP 1 — ANALYZE

Inspect all relevant files.

Output:

```text
Current state
Existing implementation
Missing implementation
Risks
Dependencies
```

## STEP 2 — PLAN

Create:

```text
Implementation Plan
Test Plan
Rollback Plan
Acceptance Criteria
```

## STEP 3 — IMPLEMENT

Make the smallest safe set of changes.

## STEP 4 — TEST

Run:

```text
unit
integration
e2e
regression
```

where applicable.

## STEP 5 — DEBUG

If failure occurs:

```text
Identify root cause
Fix
Re-run failed test
Re-run regression
```

Never simply disable a failing test.

## STEP 6 — VERIFY

Verify real behavior.

## STEP 7 — REPORT

Generate phase report.

---

# 40. PHASE REPORT FORMAT

Every completed phase MUST generate:

```text
# AUTODUBSTUDIO — PHASE X REPORT

## 1. Status

PASS / PARTIAL / FAILED / BLOCKED

## 2. Objective

## 3. Existing State

## 4. Changes Implemented

## 5. Files Added

## 6. Files Modified

## 7. Architecture Changes

## 8. API / IPC Changes

## 9. Tests Added

## 10. Tests Executed

## 11. Test Results

## 12. Regression Results

## 13. E2E Results

## 14. Performance Results

## 15. Bugs Found

## 16. Bugs Fixed

## 17. Remaining Issues

## 18. Technical Debt

## 19. Risks

## 20. Acceptance Criteria

## 21. Evidence

## 22. Next Recommended Phase

## 23. Overall Project Completion
```

---

# 41. TEST REPORT FORMAT

Always provide:

```text
Total tests:
Passed:
Failed:
Skipped:
Blocked:

Pass rate:

Unit:
Integration:
E2E:
Regression:
Stress:
```

Example:

```text
Total: 247
Passed: 247
Failed: 0
Skipped: 0

Pass Rate: 100%
```

Do not claim 100% if any required test is skipped or blocked.

---

# 42. PROJECT HEALTH SCORE

After every phase calculate:

```text
Architecture
Implementation
Testing
Performance
Reliability
UX
Security
Packaging
Documentation
```

Each:

```text 0–100
```

Then provide:

```text
Overall Project Health
```

Do not use the score to hide critical failures.

A critical blocker must remain visible even if the numerical score is high.

---

# 43. DEFINITION OF DONE

A feature is DONE only if:

```text
[ ] Requirements implemented
[ ] Architecture integrated
[ ] Unit tests
[ ] Integration tests
[ ] E2E tests where applicable
[ ] Regression tests pass
[ ] Error handling
[ ] Logging
[ ] Persistence if required
[ ] Recovery if required
[ ] Performance checked
[ ] Documentation updated
[ ] Runtime verified
```

---

# 44. DO NOT CHEAT

The AI MUST NOT:

* remove tests just to make the suite pass
* weaken assertions
* mock the entire system
* hardcode expected output
* disable validation
* hide errors
* mark TODOs as complete
* claim runtime verification without running it
* claim a benchmark without measuring it
* claim a feature exists because a component name exists
* silently change requirements
* silently delete functionality
* replace working architecture unnecessarily

---

# 45. CHANGE CONTROL

Before major architectural changes:

```text
Current architecture
 ↓
Problem
 ↓
Proposed architecture
 ↓
Advantages
 ↓
Risks
 ↓
Migration strategy
 ↓
Tests
```

Do not rewrite the entire project unless clearly justified.

---

# 46. BACKWARD COMPATIBILITY

Existing functionality must continue working.

After each major phase:

```text
New tests
+
Existing tests
+
Regression tests
```

must pass.

---

# 47. CHECKPOINT FILE

Maintain a machine-readable execution state.

Example:

```json
{
  "current_phase": 11,
  "status": "IMPLEMENTING",
  "completed_phases": [],
  "active_tasks": [],
  "blocked_tasks": [],
  "last_successful_test": "",
  "last_commit": "",
  "last_verified_at": "",
  "next_action": ""
}
```

The exact format may be adapted to the repository.

---

# 48. AI SESSION RECOVERY

If the AI session stops:

```text
Read project state
 ↓
Read latest phase report
 ↓
Read checkpoint
 ↓
Inspect git diff
 ↓
Run tests
 ↓
Determine actual state
 ↓
Continue
```

Never assume previous work completed successfully.

---

# 49. GIT SAFETY

Before major work:

```text
Check git status
Check current branch
Check uncommitted changes
```

Never overwrite unrelated user changes.

If Git is available:

```text
small logical commits
```

are preferred.

Example:

```text
feat(editor): add timeline model
feat(editor): add layer engine
test(editor): add layer integration tests
fix(render): validate composition
```

---

# 50. FINAL PRODUCT REQUIREMENTS

The final product should allow a normal user to:

```text
1. Open application
2. Create project
3. Import video
4. Select language
5. Generate transcript
6. Translate
7. Generate dubbed voice
8. Generate subtitles
9. Open video editor
10. Edit subtitles
11. Drag subtitle position
12. Add text
13. Add title
14. Add image
15. Add logo
16. Move layers
17. Resize layers
18. Change layer order
19. Edit audio
20. Preview
21. Save project
22. Resume later
23. Render final video
24. Export video
```

---

# 51. AUTONOMOUS DECISION RULE

When you encounter a missing feature:

DO NOT immediately implement it.

First determine:

```text
Does it already exist?
        │
        ├── YES → verify
        │
        └── NO
             ↓
       Is it required?
             ↓
       Is dependency ready?
             ↓
       Design
             ↓
       Implement
             ↓
       Test
```

---

# 52. PRIORITY SYSTEM

Use:

```text
P0 = Critical blocker
P1 = Required for production
P2 = Important feature
P3 = Enhancement
P4 = Optional
```

Always fix:

```text
P0
 ↓
P1
 ↓
P2
 ↓
P3
 ↓
P4
```

Do not spend time polishing P4 while P0/P1 issues remain.

---

# 53. FINAL ROADMAP RULE

The AI must dynamically maintain:

```text
COMPLETED
IN_PROGRESS
NEXT
BLOCKED
DEFERRED
```

The roadmap must change when repository reality changes.

Do not blindly follow a stale roadmap.

---

# 54. FINAL RELEASE GATE

Before declaring AutoDubStudio production-ready:

## Functional

```text
All critical workflows work.
```

## Tests

```text
Required tests pass.
```

## Runtime

```text
Real video successfully processed.
```

## Long video

```text
Long-duration processing verified where hardware permits.
```

## Recovery

```text
Crash/resume verified.
```

## Editor

```text
Timeline and layer editing verified.
```

## Rendering

```text
Output media validated.
```

## Packaging

```text
Fresh installation verified.
```

## Documentation

```text
Installation and usage documented.
```

---

# 55. FINAL AI RESPONSE REQUIREMENT

At the end of every execution session, provide:

```text
CURRENT PROJECT STATUS

Completed:
...

Implemented:
...

Verified:
...

Failed:
...

Blocked:
...

Remaining:
...

Critical risks:
...

Next recommended action:
...

Overall completion:
X%

Confidence:
HIGH / MEDIUM / LOW
```

The completion percentage must be based on actual requirements, not number of files or lines of code.

---

# 56. FIRST ACTION

When this specification is loaded, DO NOT immediately write new features.

The first action MUST be:

```text
PHASE 0 — FULL PROJECT AUDIT
```

Perform:

```text
Repository inspection
Architecture inspection
Dependency inspection
Existing feature inspection
Test inspection
Runtime inspection
Performance inspection
Packaging inspection
Documentation inspection
Security inspection
```

Then generate:

```text
AUTODUBSTUDIO — MASTER AUDIT REPORT
```

The report must contain:

```text
1. Current Architecture
2. Existing Features
3. Verified Features
4. Partial Features
5. Missing Features
6. Broken Features
7. Technical Debt
8. Test Coverage
9. Runtime Verification
10. Performance Baseline
11. Security Risks
12. Packaging Status
13. Product Gaps
14. Recommended Roadmap
15. Phase Priorities
16. Critical Blockers
17. Estimated Complexity
18. Recommended Next Phase
```

ONLY AFTER THIS AUDIT may implementation begin.

---

# 57. FINAL PRINCIPLE

The goal is NOT:

> "Generate as much code as possible."

The goal is:

> "Build the correct product, verify it objectively, detect failures automatically, recover safely, and maintain a trustworthy record of what is actually completed."

Every decision must prioritize:

```text
Correctness
Reliability
Testability
Maintainability
Performance
User Experience
Recoverability
Production Readiness
```

---

# 58. CRITICAL REQUIREMENT — AI PIPELINE TO TIMELINE INTEGRATION

```text
Import Video
    ↓
AI Pipeline
    ├── STT
    ├── Translation
    ├── TTS
    ├── Audio Sync
    └── Subtitle Generation
             ↓
      Composition Builder
             ↓
        Timeline Model
             ↓
┌─────────────────────────────────────┐
│ TIMELINE                            │
│                                     │
│ VIDEO       ████████████████████    │
│ ORIGINAL    ████████████████████    │
│ DUB AUDIO   ████████████████████    │
│ SUBTITLE    ███ ████ ███ ██████     │
│ TITLE           █████               │
│ IMAGE                ███████        │
│ LOGO        ███████████████████     │
└─────────────────────────────────────┘
             ↓
       User Editing
             ↓
      Final Composition
             ↓
           FFmpeg
             ↓
       Final Video
```

## Mandatory AI Artifact to Timeline Mapping

1. **Video Import**:
   - Original video file is automatically added as a `video` clip on the primary Video track.

2. **STT & Translation**:
   - Every transcribed / translated segment is converted into an editable `subtitle` clip with `id`, `trackId`, `start`, `duration`, `text`, `style`, `position`.
   - Users can drag subtitle boundaries, change text, adjust styling, split, merge, delete.

3. **TTS & Audio Sync**:
   - Synthesized & synchronized speech is mapped directly into an `audio` clip on the Dub Audio track.
   - Users can trim, split, adjust volume, mute, fade, and replace.

4. **Integration Test Verification Flow**:
```text
Verify Subtitle Text Updated
    ↓
Run TTS
    ↓
Verify Dub Audio Layer Created
    ↓
Run Audio Sync
    ↓
Verify Audio Timing Updated
    ↓
Add Text
    ↓
Verify Text Layer
    ↓
Add Image
    ↓
Verify Image Layer
    ↓
Move Layer
    ↓
Save Project
    ↓
Reload Project
    ↓
Verify Timeline
    ↓
Render
    ↓
Validate Final Video
```

## Architectural Source of Truth

```text
                  ┌──────────────┐
                  │ AI PIPELINE  │
                  └──────┬───────┘
                         │
             ┌───────────▼───────────┐
             │  ARTIFACT MANAGER     │
             └───────────┬───────────┘
                         │
             ┌───────────▼───────────┐
             │ COMPOSITION BUILDER   │
             └───────────┬───────────┘
                         │
                         ▼
                 ┌──────────────┐
                 │   TIMELINE   │
                 │ SOURCE TRUTH │
                 └──────┬───────┘
                        │
         ┌──────────────┼───────────────┐
         ▼              ▼               ▼
      Canvas         Inspector        Layers
         │              │               │
         └──────────────┼───────────────┘
                        ▼
                 USER EDITING
                        │
                        ▼
                 FINAL COMPOSITION
                        │
                        ▼
                     FFmpeg
                        │
                        ▼
                  FINAL VIDEO
```

The pipeline does not end at `AI → File`. It must be: `AI → Artifact → Timeline Layer → Editable Composition → User Modification → Final Composition → Renderer → Video`.

The Timeline is the central integration point between the AI engine and the Video Editor.

END OF TIMELINE INTEGRATION REQUIREMENT

