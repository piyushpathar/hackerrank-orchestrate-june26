# UI Context: ClaimVerify Dashboard

## Theme & Design Language

**Dark first. Insurance-grade credibility.** The visual language is a dark professional dashboard — deep charcoal backgrounds, clear information hierarchy, and strategic accent colors for claims status and risk levels.

All colors use CSS custom properties in `globals.css` and map to Tailwind tokens. Components **must** reference tokens, never hardcoded hex values.

| Role                 | CSS Variable              | Hex / Value                     |
|---------------------|--------------------------|--------------------------------|
| Page background      | `--bg-base`               | `#0f172a` (deep navy)           |
| Card surface         | `--bg-surface`            | `#1e293b` (slate)               |
| Elevated surface     | `--bg-elevated`           | `#334155` (lighter slate)       |
| Subtle surface       | `--bg-subtle`             | `#475569` (subtle)              |
| Default border       | `--border-default`        | `#64748b`                       |
| Subtle border        | `--border-subtle`         | `#94a3b8`                       |
| Primary text         | `--text-primary`          | `#f1f5f9` (almost white)        |
| Secondary text       | `--text-secondary`        | `#cbd5e1` (muted)               |
| Muted text           | `--text-muted`            | `#94a3b8` (faint)               |
| Faint text           | `--text-faint`            | `#64748b` (very faint)          |
| **Status: Supported**| `--state-success`         | `#10b981` (emerald)             |
| **Status: Rejected** | `--state-error`           | `#ef4444` (red)                 |
| **Status: Review**   | `--state-warning`         | `#f59e0b` (amber)               |
| **Status: Pending**  | `--state-info`            | `#06b6d4` (cyan)                |
| Risk badge (high)    | `--risk-high`             | `#dc2626` (dark red)            |
| Risk badge (med)     | `--risk-medium`           | `#ea580c` (orange)              |
| Risk badge (low)     | `--risk-low`              | `#eab308` (yellow)              |
| Accent (interactive) | `--accent-primary`        | `#3b82f6` (blue)                |
| AI accent            | `--accent-ai`             | `#8b5cf6` (purple)              |

## Typography

| Role          | Font       | CSS Variable        | Usage                    |
|--------------|------------|-------------------|--------------------------|
| UI text      | Inter      | `--font-inter`    | Body, labels, UI controls |
| Code/Mono    | Fira Code  | `--font-mono`     | Image IDs, transcripts, JSON |
| Heading (XL) | Inter 700  | `--font-inter`    | Page titles, dashboard header |
| Heading (MD) | Inter 600  | `--font-inter`    | Card titles, section headers |

Fonts loaded via `next/font/google` as CSS variables on `<html>`. Default body uses Inter with `antialiased`.

## Border Radius

Consistent scale increases with surface depth.

| Context          | Class         | Use Case                    |
|-----------------|---------------|---------------------------|
| Inline / badges | `rounded-lg`  | Tags, status badges, icons |
| Buttons / inputs| `rounded-lg`  | Form controls, buttons      |
| Cards / panels  | `rounded-xl`  | Claim cards, tables         |
| Modals / sheets | `rounded-2xl` | Dialogs, detail views       |

## Components & Patterns

### Dashboard Layout
```
┌─ Header (auth, search, filters) ──────────────────┐
├─ Claims Table / Grid ─────────────────────────────┤
│  ┌─ Claim Card (claimId, status, risk) ────────┐  │
│  │  • Status badge (Supported, Rejected, Review)│  │
│  │  • Risk level indicator (red, orange, yellow)│  │
│  │  • User + claim summary                      │  │
│  │  • Action: View Details                      │  │
│  └────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────┘
```

### Claim Detail View
```
┌─ Header ────────────────────────────────────┐
│ Claim #XXX | Status Badge | Risk Badge     │
├─ Two-Column Layout ────────────────────────┤
│ Left:                   │ Right:             │
│  • Claim Info           │  • Analysis        │
│  • User History         │  • Evidence Check  │
│  • Decision             │  • Risk Flags      │
│                         │                    │
├─ Image Gallery ────────────────────────────┤
│ Thumbnail grid of submitted images         │
│ Click to expand with vision annotations    │
├─ Chat Transcript ──────────────────────────┤
│ User claim in readable format              │
└────────────────────────────────────────────┘
```

### Status Badges

**Claim Status:**
- `Supported` — emerald with checkmark (state-success)
- `Contradicted` — red with X (state-error)
- `Not Enough Info` — cyan with warning (state-info)
- `Pending` — gray with spinner (state-muted)

**Risk Level:**
- `High Risk` — dark red background, white text (risk-high)
- `Medium Risk` — orange background, white text (risk-medium)
- `Low Risk` — yellow background, dark text (risk-low)
- `No Risk` — gray background (text-muted)

### Risk Flag Chips

Inline chips for each risk flag with small icons:
```
[blurry_image] [user_history_risk] [claim_mismatch] [manual_review_required]
```

Color-coded by severity. Hoverable for explanations.

### Evidence Checklist

Inline checklist showing evidence requirements vs. what was submitted:
```
✓ Multiple angles of damage  (2 images)
✗ Clear lighting            (1 image too dark)
✓ Object identification     (clear car front)
? Damage comparison         (before/after requested)
```

### Image Viewer

Lightbox gallery for claim images with:
- Thumbnail strip at bottom
- Full image view with zoom
- Vision analysis overlay (optional) showing detected regions
- Image metadata (filename, dimensions, quality flags)

### Search & Filters

Header search with:
- Search by claim ID, user email, user name
- Filter by status (Supported, Contradicted, Review, Pending)
- Filter by risk level (High, Medium, Low, None)
- Filter by date range
- Filter by object type (Car, Laptop, Package)
- Sort by status, risk, date, or user

Results update with URL params for bookmarking.

## Component Library

**shadcn/ui** on Tailwind. Standard components in `components/ui/`:
- Alert, Badge, Button, Card, Checkbox, Dialog
- Dropdown Menu, Input, Label, Pagination, Select
- Sheet (slide-over), Switch, Table, Tabs, Tooltip

**Custom components** in `components/`:
- `ClaimCard` — single claim summary with actions
- `ClaimDetailView` — full claim analysis and history
- `ImageGallery` — lightbox for claim images
- `RiskBadge` — risk level indicator with color
- `StatusBadge` — claim status with icon
- `EvidenceChecklist` — requirement validation display
- `UserRiskProfile` — user history and risk flags
- `DashboardHeader` — search, filters, auth
- `ClaimsTable` — paginated searchable results

## Responsive Design

- **Mobile (< 768px)**: Single column, card-based layout, vertical stack
- **Tablet (768px - 1024px)**: Two-column where possible, inline badges
- **Desktop (> 1024px)**: Full dashboard layout, side panel, expanded tables

Tables convert to cards on mobile. Images lazy-loaded. Modals full-screen on mobile.

## Accessibility

- **ARIA labels** on all interactive elements
- **Keyboard navigation**: Tab through search, filters, claim cards
- **Color contrast**: All text passes WCAG AA (min 4.5:1 for body)
- **Focus indicators**: Clear focus ring on interactive elements
- **Semantic HTML**: Use `<button>`, `<input>`, `<table>` elements
- **Skip navigation**: Link to main content area

## Dark Mode Implementation

No light mode. CSS variables provide full theming:

```css
:root {
  --bg-base: #0f172a;
  --bg-surface: #1e293b;
  /* ... all other tokens ... */
}

body {
  background-color: var(--bg-base);
  color: var(--text-primary);
}
```

Tailwind configured with CSS custom properties:

```javascript
// tailwind.config.js
theme: {
  colors: {
    base: 'var(--bg-base)',
    surface: 'var(--bg-surface)',
    'text-primary': 'var(--text-primary)',
    // ...
  }
}
```

## Layout Patterns

### Full-Page Dashboard
- Fixed header with search and auth
- Scrollable content area below
- Sidebar optional for filters on desktop
- Mobile: stacked layout with collapsible filters

### Modal / Overlay
- Centered modal with backdrop blur
- `rounded-2xl` border radius
- Dark background with subtle border
- Dismiss button (X) in top right
- Focus trap inside modal

### Sidebar / Slide-Over
- Floating overlay from right edge on desktop
- Full-width bottom sheet on mobile
- Backdrop with semi-transparent overlay
- Smooth slide animation

### Empty State
- Centered content area
- Icon (Lucide React, h-12 w-12)
- Heading and description
- Call-to-action button
- Light gray background (bg-subtle)

## Icons

**Lucide React** only. Stroke-based, no fills. Sizing:
- `h-4 w-4` — inline in text, labels
- `h-5 w-5` — buttons, table icons
- `h-8 w-8` — feature icons, empty states, section headers
- `h-6 w-6` — navigation, sidebar

Status icons:
- Success: `Check` (emerald)
- Error: `X` (red)
- Warning: `AlertCircle` (amber)
- Info: `Info` (cyan)

Risk icons:
- High: `AlertTriangle` (dark red)
- Medium: `AlertCircle` (orange)
- Low: `AlertOctagon` (yellow)

## Performance Considerations

- Images lazy-loaded with `next/image`
- Dashboard pagination (50 claims per page)
- Virtualized tables for 1000+ results
- CSS-in-JS minimal; use Tailwind for styling
- Server Components by default; Client only for interactivity
- Revalidate dashboard cache every 30 seconds
- Cache image metadata in browser for 1 hour

## Data Visualization (Optional Future)

If adding charts:
- Use Recharts for responsive charts
- Dark theme colors aligned with dashboard
- Minimalist design: no grid lines, labeled axes only
- Charts: claims by status (pie), over time (line), by risk (bar)
