---
name: Contract status consistency
description: Rules for keeping customer-facing contract status aligned with license administration while preserving anonymized records.
---

# Contract status consistency

Customer-facing contract pages and administrative license views must obtain the displayed license status and package from the same central effective license evaluation, rather than independently rendering a stored raw status.

**Why:** Raw records can be stale or require date/suspension evaluation. Parallel display paths otherwise allow the same customer to appear active in one place and deleted or expired in another.

**How to apply:** Preserve contract fields and customer number from the leading customer record, but overlay its effective license status and normalized package for display. Pass the technical-mandate context through every administrative read path so legacy packages normalize identically. An anonymized record marked by either the deletion sentinel or raw deletion status is a retention record, not a recoverable customer: never restore its number, access, or license through normal reactivation. The sole legacy exception requires all three independent signals—active club, no club lock, and at least one active linked user—beside a deletion marker; it is repaired only through the license path and receives a fresh atomic customer number. A pending Stripe cancellation is reversed only through the Stripe-aware revocation flow; local license writes must reject status changes and must not clear its cancellation fields.

## Expired customer access

Customers with an expired trial/license or an ended subscription retain only a narrow account corridor: profile, contract/package selection, and legal information. Professional areas remain unavailable.

**Why:** Customers need to view their contract and choose a package without exposing sports data or leaving them at a removed legacy license destination.

**How to apply:** Keep the customer-facing contract view as the sole renewal path. Any expiry gate action must enter the narrow corridor, not reactivate a license or restore domain navigation. Superadmins remain outside this customer gate.