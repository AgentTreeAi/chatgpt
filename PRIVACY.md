# Privacy Notice

Remote-Team Mental Health Tracker (RMHT) is designed to protect employee anonymity while giving leaders actionable trends.

## Data We Process

- **Check-ins:** mood (1-5), stress (1-5), optional comment. No names or emails stored with entries.
- **Auth:** hashed employee tokens; email addresses only for admins using magic links.
- **Integrations:** Slack workspace IDs and bot tokens, stored encrypted at rest.
- **Billing:** Stripe customer and subscription IDs; no payment card data stored by RMHT.

## Aggregation & Thresholds

Dashboards only render when ≥5 unique respondents contribute within the period. Risk scoring uses smoothed aggregates—no individual entries exposed.

## Retention

Default retention is 180 days per org. Daily jobs purge check-ins older than each org’s policy while keeping derived risk snapshots.

## Data Residency

Preview deployments run on Railway (US) with Neon Postgres. Customers can request EU data residency for GA.

## Data Subject Requests

Org admins can delete tokens/users anytime. For assistance email privacy@rmht.app; responses within 7 days.
