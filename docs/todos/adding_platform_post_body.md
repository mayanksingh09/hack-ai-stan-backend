# 🚧 Platform-Specific Content Expansion – Project TODO

> Goal: Extend the `/api/v1/generate/{platform}` endpoint so that, in addition to *title* and *tags*, it returns **all text fields required to publish directly to each supported platform while still enforcing platform rules**.

---

## 0. Pre-flight
- [x] **Familiarise with existing code & tests** – read `app/models`, `app/services`, `app/routers`, and current tests to understand the baseline.

---

## 1. Research & Specification  
For every supported platform (`youtube`, `instagram`, `facebook`, `tiktok`, `x_twitter`, `linkedin`, `twitch`):
- [x] Collect up-to-date text-field requirements (description/caption/body limits, hashtag rules, truncation points, etc.).
- [x] Capture findings in `docs/platform_text_rules.md` as a table (field, max length, notes, source URL).
- [x] Add automated unit tests that fail if any rule doc entry is missing.

*Validation checkpoint → `docs` file present & tests green before moving on.*

---

## 2. Model Layer  
- [x] **Expand PlatformRules**: add optional length/limit attributes for any new text fields (e.g. `description_max_length`, `caption_max_length`, `post_max_length`).
- [x] **Update PlatformContent**:
  - Include optional fields per platform (e.g. `description`, `caption`, `post_body`).
  - Ensure Pydantic validation & `computed_field` helpers for new length counts.
- [x] ~~Introduce `GenericPostText` type aliases if helpful to avoid bloating the model~~ (Not needed - optional fields work well).

*Validation checkpoint → mypy & unit tests for model validation pass.*

---

## 3. Generation Logic  
- [x] **Orchestrator prompt update** so LLM returns the additional fields in a strict, parseable format (JSON format implemented).
- [x] Extend `_parse_response` logic to extract new fields safely with fallbacks.
- [x] Ensure `_process_tags` still works & unit-tested.

*Validation checkpoint → new fast unit test asserts that orchestrator parses mock LLM response containing all fields.*

---

## 4. Validation Service  
- [x] Update `ContentValidator`:
  - Character-limit checks for each new field.
  - Platform-specific heuristics (e.g. Instagram caption truncation, YouTube description SEO check ≥ 100 chars).
- [x] Adjust quality-score weighting to include new dimensions.

*Validation checkpoint → validator unit tests for edge-cases (too-long caption, empty LinkedIn post, etc.).*

---

## 5. API & Router Layer  
- [x] Modify `/generate/{platform}` response schema to surface new fields; keep backwards-compatibility via version bump or feature flag.
- [x] Update `/validate/{platform}` to evaluate new fields.
- [x] Ensure OpenAPI docs reflect changes.

*Validation checkpoint → `app/tests/test_api_endpoints.py` extended & passing.*

---

## 6. Tests  
- [x] Extend existing tests & create new ones in `app/tests` covering:
  - Model validation for new fields.
  - Successful generation & validation round-trip.
  - API contract (Pydantic/BaseModel changes reflected).

---

## 7. Documentation  
- [x] Update `README.md` usage examples with new response payload.
- [x] Add `docs/examples/` with sample JSON per platform.

---

## 8. CI & Tooling  
- [x] Ensure pre-commit, linters, and typing all succeed.
- [x] Update any CI workflows to run new tests & doc-linting.

---

## 9. Final QA  
- [x] Manual smoke test via `uvicorn` & cURL or Swagger UI for at least three platforms.
- [x] Review API versioning & backward-compatibility notes.

---

### How to strike off items
1. When you complete a task, replace the space inside the checklist brackets with an **x** – e.g. `- [x] Task done`.
2. Commit the change with a concise message, eg. `docs: mark research complete`.
3. Run tests; only push if the suite is green.

Happy shipping! 🚀 