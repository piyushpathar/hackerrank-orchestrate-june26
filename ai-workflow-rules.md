# AI Workflow & Development Rules: ClaimVerify

## Development Methodology

Build this project **incrementally and spec-driven**. Context files define what to build, how to build it, and current progress. Implement against these specs—do not invent behavior.

## Scoping Rules

**Work on ONE feature unit at a time.**

A feature unit is:
- One user journey from start to finish (e.g., "submit claim with images")
- One API endpoint with request validation and response
- One background job with its input/output schema
- One component with its integration point

### Examples of Proper Scoping

✅ **Good**:
1. Claim submission form (UI + validation)
2. Image upload and compression (backend service)
3. Database schema for claims and images
4. API endpoint to save claim + enqueue job
5. Background job to process single claim
6. Dashboard to display claim status

❌ **Bad**:
- "Build the entire claims system" (too broad)
- "Implement vision analysis, database, UI, and export" (multiple unrelated systems)
- "Add search, filtering, sorting, and pagination to dashboard" (four features)

## Splitting Work

Split an implementation step if it crosses **system boundaries**:

- [ ] UI changes + background processing → **Split**: Build UI first, then job
- [ ] Database writes + API response → **Keep together**: Both in one request handler
- [ ] Vision API call + caching logic → **Split**: Call works first, caching second
- [ ] Job processing + result export → **Keep together**: Both in one job handler
- [ ] Image upload + compression → **Split**: Upload works first, compression next
- [ ] Multiple API routes → **Split**: One route per feature unit

## Handling Missing Requirements

Before implementing:

1. **Read the problem statement completely** — understand all inputs/outputs
2. **Check context files** — are requirements already defined?
3. **If ambiguous** — resolve in context file BEFORE coding
4. **If missing** — add to `progress-tracker.md` as "Open Question"
5. **Do not invent** — if not defined, ask or update tracker

### Missing Requirement Example

❌ Problem: "Estimate claim severity" — but no definition of severity levels

✅ Solution: Add to progress-tracker:
```markdown
## Open Questions
- **Severity levels**: What is the scale? (low/medium/high? 1-10? percentage?)
  - Should it be derived from image analysis alone?
  - Or should user history affect severity?
  - Is severity used in the decision, or just reported?
```

Then discuss with team before implementing.

## Protected Foundation Components

**Do NOT modify:**
- `components/ui/*` (shadcn/ui components)
- Third-party library internals (Prisma client, Clerk modules)

**Do modify:**
- `app/*` (application routes)
- `components/dashboard/*` (application-specific UI)
- `lib/*` (business logic)
- Tailwind config, CSS variables, theme

**Reason:** Foundation components are reusable. Project-specific logic belongs in app-level code.

## Feature Delivery Checklist

Before marking a feature "done", verify:

- [ ] **Spec**: Implementation matches the context files
- [ ] **Invariants**: No invariants from `architecture-context.md` violated
- [ ] **Types**: Full TypeScript, no `any`, all inputs validated
- [ ] **Testing**: Unit tests for functions, happy path verified
- [ ] **Logging**: Key operations logged with context
- [ ] **Error handling**: Failures logged, user-facing errors clear
- [ ] **Performance**: Meets latency targets (see `project-overview.md`)
- [ ] **Docs**: README updated, code comments where non-obvious
- [ ] **Progress**: `progress-tracker.md` updated with completion

## Session Workflow

### Start of Session
1. Read `progress-tracker.md` — understand current state
2. Read relevant context file for the feature being worked on
3. Verify you understand the invariants and performance targets

### During Development
1. Keep implementation tightly scoped (one feature unit)
2. Check work against the spec regularly
3. Add logging for decision points
4. Write unit tests as you go

### End of Session
1. Update `progress-tracker.md` with actual progress (not intended)
2. Note any blockers or open questions
3. Leave implementation in a state that can be reviewed and tested
4. Commit with clear message referencing the feature unit

### Example Progress Update

❌ Bad:
```markdown
## In Progress
- Backend and frontend and database
```

✅ Good:
```markdown
## In Progress
- **Image compression service**: Converts uploaded JPG/PNG to WebP, saves to Vercel Blob
  - Status: Testing with sample images
  - Blocker: None
  - Next: Integrate with claim submission API

## Completed
- [x] Image validation (format, size)
- [x] Upload endpoint (multipart form)
```

## Dependency Resolution

If a feature depends on another feature not yet built:

1. **Stub the dependency** — create a mock/placeholder implementation
2. **Document the dependency** — note in progress tracker
3. **Build the real version after** — replace stub when dependency is ready

Example:

```typescript
// lib/vision/index.ts - STUB
export async function analyzeImage(
  imagePath: string
): Promise<ImageAnalysis> {
  // TODO: Replace with real Claude Vision API call
  // For now, return synthetic analysis
  return {
    issueType: "dent",
    objectPart: "bumper",
    confidence: 0.85,
  };
}
```

Then, after vision API integration is complete:

```typescript
// lib/vision/index.ts - REAL
export async function analyzeImage(
  imagePath: string
): Promise<ImageAnalysis> {
  const response = await anthropic.vision.analyze(imagePath);
  return parseVisionResponse(response);
}
```

## Code Review Checklist

When reviewing your own work:

- [ ] Does it solve the specified problem only?
- [ ] Are all types properly defined?
- [ ] Is error handling appropriate?
- [ ] Are database queries optimal?
- [ ] Are API responses consistent?
- [ ] Is logging sufficient for debugging?
- [ ] Are performance targets met?
- [ ] Is code testable?
- [ ] Are there any TODO comments left?
- [ ] Does context file need updates?

## Handling New Information

If during development you discover:
- A requirement is unclear → update context file with clarification
- A requirement is infeasible → discuss with team, update progress tracker
- A better approach exists → update context file before changing implementation
- Performance is worse than target → investigate root cause, document findings

**Update context files BEFORE changing implementation.**

## Communication Rules

When stuck:
1. **Check context files** — is the requirement actually defined?
2. **Check progress tracker** — is there a known blocker?
3. **Ask for clarification** — update progress tracker with question
4. **Don't guess** — unblock by resolving the question, not by assuming

## Continuous Integration

Every commit should:
- [ ] Pass TypeScript compilation (`tsc --noEmit`)
- [ ] Pass linter (`eslint .`)
- [ ] Pass unit tests (`npm test`)
- [ ] Include meaningful commit message
- [ ] Reference the feature unit being worked on

Example:

```bash
git commit -m "feat: Image compression service (WebP conversion, Blob storage)"
```

NOT:

```bash
git commit -m "work in progress"
```

## Deployment Readiness

Before merging to main:

- [ ] All tests passing
- [ ] No console errors in staging
- [ ] Performance benchmarks met
- [ ] Database migrations tested locally
- [ ] Environment variables documented
- [ ] README updated
- [ ] Progress tracker reflects actual state

## Scaling & Cost Considerations

As you implement, consider:

- **Vision API calls**: Cache results by image hash, batch when possible
- **Database queries**: Use indexes, avoid N+1 patterns
- **Image storage**: Compress to WebP, lazy load in UI
- **Background jobs**: Implement concurrency control, retry logic
- **Cache hits**: Size Redis memory, set appropriate TTLs
- **Monitoring**: Log token usage, API costs, processing times

Log these metrics at the end of each feature unit.
