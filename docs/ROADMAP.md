# Product Roadmap: Inkguard Brand Governance

This roadmap outlines the prioritized, sequenced product vision for Inkguard. It builds on the original Round 1 plan, updated with empirical findings from user testing, benchmark evaluation results, and architectural lessons learned during Round 2 and Round 3.

---

## 1. Roadmap Horizon Overview

| Horizon | Timeline | Strategic Focus | Primary Objective |
| :--- | :--- | :--- | :--- |
| **Now** | **Next 4 Weeks** | Usability polish, user-testing feedback, and cloud deployment hardening | Eliminate workflow friction for creators and reviewers; stabilize cloud telemetry. |
| **Next** | **3 Months** | Enterprise integrations, deep format ingestion, and guideline lifecycle automation | Connect into creator authoring tools (Figma, CMS); automate guideline gap merges. |
| **Later** | **6+ Months** | Multimodal video/audio governance, cross-brand multi-tenancy, and compliance reporting | Full-spectrum pre-publication risk intelligence for global enterprise marketing. |

---

## 2. Sequenced Milestones

### Horizon 1: NOW (Next 4 Weeks)

1. **G-17: Deep Link Preservation on Session Expiry (`?return_to=`)**
   - **Reason**: User testing revealed that when a reviewer opens a direct link to `/submission?id=...` while signed out, they are redirected to `/` and must manually find the item in their queue.
   - **Dependency**: `<AuthGuard>` in `frontend/src/shared/ui/AuthGuard.tsx`.
   - **Effort**: Low (1–2 days).

2. **G-19: Dedicated "1 of 2 Approved" Partial Approval Badge in Queue**
   - **Reason**: In the reviewer queue, high-risk items waiting for a second reviewer show status `In Review`, requiring the reviewer to open the item to see if they can provide the second sign-off.
   - **Dependency**: `get_reviewer_queue` endpoint returning approval counts; Queue table UI.
   - **Effort**: Low (2–3 days).

3. **G-11: Unstructured Guideline Document Ingestion (F-14)**
   - **Reason**: Currently, brand managers must enter rules or upload structured JSON. Ingesting raw `.txt` / `.md` brand books with heuristic sectioning will reduce onboarding time from days to minutes.
   - **Dependency**: `DocumentExtractorPort`, pure Python markdown/text sectioner.
   - **Effort**: Medium (1 week).

4. **WASM-Based Client-Side OCR Fallback**
   - **Reason**: On headless cloud hosts without native Tesseract binaries, image text extraction currently relies on server host tools. Compiling Tesseract to WebAssembly (`tesseract.js`) or using an embedded ONNX runtime will enable client-side OCR without server binary dependencies.
   - **Dependency**: Frontend file upload pipeline; declared limitation in `docs/ROUND3_CHANGES.md`.
   - **Effort**: Medium (1–2 weeks).

---

### Horizon 2: NEXT (3 Months)

1. **Figma & Google Docs Integration Plugins**
   - **Reason**: Creators write copy in Google Docs and design graphics in Figma. Bringing Inkguard directly into their authoring canvas catches violations *before* copy is exported for approval.
   - **Dependency**: Headless REST API (`/api/v1/submissions` and `/review`); OAuth 2.0 app registration.
   - **Effort**: High (4–6 weeks).

2. **Automated Guideline Gap Pull-Request Generation**
   - **Reason**: Brand managers who approve candidate rule proposals from uncited comments currently add rules directly to the database. Integrating with Git allows proposed rule changes to be reviewed as Git PRs in Markdown brand repos.
   - **Dependency**: Gap Detection Engine (`gaps.py`); GitHub API Webhooks.
   - **Effort**: Medium (3 weeks).

3. **Multi-Model Ensembling & Self-Hosted Fallback (Ollama / vLLM)**
   - **Reason**: To eliminate external LLM rate limits and ensure 100% data sovereignty for confidential tiers, offer one-click local inference using quantized Llama 3 / Mistral via vLLM or Ollama.
   - **Dependency**: `LLMClient` protocol; local GPU or CPU inference infrastructure.
   - **Effort**: High (4 weeks).

4. **Multi-Brand Workspace Isolation**
   - **Reason**: Marketing agencies manage multiple distinct client brands with conflicting tone rules and asset guidelines.
   - **Dependency**: Database tenant partitioning (`tenant_id`), multi-tenant RBAC policies.
   - **Effort**: High (5 weeks).

---

### Horizon 3: LATER (6+ Months)

1. **Video & Audio Asset Brand Governance**
   - **Reason**: Short-form video (TikTok, Reels, YouTube) is the dominant marketing channel. Transcribing audio, extracting on-screen text, and checking logo presence across video frames will expand coverage.
   - **Dependency**: Whisper transcription, frame-by-frame perceptual hashing, video file processing pipelines.
   - **Effort**: Very High (8–12 weeks).

2. **Automated Legal & Regulatory Jurisdiction Mapping**
   - **Reason**: Regulated marketing (cosmetics, healthcare, financial services) requires different disclaimers by geography (FDA in US, EMA in EU, TGA in Australia).
   - **Dependency**: Geo-targeted rule schemas, structured claim verification databases.
   - **Effort**: High (6–8 weeks).

3. **Predictive Approval Risk Scoring**
   - **Reason**: Historical data from synthetic reviews and real approvals can predict whether a piece of copy is likely to pass first-round review, enabling fast-tracking of low-risk content.
   - **Dependency**: Sufficient historical review dataset; regression ML pipeline.
   - **Effort**: High (6 weeks).

---

## 3. Alignment with Declared Limitations

| Declared Limitation | Current State | Roadmap Resolution | Horizon |
| :--- | :--- | :--- | :---: |
| **Server OCR Binaries** | Graceful degradation; visual checks without text OCR | WASM-based in-browser OCR (`tesseract.js`) | **Now** |
| **Free-Tier LLM Quotas** | Daily cap (100) + offline evaluation disk cache | Local self-hosted LLM (Ollama/vLLM) | **Next** |
| **Unstructured Guidelines** | Structured JSON import only | Heuristic Markdown/Text sectioner (F-14) | **Now** |
| **Single-Tenant Scope** | Single brand ("Lumo") workspace | Multi-tenant brand workspace partitioning | **Next** |
