# AGENTS.md: ClaimVerify Development Rules

## Overview

This is a damage claim verification system built with Next.js 15, TypeScript, and Claude Vision API. The system processes vehicle, laptop, and package damage claims through image analysis and risk assessment.

Before implementing **ANY** feature, read the following in order:

1. `project-overview.md` — product definition, goals, features, success criteria
2. `architecture-context.md` — system structure, boundaries, data model, invariants
3. `ui-context.md` — design system, component patterns, responsive behavior
4. `code-standards.md` — implementation conventions, typing, styling
5. `ai-workflow-rules.md` — development methodology, scoping, session workflow
6. `progress-tracker.md` — current phase, completed work, next steps

**Update `progress-tracker.md` after each meaningful change.**

## Technology Choices

### Why Next.js 15?
- App Router with Server Components (default): Reduces JavaScript sent to browser
- Built-in image optimization: `next/image` with automatic compression
- Request deduplication: Same request in single render → cached
- Incremental Static Revalidation: Cache pages, revalidate on-demand
- API routes with middleware: Built-in auth, validation
- Vercel deployment: 0-config, serverless functions, blob storage

### Why Claude 3.5 Vision?
- Fastest vision model with strong accuracy
- Handles all image formats (JPG, PNG, WebP)
- Can detect damage, estimate severity, identify object parts
- Cacheable results: avoid duplicate analyses on same image

### Why PostgreSQL + Prisma?
- PostgreSQL: relational, ACID transactions, indexing
- Prisma: type-safe queries, auto migrations, connection pooling
- Suitable for: users, claims, decisions, audit logs (structured data)

### Why Redis?
- Sub-100ms lookups for user history and evidence requirements
- Caching vision results by image hash prevents duplicate analyses
- Session storage if scaling beyond serverless

### Why Vercel Blob?
- Seamless integration with Next.js/Vercel
- Automatic CDN for image serving
- Cost-effective ($0.06/GB/month)
- Native support for time-limited signed URLs

### Why shadcn/ui?
- Accessible component library
- Dark mode support out-of-the-box
- No breaking updates (static components in repo)
- Minimal opinionation: use as-is or customize

## Architecture Decisions

### Server-First Design
- Load claims and initial data on server (fast, no loading spinners)
- Use Server Components by default
- Client Components only for real-time updates (status polling)
- API routes thin: validation + database operations, logic in `/lib`

### Separated Storage Layers
- **PostgreSQL**: Metadata, relationships, audit logs
- **Vercel Blob**: Images (compressed), image metadata
- **Redis**: Cache for frequent lookups (user history, evidence requirements)

**Why separate?** Database would overflow with image data. Blob storage is cheap and fast.

### Durable Job Processing
- Background jobs via BullMQ + Redis (or Trigger.dev)
- No synchronous vision API calls in request handlers
- Jobs resumable: failures don't lose progress
- Idempotent: can retry safely without duplication

### Evidence-Based Decisions
- Decisions grounded in image analysis (primary source of truth)
- User history adds risk context, doesn't override visual evidence
- All decisions include supporting image IDs for auditability

## Core Workflows

### Claim Submission Flow

```
User submits claim
  ↓
POST /api/claims
  ├─ Validate: auth, claim format, image count
  ├─ Upload images to Blob storage (compress to WebP)
  ├─ Save Claim record (status: "submitted")
  ├─ Enqueue BullMQ job
  └─ Return claimId
         ↓
[Background Job]
  ├─ Load claim + images
  ├─ Load evidence requirements (from cache)
  ├─ Load user history (from cache)
  ├─ For each image:
  │   ├─ Check vision cache (by hash)
  │   ├─ If miss: call Claude Vision
  │   └─ Cache result
  ├─ Evaluate evidence standard
  ├─ Generate decision (supported/contradicted/insufficient)
  ├─ Flag risks (history, image quality)
  ├─ Save ClaimDecision record
  ├─ Create AuditLog entry
  └─ Update Claim status
         ↓
GET /api/claims/{id}
  └─ Return full claim + decision + images
```

### Dashboard Display Flow

```
User loads dashboard
  ↓
GET /dashboard (Server Component)
  ├─ Fetch claims (with decision) from DB
  ├─ Cache results (revalidate every 30 seconds)
  └─ Render table with status badges, risk indicators
         ↓
User filters/searches
  └─ Client-side filter (no new request) + URL update
         ↓
User clicks claim detail
  └─ GET /dashboard/claims/[id]
     ├─ Fetch claim + images from DB/Blob
     ├─ Generate signed image URLs
     └─ Render detail view
```

### Risk Assessment Flow

```
During job processing:
  Load user history
    ├─ Check Redis cache (1-hour TTL)
    ├─ If miss: query DB
    └─ Cache result
         ↓
  Evaluate risk factors
    ├─ Past claim count
    ├─ Acceptance rate
    ├─ Recent claim spike
    ├─ Image quality flags
    ├─ Claim-to-history mismatch
    └─ Generate risk score (0-100)
         ↓
  Flag high-risk claims
    └─ Mark for manual review if score > 60
```

## Key Invariants

**Violating these breaks the system:**

1. **No long-running work in request handlers**
   - Vision API calls belong in BullMQ jobs
   - Claim processing happens async, not in POST /api/claims

2. **Decisions are immutable** (but reviewable)
   - Once saved, decision doesn't change
   - Human override creates new AuditLog entry, not mutation

3. **Image storage separated from database**
   - Images live in Blob storage
   - DB stores only the path + metadata

4. **User history cached with TTL**
   - Prevents expensive DB queries on every claim
   - Cache invalidated on manual update

5. **Evidence requirements configured, not hardcoded**
   - Load from `EvidenceRequirement` table
   - Cache with 24-hour TTL
   - Centralized updates for compliance

6. **Every decision includes audit context**
   - Who/what decided? (system or human)
   - Image IDs supporting the decision
   - Risk flags evaluated
   - Timestamp and token usage

7. **Failures don't lose work**
   - BullMQ jobs persist state
   - Failed claims can be retried
   - Database transactions prevent partial updates

## Performance Targets

| Operation | Target | Key Implementation |
|-----------|--------|-------------------|
| Submit claim | <3 sec | Upload + queue, async processing |
| Process claim | <5 sec | Cached history, cached vision results |
| Load dashboard | <2 sec | Paginated queries, Redis cache |
| Vision analysis | <2 sec | Claude 3.5 Vision, result caching |
| User history lookup | <100 ms | Redis cache, 1-hour TTL |

## Cost Optimization

### Image Storage
- Compress to WebP: saves 60-70% vs JPEG
- Delete images after legal retention period
- Use Vercel Blob (pay per GB) vs S3 (pay per request)

### Vision API
- Cache results by image hash (avoid duplicate analyses)
- Batch image descriptions when possible
- Set max tokens per request (4096 tokens per image)
- Monitor token usage in logs

### Database
- Connection pooling (Prisma)
- Indexes on frequently queried columns
- Archive old claims after 1 year
- Use read replicas for dashboard queries (if scaling)

### Monitoring Metrics
- Vision API calls per claim (should be 1-5)
- Cache hit rate on user history (target: >80%)
- Database query time (p95 <500ms)
- Job processing time distribution
- Total cost per claim processed

## Error Scenarios

### Vision API Rate Limit
- Implement exponential backoff (3 retries max)
- Set BullMQ job concurrency to avoid overload
- Flag image with `valid_image: false` if call fails
- Mark claim as `not_enough_information`

### Database Connection Failure
- Prisma auto-retries
- Log error, mark job for retry
- User sees "Processing" until job succeeds

### Image Upload Timeout
- User can retry upload
- Temporary files cleaned up after 24 hours
- Log for monitoring

### Corrupted Evidence Requirement Cache
- Fall back to database query
- Log cache miss
- Update cache on successful fetch

## Monitoring & Alerts

### Key Metrics to Log

```typescript
logger.info("Claim processing completed", {
  claimId: string,
  status: "supported" | "contradicted" | "not_enough_information",
  riskScore: number (0-100),
  processingTimeMs: number,
  imagesAnalyzed: number,
  tokensUsed: number,
  estimatedCost: number (USD),
  cacheHits: {
    vision: number,
    userHistory: boolean,
    evidenceRequirements: boolean,
  },
  flagsRaised: string[], // ["blurry_image", "user_history_risk", ...]
});
```

### Dashboard Health Checks
- [ ] Claim submission success rate (target: >99%)
- [ ] Average processing time (target: <5 sec)
- [ ] Manual review rate (target: <15% of claims)
- [ ] Vision API error rate (target: <0.1%)
- [ ] Cache hit rate (target: >80%)

## Deployment Checklist

Before deploying to production:

- [ ] All TypeScript types strict mode
- [ ] All tests passing
- [ ] Database migrations tested locally
- [ ] Vision API integrated and tested
- [ ] Image compression working
- [ ] Redis connection tested
- [ ] BullMQ jobs processed end-to-end
- [ ] Dashboard responsive on mobile
- [ ] All logging in place
- [ ] Monitoring dashboard set up
- [ ] Error handling covers main failure modes
- [ ] Documentation up-to-date
- [ ] Performance targets met in staging

## Development Tips

### Local Setup
```bash
# Clone and install
git clone ...
npm install

# Set up environment
cp .env.example .env.local
# Fill in: Clerk keys, DB URL, Vision API key, Redis URL

# Run migrations
npx prisma migrate dev

# Start dev server
npm run dev

# Monitor job queue
npm run jobs:monitor
```

### Testing Vision Analysis
Create test images with known damage:
- Dented bumper (car)
- Cracked screen (laptop)
- Crushed corner (package)

Test image quality issues:
- Blurry image
- Dark/low light
- Cropped or obstructed
- Wrong angle

### Debugging Failed Jobs
```typescript
// Check job status
const job = await claimsQueue.getJob(jobId);
console.log(job.state, job.progress(), job.data, job.failedReason);

// Retry job
await job.retry();

// Inspect logs for this claim
const logs = await db.auditLog.findMany({
  where: { claimId },
  orderBy: { createdAt: "desc" },
});
```

### Profiling Performance
```typescript
// In your claim processor
const startTime = Date.now();

// ... processing ...

const duration = Date.now() - startTime;
logger.info("Processing duration", { claimId, duration, phase: "vision_analysis" });
```

## Integration Points

### Future: External Claims System
API endpoint to export decisions:
```
POST /api/webhooks/export
Body: { claimId, decision, imageIds }
```

### Future: Underwriting Override
API endpoint to accept human review:
```
POST /api/claims/{id}/review
Body: { reviewedBy, decision, override, notes }
```

## References

- Claude API: https://docs.anthropic.com
- Next.js: https://nextjs.org/docs
- Prisma: https://www.prisma.io/docs
- shadcn/ui: https://ui.shadcn.com
- Vercel Blob: https://vercel.com/docs/storage/vercel-blob
