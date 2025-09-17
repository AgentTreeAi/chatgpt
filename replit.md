# Remote-Team Mental Health Tracker (RMHT)

## Overview

RMHT is a privacy-first micro-SaaS application that helps distributed teams monitor wellbeing through anonymous check-ins. The system collects mood and stress scores via secure tokens, aggregates them into team dashboards with risk insights, and integrates with Slack for notifications. Key features include org-scoped RBAC, anonymization thresholds (≥5 respondents), EWMA-based risk scoring, and Stripe-powered billing.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Core Framework
- **Backend**: FastAPI with Python 3.11, using Jinja2 templates for server-side rendering
- **Database**: PostgreSQL with SQLAlchemy 2.x ORM and Alembic migrations
- **Deployment**: Railway platform with Neon Postgres hosting

### Authentication & Security
- **Passwordless Auth**: Magic link authentication via SendGrid with signed JWT tokens
- **RBAC System**: Role-based access control with org-scoped isolation (`org_admin`, `team_lead`, `employee`)
- **CSRF Protection**: Token-based CSRF validation for state-changing operations
- **Privacy Controls**: Anonymization threshold of ≥5 respondents before displaying aggregated data
- **Data Retention**: Configurable retention periods (default 180 days) with automated purging

### Data Models
- **Multi-tenant Structure**: Organizations contain teams, teams contain users
- **Anonymous Check-ins**: Mood/stress scores (1-5 scale) linked to hashed tokens, not user identities
- **Risk Scoring**: EWMA-based risk snapshots with low/moderate/high classifications
- **Audit Logging**: Comprehensive audit trails for compliance and debugging

### Integration Layer
- **Slack Integration**: OAuth-based bot installation for weekly check-in reminders
- **Stripe Billing**: Subscription management with tiered plans (starter/pro/enterprise)
- **Email Delivery**: SendGrid integration for magic links and notifications
- **Cron Jobs**: Railway-scheduled background tasks for retention, reminders, and risk calculation

### API Design
- **RESTful Routes**: Organized by domain (admin, auth, billing, integrations, jobs, public)
- **Template Rendering**: Server-side HTML generation with TailwindCSS styling
- **Error Handling**: Consistent HTTP status codes with detailed error responses
- **Request Tracking**: UUID-based request correlation for distributed logging

### Privacy Architecture
- **Token-based Anonymity**: User check-ins linked only to hashed tokens, not PII
- **Aggregation Thresholds**: No individual data exposed until minimum cohort size reached
- **Data Minimization**: Only essential data collected and stored
- **Export Controls**: Admin tooling for data export while maintaining anonymity

## External Dependencies

### Core Infrastructure
- **Neon**: Managed PostgreSQL database hosting
- **Railway**: Application hosting and deployment platform
- **SendGrid**: Transactional email delivery service

### Third-Party Integrations
- **Slack API**: Workspace integration for check-in reminders and notifications
- **Stripe**: Payment processing and subscription billing management

### Development Tools
- **Alembic**: Database schema migrations
- **SQLAlchemy**: Python ORM for database operations
- **Pydantic**: Data validation and settings management
- **FastAPI**: Web framework with automatic API documentation

### Optional Services
- **HRIS Integration**: Placeholder for employee roster synchronization
- **Calendar Integration**: Placeholder for meeting utilization analytics

## Replit deployment notes

- Set `APP_ENV=dev`, `SECRET_KEY`, and `RMHT_ADMIN_TOKEN` in the Secrets panel.
- Leave `DATABASE_URL` unset for development; the app will automatically create `rmht.db` using SQLite.
- Provide `DATABASE_URL` and production-grade secrets when switching `APP_ENV` to `prod`.
- Run `uvicorn app.main:app --host 0.0.0.0 --port 8000` to start the service.

