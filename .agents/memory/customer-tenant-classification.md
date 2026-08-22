---
name: Customer and tenant classification
description: Rules that distinguish real clubs, individual trainers, technical tenants, and orphaned tenant records in Superadmin views.
---

Use one shared, read-only classification for customer administration and the Superadmin license view:

- A real club needs its own contract, license, or Stripe evidence; active memberships alone never create a customer.
- Current club membership comes from `trainer_mandanten`, not the legacy `benutzer.verein_id` field.
- A technical tenant represents an individual trainer only when it has a demonstrated trainer package; show the technical contract once, with one deterministic owner.
- A tenant without active users or players but with commercial data is a data-review record, not a normal customer.
- In a classified club detail view, commercial fields come exclusively from the classified contract partner; user profiles supply contact/account data only. Normalize historical plan names with the partner context before displaying a plan or price.

**Why:** Legacy direct assignments and technical helper tenants otherwise make a person or club appear more than once, or turn a membership into a fictitious customer.

**How to apply:** Reuse the central classifier when adding or changing Superadmin customer, licensing, invoice, or tenant-overview lists. Keep data-review paths informational unless a separately approved data-cleanup workflow is implemented.

For a club, never fall back to a secondary user profile for commercial data. Unknown package values must remain visibly unassigned rather than defaulting to a trainer plan.

## Destructive customer actions

Customer deletion must derive its identity and confirmation number from the classified contract partner. For a technical individual trainer, that is the technical tenant; the linked user account is secondary account information and must never become the deletion identity.

**Why:** Legacy user assignments and multi-tenant memberships can make an arbitrary account look like the owner. Deleting from that identity risks removing data from a different tenant.

**How to apply:** Resolve the target consistently for the UI, data preview, and final mutation. Revalidate the exact contract number, target account relationship, active player-trainer assignments, and all other tenant memberships immediately before mutation in one transaction. Any ambiguity or foreign/inactive association must fail closed; retention records and the deletion audit remain in the same transaction.