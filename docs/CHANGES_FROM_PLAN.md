# Deviations & Changes From Original Plan

## Round 1 vs Round 2 Architecture Adjustments
1. **Vector DB (pgvector) -> In-Process BM25**:
   - *Original Plan*: External PostgreSQL with pgvector extension for guideline retrieval.
   - *Change*: Implemented in-process BM25 lexical ranking engine.
   - *Rationale*: A ~50-entry brand guideline set is compact, precise, and deterministic. Avoids cloud vector DB costs and simplifies local zero-dependency testing.
2. **Dual Hosting -> Unified Static-Export Fast-API Deployment**:
   - *Original Plan*: Separate Next.js Vercel frontend and FastAPI Render backend.
   - *Change*: Built Next.js as static export (`output: 'export'`) served directly by FastAPI.
   - *Rationale*: Render free tier limits, single domain eliminates cross-origin latency and dual cold-start delays.
