# Security Policy

## Supported Versions

The RMHT service is in private preview. Security patches land on `main`; deploys promote immediately via Railway.

## Reporting a Vulnerability

Email security@rmht.app with:

- Issue summary
- Steps to reproduce
- Impact assessment
- Proof-of-concept logs or screenshots

We respond within 2 business days and issue mitigations within 5 business days for critical findings.

## Hardening Checklist

- Passwordless login via signed magic links and enforced session CSRF tokens.
- Org-scoped RBAC ensures isolation between customers.
- Minimum aggregation cohort of 5 to prevent re-identification.
- Data retention defaults to 180 days with configurable policy per org.
- Stripe-verified billing entitlements gate premium routes.

Penetration testing and SOC 2 program are in planning for GA.
