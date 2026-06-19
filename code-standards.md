# Code Standards: ClaimVerify

## General Principles

- **Clarity over cleverness**: Code should be readable at a glance
- **Type safety**: Strict TypeScript, no `any` type
- **Single responsibility**: Functions and modules do one thing well
- **Fail fast**: Validate inputs at system boundaries
- **Cache aggressively**: Reuse computed results where possible
- **Monitor everything**: Log decisions, costs, and latencies
- **Audit trail**: Record every decision with context and actor

## Project Structure

```
claimverify/
├─ app/
│  ├─ api/                    # API routes (request handlers)
│  │  ├─ claims/             # POST claim, GET claim detail
│  │  ├─ batch/              # POST batch process
│  │  └─ health/             # System health check
│  ├─ dashboard/             # Protected pages
│  │  ├─ page.tsx            # Claims list/dashboard
│  │  ├─ claims/
│  │  │  └─ [id]/page.tsx    # Claim detail view
│  │  └─ admin/
│  │     ├─ users/page.tsx   # User risk profiles
│  │     └─ settings/page.tsx # Configuration
│  ├─ auth/                  # Clerk auth callbacks
│  ├─ layout.tsx             # Root layout (Providers, fonts)
│  └─ page.tsx              # Landing page
├─ components/
│  ├─ ui/                    # shadcn/ui components (do not modify)
│  ├─ dashboard/             # Dashboard-specific components
│  │  ├─ ClaimCard.tsx
│  │  ├─ ClaimsTable.tsx
│  │  ├─ DashboardHeader.tsx
│  │  └─ ClaimDetailView.tsx
│  ├─ claim/                 # Claim submission components
│  │  ├─ ClaimForm.tsx
│  │  ├─ ImageUpload.tsx
│  │  └─ ClaimTranscript.tsx
│  └─ common/                # Reusable components
│     ├─ StatusBadge.tsx
│     ├─ RiskBadge.tsx
│     ├─ ImageGallery.tsx
│     └─ LoadingState.tsx
├─ lib/
│  ├─ claim-processor/       # Core claim processing logic
│  │  ├─ index.ts            # Main orchestrator
│  │  ├─ decision-engine.ts  # Generate final decision
│  │  └─ types.ts            # ProcessingResult, Decision types
│  ├─ vision/                # Claude Vision API integration
│  │  ├─ index.ts            # Image analysis
│  │  ├─ cache.ts            # Vision result caching
│  │  └─ types.ts            # VisionAnalysis, ImageIssue types
│  ├─ risk/                  # User risk assessment
│  │  ├─ index.ts            # Risk evaluation
│  │  ├─ history.ts          # User history loading
│  │  └─ flags.ts            # Risk flag generation
│  ├─ evidence/              # Evidence requirement validation
│  │  ├─ index.ts            # Evidence checking
│  │  └─ cache.ts            # Requirement caching
│  ├─ images/                # Image handling
│  │  ├─ index.ts            # Upload, compression
│  │  ├─ storage.ts          # Vercel Blob / S3 integration
│  │  └─ validation.ts       # Format and size checks
│  ├─ jobs/                  # Background job processing
│  │  ├─ index.ts            # Job queue setup
│  │  ├─ processors.ts       # Job handlers
│  │  └─ monitor.ts          # Job monitoring
│  ├─ db/                    # Database operations
│  │  ├─ client.ts           # Prisma client singleton
│  │  ├─ claim.ts            # Claim queries
│  │  ├─ user.ts             # User queries
│  │  └─ audit.ts            # Audit log helpers
│  ├─ cache/                 # Redis integration
│  │  ├─ index.ts            # Redis client
│  │  ├─ keys.ts             # Cache key generation
│  │  └─ ttls.ts             # TTL constants
│  ├─ auth/                  # Auth helpers
│  │  ├─ index.ts            # Auth checks
│  │  └─ permissions.ts      # Permission checks
│  └─ utils/                 # Shared utilities
│     ├─ logger.ts           # Structured logging
│     ├─ errors.ts           # Error types
│     ├─ csv.ts              # CSV parsing/generation
│     └─ validation.ts       # Input validation
├─ prisma/
│  ├─ schema.prisma          # Database schema
│  └─ seed.ts                # Seed script
├─ jobs/                     # Background jobs (alternative to Trigger.dev)
│  └─ claim-processor.ts     # BullMQ job handler
├─ tests/
│  ├─ unit/                  # Unit tests for functions
│  ├─ integration/           # API route tests
│  └─ fixtures/              # Test data and mocks
├─ public/
│  └─ images/                # Static assets
├─ styles/
│  └─ globals.css            # CSS tokens, dark theme
├─ .env.example              # Environment variables template
├─ package.json
├─ tsconfig.json             # TypeScript strict mode
├─ next.config.js            # Next.js config
├─ tailwind.config.js        # Tailwind with custom tokens
└─ README.md                 # Comprehensive setup guide
```

## TypeScript

**Strict mode required. No exceptions.**

```typescript
{
  "compilerOptions": {
    "strict": true,
    "noImplicitAny": true,
    "strictPropertyInitialization": true,
    "strictBindCallApply": true,
    "strictFunctionTypes": true,
    "strictNullChecks": true
  }
}
```

### Type Guidelines

- **Interfaces** for object contracts: `interface ClaimDecision { ... }`
- **Enums** for fixed values: `enum ClaimStatus { Supported, Contradicted, Insufficient }`
- **Branded types** for IDs: `type UserId = string & { readonly __brand: "UserId" }`
- **Result types** for operations: `type Result<T, E> = { ok: true; value: T } | { ok: false; error: E }`
- **Discriminated unions** for state: 
  ```typescript
  type ClaimState = 
    | { status: "submitted"; createdAt: Date }
    | { status: "processing"; startedAt: Date }
    | { status: "completed"; decision: ClaimDecision; completedAt: Date }
  ```

### Never Use `any`

❌ Bad:
```typescript
function processImage(image: any) {
  return image.analyze();
}
```

✅ Good:
```typescript
interface UploadedImage {
  path: string;
  format: "jpg" | "png" | "webp";
  sizeBytes: number;
}

function processImage(image: UploadedImage): Promise<AnalysisResult> {
  // ...
}
```

## Next.js & React

### Server vs. Client

**Default to Server Components.** Use `"use client"` only when required:
- Browser API (localStorage, fetch, etc.)
- React hooks (useState, useEffect, etc.)
- Event listeners (onClick, onChange, etc.)
- Real-time subscriptions

✅ Server Component:
```typescript
// app/dashboard/page.tsx
import { ClaimsTable } from "@/components/dashboard/ClaimsTable";

export default async function DashboardPage() {
  const claims = await db.claim.findMany({
    where: { userId: auth.userId },
  });
  return <ClaimsTable initialData={claims} />;
}
```

❌ Avoid Client Rendering Everything:
```typescript
// app/dashboard/page.tsx
"use client"; // Unnecessary

import { useEffect, useState } from "react";

export default function DashboardPage() {
  const [claims, setClaims] = useState([]);
  useEffect(() => {
    fetch("/api/claims").then(r => r.json()).then(setClaims);
  }, []);
  return <ClaimsTable data={claims} />;
}
```

### API Route Handlers

Keep handlers **thin**. Push business logic to `lib/`.

```typescript
// app/api/claims/route.ts
import { auth } from "@clerk/nextjs/server";
import { submitClaim } from "@/lib/claim-processor";
import { validateClaimInput } from "@/lib/utils/validation";

export async function POST(request: Request) {
  // 1. Validate auth
  const user = auth();
  if (!user.userId) return Response.json({ error: "Unauthorized" }, { status: 401 });

  // 2. Validate input
  const body = await request.json();
  const validation = validateClaimInput(body);
  if (!validation.ok) {
    return Response.json({ error: validation.error }, { status: 400 });
  }

  // 3. Call business logic
  try {
    const result = await submitClaim(user.userId, validation.value);
    return Response.json(result);
  } catch (error) {
    logger.error("Claim submission failed", { error, userId: user.userId });
    return Response.json({ error: "Processing failed" }, { status: 500 });
  }
}
```

### Caching Strategy

**Use Next.js caching tiers aggressively:**

1. **Client component memo**: Prevent re-renders
   ```typescript
   const ClaimCard = memo(({ claim }: { claim: Claim }) => {
     return <div>{claim.id}</div>;
   });
   ```

2. **Request deduplication**: Same request in single render cycle → single execution
   ```typescript
   // Both return same cached result
   const data1 = await fetch("/api/users", { next: { revalidate: 3600 } });
   const data2 = await fetch("/api/users", { next: { revalidate: 3600 } });
   ```

3. **Segment caching**: Revalidate pages on specific events
   ```typescript
   // app/dashboard/page.tsx
   export const revalidate = 30; // Revalidate every 30 seconds
   
   export default async function DashboardPage() {
     const claims = await db.claim.findMany();
     return <Dashboard claims={claims} />;
   }
   ```

4. **On-demand revalidation**: Invalidate cache from API
   ```typescript
   // app/api/claims/route.ts (POST handler)
   revalidatePath("/dashboard");
   revalidateTag("claims-list");
   ```

5. **Redis caching**: Application-level for high-value lookups
   ```typescript
   // lib/cache/index.ts
   export async function getUserHistory(userId: string) {
     const cached = await redis.get(`user:${userId}:history`);
     if (cached) return JSON.parse(cached);

     const history = await db.userHistory.findUnique({ where: { userId } });
     await redis.setex(`user:${userId}:history`, 3600, JSON.stringify(history));
     return history;
   }
   ```

## Database

### Prisma Usage

Always use connection pooling and indexes.

```prisma
model Claim {
  id        String   @id @default(cuid())
  userId    String
  status    String   @default("submitted")
  createdAt DateTime @default(now())

  // Always index frequently queried fields
  @@index([userId])
  @@index([status])
  @@index([createdAt])
}
```

### Query Patterns

❌ Avoid N+1 queries:
```typescript
const claims = await db.claim.findMany();
for (const claim of claims) {
  const decision = await db.claimDecision.findUnique({
    where: { claimId: claim.id },
  }); // Each claim triggers a query
}
```

✅ Use `include` / `select`:
```typescript
const claims = await db.claim.findMany({
  include: { decision: true },
  take: 50,
  skip: 0,
});
```

### Transactions

Use transactions for multi-step operations:

```typescript
async function processClaim(claimId: string, decision: ClaimDecision) {
  return await db.$transaction(async (tx) => {
    // Both operations succeed or both rollback
    const updated = await tx.claim.update({
      where: { id: claimId },
      data: { status: "completed" },
    });
    await tx.claimDecision.create({
      data: { claimId, ...decision },
    });
    await tx.auditLog.create({
      data: { claimId, action: "decision_made" },
    });
    return updated;
  });
}
```

## Styling

**CSS custom properties + Tailwind only. No raw hex values.**

✅ Good:
```typescript
// components/StatusBadge.tsx
export function StatusBadge({ status }: { status: string }) {
  const bgColor = {
    supported: "bg-state-success",
    rejected: "bg-state-error",
    review: "bg-state-warning",
  }[status];

  return <span className={`${bgColor} text-white rounded-lg px-3 py-1`} />;
}
```

❌ Bad:
```typescript
export function StatusBadge({ status }: { status: string }) {
  const bgColor = {
    supported: "bg-green-500",
    rejected: "bg-red-600",
    review: "bg-yellow-400",
  }[status];

  return <span style={{ backgroundColor: "#10b981" }}>...</span>;
}
```

Border radius scale:
- **Inline elements**: `rounded-lg` (8px)
- **Buttons/inputs**: `rounded-lg` (8px)
- **Cards**: `rounded-xl` (12px)
- **Modals**: `rounded-2xl` (16px)

## Error Handling

Create domain-specific error types:

```typescript
// lib/utils/errors.ts
export class ValidationError extends Error {
  constructor(public field: string, public reason: string) {
    super(`Validation error: ${field} ${reason}`);
  }
}

export class AuthorizationError extends Error {
  constructor(public action: string, public resource: string) {
    super(`Not authorized to ${action} ${resource}`);
  }
}

export class ExternalAPIError extends Error {
  constructor(
    public service: string,
    public statusCode: number,
    public details: unknown
  ) {
    super(`${service} API error: ${statusCode}`);
  }
}
```

Use typed error handling:

```typescript
export type Result<T> = 
  | { ok: true; value: T }
  | { ok: false; error: Error };

export async function analyzeImage(
  imagePath: string
): Promise<Result<ImageAnalysis>> {
  try {
    const analysis = await visionAPI.analyze(imagePath);
    return { ok: true, value: analysis };
  } catch (error) {
    return {
      ok: false,
      error: new ExternalAPIError("Claude Vision", 500, error),
    };
  }
}
```

## Logging & Monitoring

Use structured logging throughout:

```typescript
// lib/utils/logger.ts
export const logger = {
  info: (msg: string, context?: Record<string, unknown>) =>
    console.log(JSON.stringify({ level: "INFO", msg, ...context })),
  error: (msg: string, error?: Error, context?: Record<string, unknown>) =>
    console.error(JSON.stringify({ level: "ERROR", msg, error: error?.message, ...context })),
  warn: (msg: string, context?: Record<string, unknown>) =>
    console.warn(JSON.stringify({ level: "WARN", msg, ...context })),
  debug: (msg: string, context?: Record<string, unknown>) =>
    console.log(JSON.stringify({ level: "DEBUG", msg, ...context })),
};
```

Log key operations:

```typescript
// lib/claim-processor/index.ts
export async function processClaim(claimId: string): Promise<ClaimDecision> {
  const startTime = Date.now();
  
  try {
    logger.info("Claim processing started", { claimId });
    
    const result = await decisionEngine.decide(claimId);
    const duration = Date.now() - startTime;
    
    logger.info("Claim processing completed", {
      claimId,
      status: result.claimStatus,
      duration,
      tokensUsed: result.tokensUsed,
      cost: result.costEstimate,
    });
    
    return result;
  } catch (error) {
    logger.error("Claim processing failed", error as Error, { claimId });
    throw error;
  }
}
```

## Testing

**Unit tests for pure functions. Integration tests for API routes.**

```typescript
// tests/unit/vision.test.ts
import { analyzeImageForDamage } from "@/lib/vision";

describe("Vision Analysis", () => {
  it("should detect dent in car bumper", async () => {
    const result = await analyzeImageForDamage("tests/fixtures/car-dent.jpg");
    expect(result.issueType).toBe("dent");
    expect(result.objectPart).toBe("front_bumper");
  });

  it("should flag blurry images", async () => {
    const result = await analyzeImageForDamage("tests/fixtures/blurry.jpg");
    expect(result.riskFlags).toContain("blurry_image");
  });
});
```

## Deployment

- Use environment variables for all secrets (Clerk, API keys, DB URL)
- Vercel automatically handles `.env.local` → environment variables
- Zero-downtime deployments: migrations run before app starts
- Monitor error rates and performance post-deploy
