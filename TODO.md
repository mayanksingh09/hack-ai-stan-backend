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
- [ ] **Expand PlatformRules**: add optional length/limit attributes for any new text fields (e.g. `description_max_length`, `caption_max_length`, `post_max_length`).
- [ ] **Update PlatformContent**:
  - Include optional fields per platform (e.g. `description`, `caption`, `post_body`).
  - Ensure Pydantic validation & `computed_field` helpers for new length counts.
- [ ] Introduce `GenericPostText` type aliases if helpful to avoid bloating the model.

*Validation checkpoint → mypy & unit tests for model validation pass.*

---

## 3. Generation Logic  
- [ ] **Orchestrator prompt update** so LLM returns the additional fields in a strict, parseable format (e.g. YAML or JSON block).
- [ ] Extend `_parse_response` logic to extract new fields safely with fallbacks.
- [ ] Ensure `_process_tags` still works & unit-tested.

*Validation checkpoint → new fast unit test asserts that orchestrator parses mock LLM response containing all fields.*

---

## 4. Validation Service  
- [ ] Update `ContentValidator`:
  - Character-limit checks for each new field.
  - Platform-specific heuristics (e.g. Instagram caption truncation, YouTube description SEO check ≥ 100 chars).
- [ ] Adjust quality-score weighting to include new dimensions.

*Validation checkpoint → validator unit tests for edge-cases (too-long caption, empty LinkedIn post, etc.).*

---

## 5. API & Router Layer  
- [ ] Modify `/generate/{platform}` response schema to surface new fields; keep backwards-compatibility via version bump or feature flag.
- [ ] Update `/validate/{platform}` to evaluate new fields.
- [ ] Ensure OpenAPI docs reflect changes.

*Validation checkpoint → `app/tests/test_api_endpoints.py` extended & passing.*

---

## 6. Tests  
- [ ] Extend existing tests & create new ones in `app/tests` covering:
  - Model validation for new fields.
  - Successful generation & validation round-trip.
  - API contract (Pydantic/BaseModel changes reflected).

---

## 7. Documentation  
- [ ] Update `README.md` usage examples with new response payload.
- [ ] Add `docs/examples/` with sample JSON per platform.

---

## 8. CI & Tooling  
- [ ] Ensure pre-commit, linters, and typing all succeed.
- [ ] Update any CI workflows to run new tests & doc-linting.

---

## 9. Final QA  
- [ ] Manual smoke test via `uvicorn` & cURL or Swagger UI for at least three platforms.
- [ ] Review API versioning & backward-compatibility notes.

---

### How to strike off items
1. When you complete a task, replace the space inside the checklist brackets with an **x** – e.g. `- [x] Task done`.
2. Commit the change with a concise message, eg. `docs: mark research complete`.
3. Run tests; only push if the suite is green.

Happy shipping! 🚀 