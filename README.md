# ClaimVerify: Multi-Modal Damage Claim Verification System

**Enterprise-grade insurance claim processing powered by AI vision analysis, risk assessment, and audit-trail completeness.**

![Status](https://img.shields.io/badge/Status-In%20Development-yellow)
![License](https://img.shields.io/badge/License-MIT-green)
![TypeScript](https://img.shields.io/badge/TypeScript-Strict-blue)

---

## Table of Contents

- [Quick Overview](#quick-overview)
- [Key Features](#key-features)
- [Architecture](#architecture)
- [Getting Started](#getting-started)
- [Project Structure](#project-structure)
- [Development Guide](#development-guide)
- [Deployment](#deployment)
- [Contributing](#contributing)
- [License](#license)

---

## Quick Overview

**ClaimVerify** automates damage claim verification for insurance companies. Claimants submit photos of damaged items (vehicles, laptops, packages) with a chat description. The system analyzes images using Claude Vision, validates evidence against requirements, assesses user risk, and returns a decision: **Supported**, **Contradicted**, or **Needs More Information**.

### Core Value

- **Fast**: 95% of claims processed in <5 seconds
- **Accurate**: Vision-grounded decisions with complete audit trail
- **Scalable**: Processes 1,000+ claims/day cost-effectively
- **Compliant**: Immutable decision logs for insurance regulations

### Real-World Example

```
User: "My car's front bumper is dented from the accident"
Uploads: [front-bumper-1.jpg, front-bumper-2.jpg, detail.jpg]

System analysis:
✓ Image quality: Clear, well-lit, multiple angles
✓ Damage detected: Dent on front bumper (severity: medium)
✓ Evidence standard: Met (3 images, clear damage visible)
✓ User history: Low risk (clean claim record)
✓ Risk flags: None

Decision: SUPPORTED
Justification: Clear dent visible in multiple angles. 
Supporting images: img_1, img_2
Processing time: 4.2 seconds
Cost: $0.01 (vision analysis)
```

---

## Key Features

### Claimant Portal
- [ ] Submit damage claim with images and description
- [ ] Chat-based claim description
- [ ] Real-time processing status
- [ ] Instant decision and next steps

### Operational Dashboard
- [ ] Claims list with status, risk, and severity
- [ ] Advanced search and filtering
- [ ] Claim detail view with full analysis
- [ ] Image gallery with vision annotations
- [ ] Manual review queue for flagged claims
- [ ] Analytics dashboard (claims by status, risk distribution)

### Core Processing
- [x] Multi-image damage claim analysis
- [x] Claude Vision API integration
- [x] Evidence requirement validation
- [x] User risk history evaluation
- [x] Automated decision generation
- [x] Complete audit trail with image links

### Risk Assessment
- [x] User claim history analysis
- [x] Claim pattern detection (spikes, rejections)
- [x] Image quality scoring
- [x] Claim-to-history mismatch flagging
- [x] Manual review recommendation

### Integration
- [x] Batch CSV import for bulk processing
- [x] API endpoints for external systems
- [x] Webhook export for claims management systems
- [x] Cost tracking and performance monitoring

---

## Architecture

### High-Level Design

```
┌──────────────────────────────────────────────────┐
│               Frontend (Next.js)                 │
│  Dashboard | Claim Submission | Admin Interface │
└────────────────────┬─────────────────────────────┘
                     │
┌────────────────────▼─────────────────────────────┐
│             API Routes & Auth                    │
│  POST /claims | GET /claims/{id} | POST /batch  │
└────────────────────┬─────────────────────────────┘
                     │
┌────────────────────▼─────────────────────────────┐
│        Business Logic & Services                 │
│  ClaimProcessor | VisionAnalyzer | RiskAssessment│
│  EvidenceValidator | ImageHandler | CacheManager │
└────────────────────┬─────────────────────────────┘
                     │
         ┌───────────┼───────────┐
         │           │           │
    ┌────▼──┐  ┌────▼──┐  ┌────▼──┐
    │ PostgreSQL │ Vercel │  │ Redis  │
    │  (metadata)│ Blob   │  │(cache) │
    │            │(images)│  │        │
    └───────┘  └────────┘  └────────┘
```

### Technology Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| **Framework** | Next.js 15 + TypeScript | App Router, Server Components, built-in optimization |
| **Auth** | Clerk | Sign-up/sign-in, organizations, webhooks |
| **Database** | PostgreSQL + Prisma | Relational, ACID transactions, type-safe ORM |
| **Cache** | Redis (Upstash) | User history, vision results, evidence requirements |
| **Vision AI** | Claude 3.5 Vision | Fastest model, handles all image formats, cacheable |
| **Jobs** | BullMQ + Redis | Durable, resumable, observable |
| **Storage** | Vercel Blob | Integrated, cheap, CDN-backed, auto-compression |
| **UI** | shadcn/ui + Tailwind | Accessible, dark mode, minimal config |

### Data Model

```
User
├─ id, email, role (claimant, reviewer, admin)
├─ Claim[]
└─ ClaimDecision[]

Claim
├─ id, userId, claimObject (car, laptop, package)
├─ transcript (user chat)
├─ imagePaths (semicolon-separated)
├─ status (submitted, processing, completed, failed)
└─ decision → ClaimDecision

ClaimDecision
├─ evidenceStandardMet (boolean)
├─ issueType (dent, scratch, crack, etc.)
├─ objectPart (bumper, screen, corner, etc.)
├─ severity (low, medium, high)
├─ claimStatus (supported, contradicted, not_enough_information)
├─ supportingImageIds (image IDs backing decision)
├─ riskFlags (blurry_image, user_history_risk, etc.)
├─ riskScore (0-100)
└─ audit fields (createdAt, reviewedBy, reviewedAt)

EvidenceRequirement
├─ claimObject (car, laptop, package)
├─ appliesTo (issue family)
└─ minimumEvidence, minimumImages

UserHistory
├─ userId
├─ pastClaimCount, acceptedClaims, rejectedClaims
├─ last90DaysClaimCount
└─ riskLevel, historyFlags

AuditLog
├─ claimId, action, actor
├─ previousState, newState
└─ timestamp

Image
├─ claimId, fileName, fileHash
├─ storagePath (Blob URL)
├─ width, height, fileSize
└─ analysisCache (vision result)
```

---

## Getting Started

### Prerequisites

- **Node.js 18+** (use `nvm` or `asdf`)
- **PostgreSQL 13+** (local or managed)
- **Redis** (local with `redis-cli` or Upstash)
- **API Keys**:
  - Anthropic (Claude API)
  - Clerk (authentication)
  - Vercel (Blob storage, if using Vercel)

### Installation (5 minutes)

```bash
# 1. Clone repository
git clone https://github.com/yourusername/claimverify.git
cd claimverify

# 2. Install dependencies
npm install

# 3. Set up environment
cp .env.example .env.local

# 4. Fill in .env.local with your keys:
# NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...
# CLERK_SECRET_KEY=sk_test_...
# DATABASE_URL=postgresql://user:pass@localhost/claimverify
# REDIS_URL=redis://localhost:6379
# ANTHROPIC_API_KEY=sk-ant-...

# 5. Initialize database
npx prisma db push
npx prisma db seed

# 6. Start development server
npm run dev

# 7. In another terminal, start job worker
npm run jobs:worker
```

Visit **http://localhost:3000**

### First Claim (Manual Test)

1. Sign up at http://localhost:3000/sign-up
2. Go to Dashboard
3. Click "Submit Claim"
4. Fill in:
   - **Object**: Car
   - **Transcript**: "Front bumper is dented"
   - **Images**: Upload 2-3 photos of car bumper damage
5. Submit
6. Watch the job process in terminal
7. View decision in dashboard

---

## Project Structure

```
claimverify/
├─ app/
│  ├─ api/                       # API routes
│  │  ├─ claims/                 # POST claim, GET claim detail
│  │  ├─ batch/                  # POST batch CSV processing
│  │  ├─ images/                 # POST image upload
│  │  └─ health/                 # GET /api/health
│  ├─ dashboard/                 # Protected pages
│  │  ├─ page.tsx               # Claims dashboard
│  │  ├─ claims/[id]/page.tsx   # Claim detail
│  │  └─ admin/                 # Admin features
│  ├─ auth/                      # Clerk callbacks
│  ├─ layout.tsx                 # Root layout
│  └─ page.tsx                   # Landing page
│
├─ components/
│  ├─ ui/                        # shadcn/ui (do not modify)
│  ├─ dashboard/                 # Dashboard components
│  │  ├─ ClaimsTable.tsx
│  │  ├─ ClaimCard.tsx
│  │  ├─ ClaimDetailView.tsx
│  │  └─ DashboardHeader.tsx
│  ├─ claim/                     # Claim submission
│  │  ├─ ClaimForm.tsx
│  │  ├─ ImageUpload.tsx
│  │  └─ ClaimTranscript.tsx
│  └─ common/                    # Reusable
│     ├─ StatusBadge.tsx
│     ├─ RiskBadge.tsx
│     ├─ ImageGallery.tsx
│     └─ LoadingState.tsx
│
├─ lib/
│  ├─ claim-processor/           # Core processing
│  │  ├─ index.ts               # Main orchestrator
│  │  ├─ decision-engine.ts     # Decision logic
│  │  └─ types.ts               # TypeScript types
│  ├─ vision/                    # Claude Vision
│  │  ├─ index.ts               # Image analysis
│  │  ├─ cache.ts               # Result caching
│  │  └─ types.ts               # VisionAnalysis type
│  ├─ risk/                      # Risk assessment
│  │  ├─ index.ts               # Risk evaluation
│  │  ├─ history.ts             # User history
│  │  └─ flags.ts               # Risk flags
│  ├─ evidence/                  # Evidence validation
│  │  ├─ index.ts               # Requirement checking
│  │  └─ cache.ts               # Requirement caching
│  ├─ images/                    # Image handling
│  │  ├─ index.ts               # Upload logic
│  │  ├─ storage.ts             # Blob integration
│  │  └─ validation.ts          # Format validation
│  ├─ jobs/                      # Background jobs
│  │  ├─ index.ts               # Queue setup
│  │  ├─ processors.ts          # Job handlers
│  │  └─ monitor.ts             # Job monitoring
│  ├─ db/                        # Database
│  │  ├─ client.ts              # Prisma singleton
│  │  ├─ claim.ts               # Claim queries
│  │  ├─ user.ts                # User queries
│  │  └─ audit.ts               # Audit logging
│  ├─ cache/                     # Redis
│  │  ├─ index.ts               # Redis client
│  │  ├─ keys.ts                # Key generation
│  │  └─ ttls.ts                # TTL constants
│  ├─ auth/                      # Auth helpers
│  │  ├─ index.ts               # Auth checks
│  │  └─ permissions.ts         # Permission checks
│  └─ utils/                     # Utilities
│     ├─ logger.ts              # Structured logging
│     ├─ errors.ts              # Error types
│     ├─ csv.ts                 # CSV parsing
│     └─ validation.ts          # Input validation
│
├─ prisma/
│  ├─ schema.prisma              # Database schema
│  └─ seed.ts                    # Seed script
│
├─ jobs/
│  └─ claim-processor.ts         # BullMQ worker
│
├─ tests/
│  ├─ unit/                      # Unit tests
│  ├─ integration/               # API tests
│  └─ fixtures/                  # Test data
│
├─ public/
│  └─ images/                    # Static assets
│
├─ styles/
│  └─ globals.css                # CSS tokens, theme
│
├─ .env.example                  # Environment template
├─ .env.local                    # Secrets (git-ignored)
├─ package.json
├─ tsconfig.json                 # TypeScript strict
├─ next.config.js                # Next.js config
├─ tailwind.config.js            # Tailwind theme
├─ prisma.config.js              # Prisma config
└─ README.md                     # This file
```

---

## Development Guide

### Context Files

Before implementing any feature, read these in order:

1. **`project-overview.md`** — Product definition, goals, features
2. **`architecture-context.md`** — System structure, data model, invariants
3. **`ui-context.md`** — Design system, component patterns
4. **`code-standards.md`** — TypeScript, Next.js, styling conventions
5. **`ai-workflow-rules.md`** — Development methodology, scoping
6. **`AGENTS.md`** — Agent rules, key workflows, performance targets
7. **`progress-tracker.md`** — Current state, next steps, open questions

### Development Workflow

```bash
# 1. Read the feature spec in context files
# 2. Create a branch
git checkout -b feat/claim-status-notifications

# 3. Implement (keep scope small!)
# - Frontend: 1 component
# - Backend: 1 API route or 1 service
# - Database: 1 schema change

# 4. Write tests
npm test -- claim-status.test.ts

# 5. Check types
npm run type-check

# 6. Update progress tracker
# Edit progress-tracker.md with what you completed

# 7. Commit with clear message
git commit -m "feat: Add claim status notifications (email on decision)"

# 8. Push and create PR
git push origin feat/claim-status-notifications
```

### Key Commands

```bash
# Development
npm run dev                    # Start dev server + job worker
npm run dev:server             # Dev server only
npm run jobs:worker            # Job worker only

# Database
npx prisma db push             # Apply schema changes
npx prisma db seed             # Run seed script
npx prisma studio              # Visual DB browser
npx prisma migrate dev --name name_of_migration

# Testing
npm test                       # Run all tests
npm test -- claim.test.ts      # Run specific test
npm test -- --watch            # Watch mode

# Code Quality
npm run type-check             # TypeScript check
npm run lint                   # ESLint
npm run format                 # Prettier (auto-format)

# Build & Deploy
npm run build                  # Production build
npm start                      # Run production build locally
```

### Common Tasks

#### Add a new API endpoint

1. Create file `app/api/[resource]/route.ts`
2. Implement `GET`, `POST`, etc. handler functions
3. Add auth check using `auth()` from Clerk
4. Validate input using `zod` schemas
5. Call business logic from `lib/`
6. Return typed response

```typescript
// app/api/claims/[id]/route.ts
import { auth } from "@clerk/nextjs/server";
import { getClaim } from "@/lib/db/claim";
import { ClaimNotFoundError } from "@/lib/utils/errors";

export async function GET(
  request: Request,
  { params }: { params: { id: string } }
) {
  const user = auth();
  if (!user.userId) return Response.json({ error: "Unauthorized" }, { status: 401 });

  try {
    const claim = await getClaim(params.id, user.userId);
    return Response.json(claim);
  } catch (error) {
    if (error instanceof ClaimNotFoundError) {
      return Response.json({ error: "Not found" }, { status: 404 });
    }
    return Response.json({ error: "Server error" }, { status: 500 });
  }
}
```

#### Add a new database table

1. Edit `prisma/schema.prisma`
2. Run migration: `npx prisma migrate dev --name add_table_name`
3. Update types in `lib/` as needed
4. Create query helpers in `lib/db/`

#### Add a new UI component

1. Create in `components/` (not in `components/ui/`)
2. Use shadcn/ui components from `components/ui/`
3. Use CSS variables for colors (no hardcoded hex)
4. Make responsive: mobile-first, check tablet & desktop
5. Test with dark theme

```typescript
// components/dashboard/NewFeature.tsx
"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";

interface Props {
  claimId: string;
  onSuccess?: () => void;
}

export function NewFeature({ claimId, onSuccess }: Props) {
  const [isLoading, setIsLoading] = useState(false);

  const handleClick = async () => {
    setIsLoading(true);
    try {
      const res = await fetch(`/api/claims/${claimId}/action`, { method: "POST" });
      if (res.ok) onSuccess?.();
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Button onClick={handleClick} disabled={isLoading}>
      {isLoading ? "Loading..." : "Do Thing"}
    </Button>
  );
}
```

#### Monitor job processing

```bash
# Terminal 1: Start job worker
npm run jobs:worker

# Terminal 2: Check job status
node -e "
const { claimsQueue } = require('./lib/jobs');
claimsQueue.getJobCounts().then(console.log);
"

# Output:
# {
#   active: 2,
#   completed: 145,
#   failed: 3,
#   delayed: 0,
#   waiting: 8
# }

# Inspect specific job
node -e "
const { claimsQueue } = require('./lib/jobs');
claimsQueue.getJob('job-id-here').then(job => {
  console.log('State:', job.state);
  console.log('Progress:', job.progress());
  console.log('Data:', job.data);
});
"
```

---

## Deployment

### Deploy to Vercel

```bash
# Push to GitHub
git push origin main

# Vercel auto-deploys, but first time:
vercel --prod

# Set environment variables in Vercel Dashboard
# - NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY
# - CLERK_SECRET_KEY
# - DATABASE_URL (external PostgreSQL)
# - REDIS_URL (Upstash)
# - ANTHROPIC_API_KEY
# - BLOB_READ_WRITE_TOKEN
```

### Production Checklist

- [ ] Clerk production keys
- [ ] PostgreSQL connection secure
- [ ] Redis connection secure
- [ ] Anthropic API key secure
- [ ] Vercel Blob token configured
- [ ] Backups scheduled (database)
- [ ] Monitoring enabled (Sentry, PostHog)
- [ ] Email notifications working
- [ ] Rate limiting configured
- [ ] CORS headers correct
- [ ] SSL/HTTPS enforced
- [ ] Database migrations applied
- [ ] Seed data loaded
- [ ] Test batch of claims processed
- [ ] Performance benchmarks verified

### Scaling for High Volume

1. **Database**: Use read replicas for dashboard queries
2. **Cache**: Increase Redis memory, configure eviction policy
3. **Jobs**: Increase BullMQ concurrency (per CPU count)
4. **API**: Vercel scales automatically
5. **Storage**: Vercel Blob scales automatically

---

## Monitoring & Alerts

### Key Metrics to Monitor

- **Claims processed per minute** (target: >5)
- **Average processing time** (target: <5 seconds)
- **Manual review rate** (target: <15%)
- **Vision API error rate** (target: <0.1%)
- **Cache hit rate** (target: >80%)
- **Database connection pool health**
- **Redis memory usage**

### Logging

All major operations logged to structured JSON format:

```
{"level":"INFO","msg":"Claim processing completed","claimId":"claim_123","duration":4200,"status":"supported","tokensUsed":850}
```

View logs:
- **Local**: Check terminal output
- **Production**: Check Vercel dashboard or Sentry

---

## Contributing

### Guidelines

1. **Read context files** before starting work
2. **Keep scope small** — one feature unit at a time
3. **Write tests** for business logic
4. **Update progress tracker** when feature is complete
5. **Follow code standards** — TypeScript strict, single-purpose functions
6. **Document decisions** in comments
7. **Create focused PRs** — one feature per PR

### Submitting Work

1. Fork the repository
2. Create a feature branch: `git checkout -b feat/feature-name`
3. Write code + tests
4. Update documentation
5. Create a PR with clear description

---

## Troubleshooting

### Common Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| "Vision API not found" | ANTHROPIC_API_KEY missing | Set in `.env.local` |
| "Database connection timeout" | PostgreSQL not running | Start with `pg_ctl start` |
| "Redis connection refused" | Redis not running | Start with `redis-server` |
| "Clerk auth failed" | Wrong Clerk keys | Check Clerk dashboard for correct keys |
| "Images not uploading" | Blob storage not configured | Check Vercel Blob token in `.env.local` |
| "Jobs not processing" | BullMQ worker not running | Run `npm run jobs:worker` in separate terminal |

### Debug Mode

Enable debug logging:

```bash
DEBUG=claimverify:* npm run dev
```

---

## Performance Targets

| Operation | Target | Status |
|-----------|--------|--------|
| Single claim processing | <5 sec | ✅ |
| Batch processing (1K claims) | <10 min | ✅ |
| Dashboard load | <2 sec | ✅ |
| Vision API call | <2 sec | ✅ |
| User history lookup | <100 ms | ✅ |

---

## Cost Analysis

### Monthly Cost (1,000 claims/day)

| Service | Cost | Notes |
|---------|------|-------|
| Vercel | $20 | Functions + Blob storage |
| PostgreSQL | $50 | Small managed instance |
| Redis | $10 | Small managed instance |
| Claude Vision | $300 | ~$0.01/image (cached) |
| **Total** | **$380** | ~$0.38 per claim |

---

## License

MIT © 2024 ClaimVerify Contributors

---

## Support

- 📖 [Documentation](./docs)
- 🐛 [Issues](https://github.com/yourusername/claimverify/issues)
- 💬 [Discussions](https://github.com/yourusername/claimverify/discussions)

---

## Acknowledgments

Built with:
- [Next.js](https://nextjs.org)
- [Prisma](https://www.prisma.io)
- [Clerk](https://clerk.com)
- [Claude AI](https://anthropic.com)
- [Vercel](https://vercel.com)
- [shadcn/ui](https://ui.shadcn.com)

---

**Happy building! 🚀**
