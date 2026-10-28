# System Architecture: Inkguard

**Product:** Inkguard — Intelligent Brand Governance Platform  
**Architecture Pattern:** Clean Architecture / Hexagonal (Ports & Adapters) Modular Monolith  
**Status:** Round 3 Release

---

## 1. High-Level Architecture Diagram

```mermaid
flowchart TB
    subgraph ClientLayer ["Client Layer (Next.js 16 + React 19)"]
        UI["Tailwind CSS 4 + Lucide React UI"]
        AppShell["AppShell & Nav (ModeChip, Notifications, Role Switcher)"]
        Dashboard["Role-Specific Dashboards"]
        ReviewStudio["Review Studio (HighlightedText, FindingCards, DiffView)"]
        KBStudio["Guideline & Health Studio (/kb, /insights/guideline-health)"]
    end

    subgraph APILayer ["API Presentation Layer (FastAPI 0.162)"]
        AuthRouter["/api/v1/auth"]
        SubmissionsRouter["/api/v1/submissions"]
        FindingsRouter["/api/v1/findings"]
        KBRouter["/api/v1/kb"]
        InsightsRouter["/api/v1/insights"]
        EvalRouter["/api/v1/evaluation"]
        NotifRouter["/api/v1/notifications"]
        AuditRouter["/api/v1/audit"]
        SettingsRouter["/api/v1/settings"]
    end

    subgraph ApplicationLayer ["Application Layer (Use Cases & Orchestration)"]
        ReviewOrch["ReviewOrchestrator (5-Stage Pipeline)"]
        WorkflowOrch["Workflow & Approval Engine"]
        KBService["Knowledge Base & Versioning Service"]
        AuditService["Audit Logger & Hash Chaining"]
        NotifService["Notification Dispatcher"]
    end

    subgraph DomainLayer ["Pure Domain Core (Zero External Dependencies)"]
        StateMachine["WorkflowStateMachine (7 States)"]
        Permissions["RBAC Clearance & allowed_actions"]
        RuleEngine["RuleChecksStage (Terms, Claims, Leaks)"]
        A11yEngine["A11yChecksStage (Readability, WCAG)"]
        ColorMath["ColorMath (CIE Lab Delta-E & Contrast)"]
        VerifierStage["LLMVerifierStage (Semantic Entailment)"]
        Guardrails["Guardrails (Citation & Excerpt Validation)"]
        SuggestValidator["SuggestionValidator (<=60% Edit Cap)"]
        AmbiguityEngine["AmbiguityScorer (0-100 Formula)"]
        GapClusterer["GapClusterer (BM25 Lexical Clustering)"]
        StaleDetector["StaleRuleDetector (Lifecycle Engine)"]
    end

    subgraph PortsLayer ["Ports (Protocol Interfaces)"]
        LLMPort["LLMClient (Protocol)"]
        RetrieverPort["RetrieverPort (Protocol)"]
        StorePort["ReviewStorePort (Protocol)"]
        DocExtractorPort["DocumentExtractorPort (Protocol)"]
    end

    subgraph AdaptersLayer ["Adapters (Infrastructure Implementations)"]
        DBAdapter["SQLAlchemy (PostgreSQL / SQLite WAL)"]
        LLMAdapters["OpenAICompatibleLLM / MockLLM / CachedLLM"]
        BM25Adapter["BM25Retriever (In-Process Lexical)"]
        DocExtractors["DocxExtractor / PdfExtractor / ImageExtractor"]
        SecurityAdapter["Bcrypt Hashing & PyJWT Tokens"]
    end

    %% Dependencies
    UI --> APILayer
    APILayer --> ApplicationLayer
    ApplicationLayer --> DomainLayer
    ApplicationLayer --> PortsLayer
    AdaptersLayer --> PortsLayer
    AdaptersLayer --> DomainLayer
```

---

## 2. Module Boundaries & Dependency Invariants

Inkguard strictly implements **Clean Architecture** with inward-pointing dependencies. Contracts are automatically enforced by `import-linter` via `python manage.py arch`:

1. **`domain/` (Pure Python Core)**:
   - **Constraint**: Must NEVER import from `application`, `adapters`, `api`, or external web/ORM libraries (`fastapi`, `sqlalchemy`, `httpx`, `pydantic_settings`).
   - **Responsibility**: Pure business logic, invariants, scoring algorithms, and domain models.
   - **Verification**: `manage.py arch` verifies `Domain layer purity KEPT`.

2. **`application/` (Use Cases)**:
   - **Constraint**: Must NEVER import from `adapters` or `api`.
   - **Responsibility**: Coordinates domain objects, initiates transactions, executes pipeline stages, and interacts exclusively with interfaces defined in `ports/`.
   - **Verification**: `manage.py arch` verifies `Application layer isolation KEPT`.

3. **`ports/` (Abstract Interfaces)**:
   - **Responsibility**: Defines Python typing `Protocol` definitions (`LLMClient`, `RetrieverPort`, `ReviewStorePort`). Decouples application logic from third-party SDKs and databases.

4. **`adapters/` (Infrastructure)**:
   - **Responsibility**: Implements port interfaces with concrete technologies: SQLAlchemy (Postgres/SQLite), Google AI Studio / Ollama, `python-docx`, `pdfplumber`, `Pillow`, and Bcrypt.

5. **`api/` (Transport)**:
   - **Responsibility**: HTTP routing, request parsing, response serialization, cookie/header extraction, and role authorization gates.

---

## 3. Data Flow of One Review

When a creator clicks **"Run Brand Review"** (or calls `POST /api/v1/submissions/{id}/review`), the submission flows through a deterministic 5-stage orchestration pipeline:

```mermaid
sequenceDiagram
    autonumber
    actor Creator as Creator / Client
    participant API as Submissions Router
    participant Orch as ReviewOrchestrator
    participant San as SanitiseStage (Domain)
    participant Rules as Rule & A11y Stage (Domain)
    participant Ret as BM25 Retriever (Adapter)
    participant LLM as LLM Analysis Stage (Adapter)
    participant Ver as VerifierStage (Domain)
    participant Guard as Guardrails & Validator (Domain)
    participant DB as ReviewStore & DB (Adapter)

    Creator->>API: POST /api/v1/submissions/{id}/review?sync=true
    API->>Orch: run_review(review_id, submission_id, user_max_tier)
    
    rect rgb(240, 248, 255)
        Note over Orch,San: Stage 1: Extraction & Sanitisation
        Orch->>San: Extract text/structure & Redact PII (emails, phones, keys)
        San-->>Orch: Clean text + Redaction log (count only)
    end

    rect rgb(255, 250, 240)
        Note over Orch,Rules: Stage 2: Deterministic Rule Checks (Zero External Calls)
        Orch->>Rules: Evaluate banned terms, disclaimers, regex, a11y & color math
        Rules-->>Orch: Deterministic findings (RuleChecks + A11y)
    end

    rect rgb(245, 255, 250)
        Note over Orch,Ret: Stage 3: Retrieval & Egress Filtering
        Orch->>Ret: Lexical BM25 search over KB entries (Filtered by user max_tier)
        Ret-->>Orch: Top relevant rules & facts (Strictly excludes confidential entries)
    end

    rect rgb(255, 240, 245)
        Note over Orch,LLM: Stage 4: LLM Analysis (Mock, Cached, or Live)
        Orch->>LLM: Structured JSON prompt (30s timeout wrapper)
        LLM-->>Orch: Candidate findings (claims, tone, suggestions)
    end

    rect rgb(240, 255, 240)
        Note over Orch,Guard: Stage 5: Reliability Engine & Finalisation
        Orch->>Ver: LLMVerifierStage (Semantic entailment verification)
        Ver-->>Orch: Verdict: Supported, Contradicted, or Unsure
        Orch->>Guard: Validate citations, verify excerpts, apply <=60% edit cap
        Guard-->>Orch: Validated findings list
    end

    Orch->>DB: Persist findings, update status='completed', log Data Boundary telemetry
    DB-->>API: Review record
    API-->>Creator: HTTP 200 ReviewResponse
```

---

## 4. Trust Boundary & Data Privacy Architecture

Inkguard enforces strict data privacy invariants at every architectural layer:

```
+-------------------------------------------------------------------------------+
|                             CLIENT / BROWSER                                  |
+-------------------------------------------------------------------------------+
                                      |
                                      v HTTPS / JWT
+-------------------------------------------------------------------------------+
|                             FASTAPI GATEWAY                                   |
| - Authentication & RBAC Clearance Gate (Tier: Public, Internal, Confidential)  |
| - Input validation (413 on >20,000 chars, 422 on empty content)               |
+-------------------------------------------------------------------------------+
                                      |
                                      v In-Memory Context
+-------------------------------------------------------------------------------+
|                       INGESTION & SANITISATION BOUNDARY                       |
| - SanitiseStage: regex redaction of PII (emails, phones, API keys)           |
| - Redaction log persists type & count only; never raw PII                    |
+-------------------------------------------------------------------------------+
                                      |
                                      v
+-------------------------------------------------------------------------------+
|                       RETRIEVAL & CONFIDENTIAL FILTER                         |
| - In-process BM25 filtered strictly by user max_tier                          |
| - Hard Assert: ZERO confidential entries ever included in external payload    |
+-------------------------------------------------------------------------------+
                                      |
                                      v (Filtered sanitized payload)
+===============================================================================+
|                   EXTERNAL AI BOUNDARY (Google AI Studio / Ollama)            |
| - 30-Second Execution Deadline Wrapper                                        |
| - Admin "No External AI" switch halts all egress                              |
| - Daily Cap (LLM_DAILY_CAP) forces fallback to rules_only                     |
| - Data Boundary Log records exact character egress & clearance tier           |
+===============================================================================+
```

---

## 5. What the Three Major Improvements Added

In Round 3, three major architectural capabilities were added to the platform:

### 1. Reliability Engine
- **LLM Verifier Pass** ([verifier.py](file:///home/redpanda/Documents/WeBug/backend/app/domain/review/verifier.py)):
  - Evaluates candidate findings against cited guidelines using a dedicated semantic entailment prompt (`verify.v1.md`).
  - Automatically drops ungrounded findings and downgrades low-confidence items to `needs_human_judgment=True`.
- **Benchmark Evaluation Harness** ([eval/](file:///home/redpanda/Documents/WeBug/backend/app/eval/)):
  - 84 ground-truth annotated documents across 5 channels (`Social`, `Email`, `Blog`, `Web`, `Press Release`).
  - Automated offline regression metrics CLI (`python manage.py eval`) measuring Precision, Recall, and F1 across mock, cached, and live runs.

### 2. Guideline Health Intelligence
- **Ambiguity Scoring Engine** ([ambiguity.py](file:///home/redpanda/Documents/WeBug/backend/app/domain/insights/ambiguity.py)):
  - Pure Python formula (0–100) scoring rules based on creator dismissal rates, reviewer overrides, team disagreement discordance, and clarification comment volume (requires $\ge 5$ events).
- **Uncited Comment Clustering & Gap Detection** ([gaps.py](file:///home/redpanda/Documents/WeBug/backend/app/domain/insights/gaps.py)):
  - In-process BM25 lexical similarity clustering grouping reviewer change-request comments that do not cite existing rules, generating candidate rule proposals with one-click manager approval into the Knowledge Base.
- **Rule Lifecycle Auditing** ([stale.py](file:///home/redpanda/Documents/WeBug/backend/app/domain/insights/stale.py)):
  - Automated detection of unused rules (8+ weeks), overdue review dates, expired facts, and rules referencing expired facts.

### 3. Multi-Format Review & Visual Brand Compliance
- **Hierarchical Document Ingestion** ([docx_extractor.py](file:///home/redpanda/Documents/WeBug/backend/app/adapters/documents/docx_extractor.py), [pdf_extractor.py](file:///home/redpanda/Documents/WeBug/backend/app/adapters/documents/pdf_extractor.py)):
  - Safe parsing of `.docx` and `.pdf` files, extracting headings, tables, callouts, and tracking location metadata (`"Paragraph 3"`, `"Page 1"`).
- **Computer-Vision Brand Asset Compliance** ([image_extractor.py](file:///home/redpanda/Documents/WeBug/backend/app/adapters/documents/image_extractor.py), [color_math.py](file:///home/redpanda/Documents/WeBug/backend/app/domain/review/color_math.py)):
  - Pure Python CIE Lab Delta-E color distance calculation against brand palette (`PALETTE-001`).
  - Average 64-bit perceptual image hashing for brand logo verification (`ASSET-LOGO-01`).
  - WCAG AA 4.5:1 text/image contrast calculation and graceful degradation when OCR is unavailable.
