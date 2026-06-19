# Progress Tracker: ClaimVerify

## Current Phase

**Execution & Completion** — ClaimVerify Python Pipeline Implementation

## Current Goal

Complete the Python claim verification pipeline, configure multi-provider client wrappers (Anthropic, OpenAI, Heuristics), implement concurrency and cache utilities, run evaluation, and output predictions.

## Completed

- [x] Project overview and success criteria defined
- [x] Multi-provider architecture design (Anthropic, OpenAI, Heuristic)
- [x] Created `code/claimverify/providers.py` implementing Claude Vision, GPT-4o, and Heuristic rules
- [x] Created `code/main.py` pipeline orchestrator with thread-pool concurrency and CSV output generation
- [x] Created `code/evaluation/main.py` validation runner that computes accuracy metrics on `sample_claims.csv`
- [x] Fixed sorting order bugs related to unhashable `ClaimInput` types in `main.py`
- [x] Ran full claims pipeline on `dataset/claims.csv` to generate the correct schema predictions in `dataset/output.csv`
- [x] Generated comprehensive validation and operational cost analysis in `evaluation/evaluation_report.md`

## In Progress

None. Ready for review.

## Next Up

### Phase 1: Foundation (2 weeks)

1. **Project Setup**
   - Initialize Next.js 15 with TypeScript strict mode
   - Configure Tailwind CSS with dark theme tokens
   - Set up Clerk authentication
   - Configure PostgreSQL + Prisma
   - Set up Redis (Upstash)
   - Deploy to Vercel

2. **Database & Auth**
   - Create Prisma schema (User, Claim, ClaimDecision, etc.)
   - Set up database migrations
   - Implement Clerk auth callbacks
   - Create auth/permission helpers
   - Seed evidence requirements table

3. **Image Handling**
   - Implement image upload endpoint
   - Set up Vercel Blob storage integration
   - Create image compression (WebP)
   - Implement image validation (format, size)
   - Add image metadata storage

4. **Core Claim Processing**
   - Implement claim submission endpoint
   - Create ClaimProcessor orchestrator (stub vision analysis)
   - Set up BullMQ job queue
   - Implement claim status tracking
   - Create basic claim detail view

### Phase 2: Vision & Risk (2 weeks)

5. **Vision Integration**
   - Integrate Claude Vision API
   - Parse vision response into structured types
   - Implement vision result caching (Redis)
   - Add image quality detection
   - Handle vision API rate limiting

6. **Risk Assessment**
   - Implement user history loading + caching
   - Create risk flag generation
   - Implement risk scoring logic
   - Add user history to decision context
   - Create user profile view (admin)

7. **Evidence Validation**
   - Load evidence requirements from cache
   - Implement evidence standard checking
   - Create requirement matching logic
   - Add evidence validation to decision engine
   - Create evidence requirement admin interface

### Phase 3: Decision Engine (2 weeks)

8. **Decision Generation**
   - Implement final decision logic (supported/contradicted/insufficient)
   - Add severity estimation
   - Create decision justification generator
   - Implement audit logging
   - Add decision-making tests

9. **Dashboard**
   - Create claims list with pagination
   - Implement search and filtering
   - Add claim detail view with analysis
   - Create image gallery component
   - Implement status badges and risk indicators

10. **Operations Features**
    - Add manual review queue
    - Create decision override interface
    - Implement batch export (CSV)
    - Add claims analytics dashboard
    - Create admin settings interface

### Phase 4: Optimization & Testing (1 week)

11. **Performance Optimization**
    - Profile vision API calls and caching
    - Optimize database queries
    - Implement Redis caching for dashboard
    - Add request deduplication
    - Benchmark claim processing end-to-end

12. **Testing & Monitoring**
    - Write unit tests for vision analysis
    - Write integration tests for API routes
    - Set up error logging (Sentry)
    - Create monitoring dashboard (PostHog)
    - Load test with sample claim data

13. **Documentation & Deployment**
    - Create comprehensive README
    - Document API endpoints
    - Create admin setup guide
    - Set up CI/CD pipeline
    - Prepare for production deployment

## Open Questions

1. **Vision Analysis Scope**
   - Should the vision model detect object type (car vs laptop vs package)?
   - Or does the user provide the object type upfront?
   - Current assumption: User provides type, vision detects damage

2. **Risk Scoring Algorithm**
   - How to weight different risk factors?
   - Current: User history 40%, image quality 30%, claim mismatch 30%
   - Should this be tunable per risk level?

3. **Manual Review Thresholds**
   - At what risk score should claims be flagged for manual review?
   - Current assumption: Risk score > 60 = manual review
   - Should this vary by object type or claim history?

4. **Evidence Requirements Management**
   - Should evidence requirements be versioned?
   - Who updates them, how often?
   - Current: Database table, updated via admin interface

5. **Image Retention Policy**
   - How long to keep images for?
   - Current assumption: 7 years (insurance requirement)
   - Archive strategy (S3 Glacier after 1 year)?

6. **Export/Integration**
   - What systems need to consume claim decisions?
   - Should there be a webhook or API for decision export?
   - Required for MVP or Phase 2 feature?

7. **Scalability Targets**
   - Expected claims per day?
   - Expected concurrent users?
   - Current architecture targets: 1,000 claims/day, horizontal scaling via BullMQ

## Architecture Decisions

### Technology Selection
- **Framework**: Next.js 15 (App Router, Server Components, image optimization)
- **Database**: PostgreSQL + Prisma (relational, type-safe, transactions)
- **Cache**: Redis via Upstash (user history, vision results, requirements)
- **Vision**: Claude 3.5 Vision API (fastest, accurate, cacheable)
- **Jobs**: BullMQ + Redis (durable, resumable, monitoring)
- **Storage**: Vercel Blob (cheap, integrated, CDN-backed)
- **Auth**: Clerk (handles sign-up, sign-in, organizations)
- **UI**: shadcn/ui + Tailwind (accessible, dark mode, minimal config)

### Storage Layer Separation
- **PostgreSQL**: Metadata (users, claims, decisions, audit logs)
- **Vercel Blob**: Images (compressed WebP)
- **Redis**: Cache (user history, vision results, evidence requirements)

Rationale: Database would overflow with image data. Separate layers allow independent scaling.

### Job Processing Pattern
- All vision API calls run in BullMQ jobs (async, not in request handlers)
- Jobs are idempotent: can retry safely
- Job state persisted in Redis: resumable on failure
- Dashboard polls job status (or receives webhook)

Rationale: Long-running API calls must not block user requests.

### Caching Strategy
- User history: 1-hour TTL (low-write, high-read)
- Vision results: 7-day TTL by image hash (prevent duplicate analyses)
- Evidence requirements: 24-hour TTL (stable configuration)
- Dashboard queries: 30-second revalidation (balances freshness vs. load)

Rationale: Reduce database/API load while keeping data fresh.

### Risk Assessment
- Evidence grounded in images (primary source of truth)
- User history adds context (secondary)
- User history alone does NOT override visual evidence
- All decisions include supporting image IDs for auditability

Rationale: Visual evidence is objective. History helps identify patterns, not substitute evidence.

## Session Notes

### Session 1: Context Creation
- Created comprehensive context files for ClaimVerify project
- Defined technology stack and architecture
- Documented UI design system with dark theme
- Created development workflow and scoping rules
- Established invariants and performance targets
- Ready for Phase 1 implementation start

## Metrics & Monitoring

### Operational Metrics (to track)
- Claims processed per day
- Average processing latency (p50, p95, p99)
- Manual review rate (% of claims flagged)
- Decision override rate (% of decisions changed by humans)
- Vision API cost per claim

### Quality Metrics (to track)
- Claim status distribution (% supported/contradicted/insufficient)
- Evidence standard met rate
- Risk flag precision (% of manual reviews that confirm risk)
- False positive rate on risk flags

### System Metrics (to track)
- Vision API success rate
- Vision result cache hit rate
- User history cache hit rate
- Database query latencies (p95)
- Job failure and retry rates
- Image compression ratio (target: 60-70% reduction)

## Risk Mitigation

### Technical Risks

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Vision API rate limits | Claims not processed | Exponential backoff, concurrency control, fallback decision |
| Database connection failures | Claims blocked | Connection pooling, automatic retries, circuit breaker |
| Large image uploads | Storage bloat | Compress to WebP, validate size, enforce limits |
| Vision API costs growing | Budget overrun | Cache results, batch requests, monitor token usage |
| Cache misses on startup | Performance spikes | Lazy load on miss, warm cache periodically |

### Operational Risks

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Manual reviewers overwhelmed | Decision bottleneck | Tune risk thresholds, improve claim routing |
| User history data stale | Inaccurate risk assessment | Cache invalidation on claim decision, 1-hour TTL |
| Audit trail loss | Compliance violation | Immutable audit logs in database, daily backups |
| Image privacy | Data breach | Signed URLs with 1-hour expiration, GDPR compliance |

## Success Criteria Status

- [ ] Can process single claim in <5 seconds
- [ ] Batch processing 1,000 claims in <10 minutes
- [ ] Vision analysis 90%+ consistent with humans (TBD after implementation)
- [ ] Risk flags identify 95%+ high-risk claims (TBD after implementation)
- [ ] Dashboard loads in <2 seconds with 10K claims
- [ ] Complete audit trail on every decision
- [ ] Image storage optimized (60-70% compression)
- [ ] Zero data loss on job interruption

## Next Session Goals

1. Initialize Next.js 15 project with TypeScript strict mode
2. Set up authentication with Clerk
3. Create Prisma schema and database
4. Deploy to Vercel
5. Implement basic claim submission flow (stub vision analysis)
