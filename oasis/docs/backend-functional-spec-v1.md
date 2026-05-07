# OASIS Architecture & System Design

Backend architecture and workflow design document for OASIS — an AI-assisted career platform focused on trustworthy resume generation and structured career management.

Unlike many AI resume tools that rely heavily on freeform prompting, OASIS is designed around structured user data, explainable workflows, and verifiable experiences.

The goal of the project is not to let AI “invent” better resumes, but to help users organize and present their real experiences more clearly.

---

# 1. Product Overview

OASIS combines resume generation, job matching, application tracking, and long-term career organization into a workflow-oriented system.

Core ideas behind the product:

* Structured background management instead of large freeform text blocks
* Explainable job matching instead of black-box AI scoring
* AI-assisted resume generation grounded in verified user experiences
* Visualized application tracking to reduce stress during job searching
* Long-term career growth support instead of one-time resume generation

The platform is primarily designed for cross-disciplinary job seekers who often struggle to reorganize and present transferable skills across different domains.

---

# 2. Technical Stack

Current MVP stack:

* Backend: FastAPI
* Database: SQLite / PostgreSQL
* ORM: SQLAlchemy 2.x
* Validation: Pydantic
* AI Provider: OpenAI API

Planned future upgrades:

* JWT-based authentication
* Celery + Redis for background jobs
* Embedding-based semantic matching
* Streaming AI responses
* S3-compatible object storage

---

# 3. Core Backend Modules

## 3.1 Authentication (In Progress)

Currently implemented:

* Basic user model scaffold
* Local authentication structure
* Password hashing experiments

Still under development:

* JWT authentication
* Session management
* Role-based permission handling

The current MVP mainly focuses on core workflow and data structure validation before completing full authentication flows.

---

## 3.2 User Profile System

Acts as the structured career database for each user.

Stores:

* Career summary
* Target roles
* Target industries
* Education
* Work experience
* Projects
* Skills
* Certifications
* Languages
* Additional experiences

Instead of storing everything as one resume document, OASIS separates information into reusable structured modules that can later support multiple resume versions.

---

## 3.3 Job Management

Responsible for job posting management and JD analysis.

Stores:

* Company information
* Job title
* Job description
* Required qualifications
* Preferred qualifications
* Extracted keywords

These fields are later used for matching analysis and AI-assisted resume alignment.

---

## 3.4 Resume Generation

Handles AI-assisted resume workflows.

Planned outputs:

* Self introduction
* Motivation letter
* STAR-based rewriting
* One-page resume
* Cross-domain resume conversion
* Experience reframing

The system focuses on restructuring and aligning user experiences instead of generating fabricated achievements.

The full AI generation pipeline is still under active development.

---

## 3.5 Match Scoring

Responsible for compatibility analysis between users and job descriptions.

Current version uses:

* Rule-based scoring
* Weighted category matching
* AI-assisted explanation generation

The scoring system intentionally prioritizes explainability and transparency instead of opaque AI-only ranking.

---

## 3.6 Application Tracking

Tracks user application progress and workflow states.

Application states:

```text
drafted
applied
interview_invited
interviewing
offer
rejected
ghosted
archived
```

State transitions are controlled on the backend side to maintain workflow consistency.

---

## 3.7 Growth Visualization System (Frontend Prototype)

A lightweight visualization system intended to make the job-search process feel more trackable and less emotionally exhausting.

Current frontend prototype maps application progress into growth stages:

| Application Status | Visualization State |
| ------------------ | ------------------- |
| applied            | seed                |
| interview_invited  | sprout              |
| interviewing       | leaf                |
| offer              | bloom               |
| rejected           | withered            |

Current status:

* Frontend prototype partially implemented
* Backend synchronization not completed
* Event persistence logic still under development

The system is currently experimental and mainly exists as a conceptual UX prototype.

---

## 3.8 Reflection & Feedback System (Planned)

Designed to help users reflect on unsuccessful applications and identify improvement opportunities.

Planned functionality:

* Resume feedback
* Interview reflection
* Failure analysis
* Learning suggestions
* AI-assisted review workflows

The intention is to turn rejection experiences into actionable feedback instead of passive failure records.

---

## 3.9 AI Service Layer

Centralized service responsible for AI-related workflows.

Responsibilities:

* Prompt construction
* OpenAI API integration
* JSON schema validation
* Error handling
* Token usage tracking
* Generation logging

All AI outputs are designed to pass schema validation before persistence.

---

# 4. Data Model Design

Main entities:

* users
* user_profiles
* educations
* experiences
* projects
* skills
* certificates
* job_postings
* applications
* resume_versions
* match_scores

The database structure intentionally separates experiences into reusable modules instead of storing one static resume document.

This supports:

* Multiple resume versions
* Cross-domain resume generation
* Structured JD matching
* Explainable recommendation workflows

---

# 5. API Design

Main API groups:

```http
/auth/*
/profile/*
/educations/*
/experiences/*
/projects/*
/skills/*
/jobs/*
/applications/*
/resumes/*
/match/*
```

AI workflows are intentionally separated from core data management to reduce coupling between generation logic and persistent user data.

---

# 6. State Machine Design

## Application Workflow

```text
drafted
→ applied
→ interview_invited
→ interviewing
→ offer / rejected / ghosted
```

All transitions are controlled on the backend side to avoid inconsistent frontend state logic.

---

# 7. Match Scoring Logic (v1)

Current version uses weighted rule-based scoring:

| Category            | Weight |
| ------------------- | -----: |
| Skill Match         |    35% |
| Experience Match    |    25% |
| Education Match     |    15% |
| Certification Match |    10% |
| Domain Match        |    15% |

The first version prioritizes:

* Stability
* Explainability
* Verifiability

Future versions may incorporate embedding-based semantic retrieval.

---

# 8. AI Workflow Design

Resume generation workflow:

```text
Structured Background
        ↓
JD Analysis
        ↓
Match Detection
        ↓
Gap Identification
        ↓
Follow-up Questions
        ↓
AI Resume Generation
```

This workflow was designed to reduce hallucinated resume content and improve alignment between user experiences and generated outputs.

---

# 9. Key Design Decisions

## Prompts Stay on the Backend

Prompts are stored entirely on the backend to reduce prompt injection risks and prevent frontend tampering.

---

## Structured Background IDs

Each experience, project, and course entry includes a unique identifier:

```text
experiences-1
projects-2
courses-3
```

This avoids unreliable string matching during JD analysis and resume rewriting.

---

## JSON Validation for AI Outputs

Earlier versions relied on parsing markdown outputs with regex, which frequently caused formatting failures.

The system later switched to structured JSON outputs with schema validation for improved stability.

---

## Snapshot-Based Traceability

Resume generations are designed to preserve snapshots of:

* User profile data
* Job descriptions
* Match analysis results

This allows later inspection of:

* what information was used
* why certain experiences appeared
* how outputs were generated

---

# 10. Current MVP Scope

Currently implemented:

* Basic profile CRUD
* Experience / Project / Skill CRUD
* Job CRUD
* Rule-based JD analysis
* Match scoring prototype
* Application state prototype
* Frontend growth visualization prototype

Currently in progress:

* JWT authentication
* AI resume generation pipeline
* Structured follow-up question workflow
* Backend synchronization for growth visualization

Planned future modules:

* Reflection system
* Embedding-based matching
* PDF export
* Portfolio generation
* Multi-user collaboration

---

# 11. Development Philosophy

Several principles guided the development of OASIS:

* AI outputs should remain explainable
* User experiences should remain verifiable
* Structured workflows are preferred over raw prompting
* Product transparency matters more than aggressive automation
* Career tools should reduce anxiety instead of amplifying it

OASIS is ultimately less about “automatically writing resumes” and more about helping people better understand and organize their own experiences.
