# Architecture Context: ClaimVerify

## Stack

| Layer               | Technology                   | Role                                                  |
|-------------------|------------------------------|-------------------------------------------------------|
| **Framework**      | Next.js 15 + TypeScript      | Full-stack: server components, API routes, caching   |
| **Auth**           | Clerk                        | User identity and route protection                   |
| **Database**       | PostgreSQL + Prisma          | Claims, users, evidence rules, audit logs            |
| **Cache**          | Redis (Upstash)              | User history, evidence requirements, results         |
| **Vision AI**      | Claude 3.5 Vision API        | Image analysis, damage detection, severity estimation|
| **Task Queue**     | Bull/BullMQ + Redis          | Durable job processing for batch claims              |
| **Image Storage**  | Vercel Blob / S3             | Claim images with automatic compression              |
| **UI Components**  | shadcn/ui + Tailwind CSS     | Dark-themed dashboard and interfaces                 |
| **CSV Processing** | csv-parser / papaparse       | Efficient streaming CSV import and export            |
| **Monitoring**     | PostHog / Sentry             | Usage analytics and error tracking                   |

## System Boundaries

### Frontend (`app/`)
- **Public routes** (`/auth/*`): Sign-up, sign-in, password reset via Clerk
- **Protected routes** (`/dashboard/*`): Claim submission, review, results
- **API routes** (`/api/*`): Request handlers with auth and ownership checks
- **Real-time components**: Claim status polling, dashboard updates
- Server Components by default; Client Components only for interactivity

### Backend Services

#### **Claim Processing** (`lib/claim-processor/`)
- Extract claim from user transcript
- Validate image count against evidence requirements
- Orchestrate vision analysis for each image
- Aggregate results into final decision
- Evaluate user history for risk flags
- Return structured decision with confidence scores

#### **Vision Analysis** (`lib/vision/`)
- Image preprocessing (format validation, size checks)
- Call Claude 3.5 Vision for damage detection
- Parse vision response into structured types
- Cache vision analysis results by image hash
- Handle rate limiting and retries gracefully

#### **User Risk** (`lib/risk/`)
- Load user claim history from cache (Redis)
- Evaluate past claim patterns and acceptance rate
- Identify high-risk behaviors (recent rejections, spikes in claims)
- Generate risk flags with confidence levels
- Cache lookups with 1-hour TTL

#### **Evidence Validation** (`lib/evidence/`)
- Load evidence requirements from cache
- Match claim object + issue type to requirement
- Count images meeting standard (quality checks passed)
- Flag insufficient evidence with guidance
- Cache requirements with 24-hour TTL

#### **Job Processing** (`lib/jobs/`)
- Batch claim processing with concurrency control
- Progress tracking and resumable processing
- Error handling with automatic retries
- Cost and token tracking per batch
- Export results to CSV

#### **Image Management** (`lib/images/`)
- Image upload handling with format validation
- Automatic resizing and compression (WebP format)
- Unique file naming and storage path management
- Metadata extraction (dimensions, format, upload time)
- Secure public URLs with expiration

### Database Schema

```prisma
model User {
  id          String  @id @default(cuid())
  clerkId     String  @unique
  email       String  @unique
  name        String?
  role        String  @default("claimant") // claimant, reviewer, admin
  createdAt   DateTime @default(now())
  updatedAt   DateTime @updatedAt
  
  claims      Claim[]
  decisions   ClaimDecision[]
}

model Claim {
  id              String  @id @default(cuid())
  userId          String
  user            User    @relation(fields: [userId], references: [id], onDelete: Cascade)
  
  claimObject     String  // car, laptop, package
  userTranscript  String  @db.Text // full chat conversation
  imagePaths      String  // semicolon-separated image file paths
  
  status          String  @default("submitted") // submitted, processing, completed
  decision        ClaimDecision?
  
  createdAt       DateTime @default(now())
  updatedAt       DateTime @updatedAt
  
  @@index([userId])
  @@index([status])
  @@index([createdAt])
}

model ClaimDecision {
  id                        String  @id @default(cuid())
  claimId                   String  @unique
  claim                     Claim   @relation(fields: [claimId], references: [id], onDelete: Cascade)
  
  // Evidence
  evidenceStandardMet       Boolean
  evidenceStandardMetReason String  @db.Text
  validImage                Boolean
  
  // Analysis
  issueType                 String  // dent, scratch, crack, etc.
  objectPart                String  // bumper, screen, corner, etc.
  severity                  String  // none, low, medium, high, unknown
  
  // Decision
  claimStatus               String  // supported, contradicted, not_enough_information
  claimStatusJustification  String  @db.Text
  supportingImageIds        String  // semicolon-separated image file IDs
  
  // Risk
  riskFlags                 String  // semicolon-separated flags: user_history_risk, blurry_image, etc.
  riskScore                 Float   @default(0) // 0-100
  
  // Metadata
  processingTimeMs          Int?
  tokensUsed                Int?
  costEstimate              Float?
  
  createdAt                 DateTime @default(now())
  updatedAt                 DateTime @updatedAt
  reviewedAt                DateTime?
  reviewedBy                String?
  
  @@index([claimId])
  @@index([claimStatus])
  @@index([createdAt])
}

model EvidenceRequirement {
  id              String  @id @default(cuid())
  requirementId   String  @unique
  claimObject     String  // car, laptop, package, all
  appliesTo       String  // issue family: dent or scratch, glass break, etc.
  minimumEvidence String  @db.Text // description of minimum evidence needed
  minimumImages   Int     @default(1)
  
  createdAt       DateTime @default(now())
  updatedAt       DateTime @updatedAt
  
  @@index([claimObject])
  @@index([appliesTo])
}

model UserHistory {
  id                      String  @id @default(cuid())
  userId                  String  @unique
  
  pastClaimCount          Int     @default(0)
  acceptedClaims          Int     @default(0)
  manualReviewClaims      Int     @default(0)
  rejectedClaims          Int     @default(0)
  last90DaysClaimCount    Int     @default(0)
  
  historyFlags            String? // flags: high_rejection_rate, recent_spike, etc.
  historySummary          String? @db.Text
  riskLevel               String  @default("none") // none, low, medium, high
  
  lastClaimAt             DateTime?
  lastUpdatedAt           DateTime @default(now())
  
  @@index([riskLevel])
}

model AuditLog {
  id              String  @id @default(cuid())
  claimId         String
  action          String  // decision_made, decision_overridden, manual_review_flagged
  actor           String  // system, user_id, admin_id
  details         String  @db.Json
  previousState   String? @db.Json
  newState        String? @db.Json
  
  createdAt       DateTime @default(now())
  
  @@index([claimId])
  @@index([createdAt])
}

model Image {
  id              String  @id @default(cuid())
  claimId         String
  fileName        String
  fileHash        String  @unique
  storagePath     String  // s3://bucket/claims/xxx/img_1.webp
  originalPath    String  // dataset/images/test/case_001/img_1.jpg
  
  width           Int?
  height          Int?
  format          String? // jpg, png, webp
  fileSizeBytes   Int?
  
  analysisCache   String? @db.Json // cached vision analysis result
  analysisDone    Boolean @default(false)
  
  uploadedAt      DateTime @default(now())
  
  @@index([claimId])
  @@index([fileHash])
}
```

## Storage Model

### Database (PostgreSQL)
- **Metadata**: users, claims, decisions, evidence requirements, audit logs
- **Relationships**: ownership, claim-decision links, claim-image associations
- **Indexed heavily**: claim status, timestamps, user lookups for fast queries
- **Immutable audit log**: every decision recorded with actor, timestamp, details

### Cache (Redis via Upstash)
- **User history**: cached with 1-hour TTL (high read, low write)
- **Evidence requirements**: cached with 24-hour TTL (stable configuration)
- **Vision analysis**: cached by image hash with 7-day TTL (prevent duplicate analysis)
- **Dashboard aggregations**: claims by status with hourly update

### Image Storage (Vercel Blob / S3)
- **Original images**: `/claims/{claimId}/{imageId}.webp` (compressed, ~200KB average)
- **URL generation**: secure, time-limited URLs for browser preview
- **Retention**: match legal/insurance requirements (default 7 years)
- **Compression**: lossless WebP conversion to reduce storage cost by 60-70%

## Data Flow

```
User submits claim
    ↓
POST /api/claims (auth enforced)
    ├─ Validate images (format, size)
    ├─ Store images to blob storage
    ├─ Create Claim record in DB
    └─ Enqueue job in BullMQ
         ↓
[Background Job: Process Claim]
    ├─ Load claim + images
    ├─ Load user history from cache
    ├─ Load evidence requirements from cache
    ├─ For each image:
    │   ├─ Check vision cache (by hash)
    │   ├─ If miss: call Claude Vision API
    │   └─ Cache result in Redis
    ├─ Evaluate evidence standard
    ├─ Generate decision (supported/contradicted/insufficient)
    ├─ Flag risks (user history, image quality, etc.)
    ├─ Save ClaimDecision record
    ├─ Create AuditLog entry
    └─ Emit webhook (if configured)
         ↓
GET /api/claims/{id} (real-time fetch)
    ├─ Load Claim + ClaimDecision from DB
    ├─ Generate signed image URLs
    └─ Return to dashboard
```

## Auth & Access Control

- **Public routes**: `/`, `/auth/*`
- **Protected routes**: All `/dashboard/*` and `/api/*` routes require Clerk auth
- **Authorization checks**:
  - User can only view their own claims
  - Only reviewers/admins can override decisions
  - Admin-only routes for user history and system config
- **Audit**: Every decision change logged with actor and timestamp

## Invariants

1. **No synchronous AI calls in request handlers** — vision analysis always runs in background jobs
2. **Evidence requirements cached, not queried on every claim** — reduce database load
3. **User history cached with TTL** — prevent stale risk assessment
4. **Image storage separated from database** — blob storage for images, DB for references
5. **Decisions immutable, overrides logged** — audit trail integrity
6. **Vision results cached by image hash** — prevent duplicate API calls
7. **Batch processing resumable** — failed jobs can retry without reprocessing completed claims
8. **All timestamps UTC** — no timezone ambiguity in audit logs

## Performance Targets

| Operation | Target | Method |
|-----------|--------|--------|
| Single claim processing | <5 sec | Cached vision, parallel image analysis |
| Batch processing (1K claims) | <10 min | Concurrency control, job queuing |
| Dashboard load (10K claims) | <2 sec | Indexed queries, Redis cache, pagination |
| Image analysis API call | <2 sec | Claude Vision, cached results |
| User history lookup | <100 ms | Redis cache with 1-hour TTL |
| Evidence requirement lookup | <50 ms | Redis cache with 24-hour TTL |

## Scaling Strategy

### Database
- Use connection pooling (Prisma)
- Index on frequently queried fields (userId, status, createdAt)
- Archive old claims to separate table after 1 year
- Use read replicas for dashboard queries

### Vision API
- Implement exponential backoff retry (3 retries max)
- Batch image analysis calls where possible
- Cache vision results by image hash (Redis)
- Monitor token usage and set per-batch limits

### Image Storage
- Compress images to WebP before upload
- Use CDN for image serving
- Implement lazy loading on dashboard
- Archive old images to cheaper storage tier (Glacier) after 1 year

### Background Jobs
- Use BullMQ with concurrency limits (max 10 concurrent jobs)
- Monitor job queue depth; alert if >100 pending
- Implement circuit breaker for vision API rate limits
- Exponential backoff on failures (max 3 retries)

## Error Handling

- **Vision API failures**: Log error, flag image as `valid_image: false`, mark claim as `not_enough_information`
- **Database connection failures**: Retry with exponential backoff, fail the job after 3 attempts
- **Image storage failures**: Retry with exponential backoff, mark as failed in job metadata
- **Cache misses**: Fall through to database/API, update cache on success
- **Malformed user input**: Validate at API boundary, return 400 with error details
