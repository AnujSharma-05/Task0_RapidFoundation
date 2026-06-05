# Architecture Specification Report: Hierarchical Cluster-Based RAG System

## 1. Executive Summary
Traditional Retrieval-Augmented Generation (RAG) systems suffer from performance degradation, high latency, and vector noise when scaling across large, diverse document ecosystems. Searching an entire knowledge base exhaustively introduces irrelevant context chunks to the Large Language Model (LLM).

This system architecture resolves these inefficiencies by creating an autonomous, hierarchical data routing layer. By partitioning the vector search space using dynamically updated **Categorical Clusters**, the system reduces the target vector search space by orders of magnitude while preserving cross-document semantic synthesis within specific domain contexts.

---

## 2. System Flow Diagrams

### Data Ingestion & Injection Flow (Async)
```
[ User Upload / Doc ] 
         │
         ▼
[ Automated + Manual Categorization ] ───(Compares doc embedding to category summaries)
         │
         ├──► [Assigns Categories & IDs]
         │             │
         │             ▼
         │    [Generate/Update Categorical Summary via LLM]
         │             │
         │             ▼
         │    [Embed Summary & Save to Milvus: `categorical_chunks`]
         │
         └──► [Chunk & Embed Document Contents]
                       │
                       ▼
              [Save Chunks + Metadata to Milvus: `document_chunks`]
              [Save IDs and Hard Metadata to Postgres]
```

### Query & Retrieval Flow (/chat Endpoint)
```
[ User Query (String) ]
         │
         ▼
[ Generate Query Embedding ]
         │
         ▼
[ Semantic Search 1: Query <──> `categorical_chunks` ]
         │
         ▼
[ LLM Layer 1: Identify Target Category/Categories ]
         │
         ▼
[ Query Postgres for Target IDs mapping to selected Category ]
         │
         ▼
[ Semantic Search 2: Query <──> Filtered Vector Space in `document_chunks` ]
         │
         ▼
[ Top-K Context Chunks Retrieved ]
         │
         ▼
[ LLM Layer 2: Final Response Synthesis ]
         │
         ▼
[ NLP Response to User ]
```

---

## 3. Detailed Component Architecture

### A. Database Layout & Partitioning Strategy
The system decouples vector indexing from traditional metadata management by implementing a hybrid storage model:
1. **Milvus (Vector Database):** Split into two isolated collections or semantic spaces:
   * **categorical_chunks:** Stores high-level embeddings of the dynamically generated categorical summaries. This collection remains small, allowing for near-instantaneous initial clustering triage.
   * **document_chunks:** Contains the raw granular text chunk embeddings of all uploaded documents. Vector searches here are filtered explicitly by category_id or document_id.
2. **Postgres (Relational Metadata Store):**
   * Manages absolute mappings, relational fields (doc_id, category_id, uploader_info, timestamp), and hard attributes.
   * Acts as the relational bridge to map an LLM-selected target category to specific file IDs before the final deep vector lookup.

### B. The Dual-LLM Execution Layers
Rather than utilizing a single context-heavy LLM call, the workload is distributed across two distinct execution loops:
* **LLM Layer 1 (Router/Classifier):** Accepts the user query string alongside the top semantic matches from the categorical_chunks collection. Its sole job is to act as an intelligent router, mapping the query intent to a single or multi-label set of existing target clusters.
* **LLM Layer 2 (Synthesizer):** Executes the actual RAG operation. It processes the query alongside the highly isolated context chunks extracted from the targeted vector clusters, completely blind to the noise of the rest of the database.

---

## 4. Automation vs. User Autonomy Engine
To balance optimization with custom tailoring, the UI/UX and backend operate on a dual-mode interaction model:
* **Preemptive Automation (Default):** When a file (e.g., a *Lord of the Rings* novel) is uploaded, the system automatically runs its embedding against the existing categorical_chunks. It detects a semantic match with a broad category like Novels and auto-tags it. Simultaneously, it uses an internal threshold to determine if a specialized sub-category (e.g., Lord of the Rings) should be provisioned asynchronously.
* **User Control & Override:** The frontend UI exposes this pipeline transparently. Users can explicitly toggle off auto-classification during upload to force-assign a file to a specific domain or create an isolated workspace. During active chat sessions, users can manually clamp down searches to a explicit file or an isolated custom cluster, short-circuiting LLM Layer 1 entirely.

---

## 5. Vulnerability & Failure Mode Analysis (What Can Break?)

| Potential Failure Mode | Root Cause | Architectural Mitigation Strategy |
|---|---|---|
| **Category Proliferation / Taxonomy Drift** | Auto-generation creates too many fine-grained, redundant categories (e.g., Sci-Fi, Science Fiction, SciFi). | **Scheduled Cron Function Calls:** Implement an asynchronous maintenance loop utilizing the LLM to inspect, reconcile, and merge adjacent category summaries based on semantic proximity, updating the vector indexes accordingly. |
| **Early Classification Failure** | LLM Layer 1 misclassifies the query intent, pointing the system to the wrong cluster. True context is never reached. | **Confidence-Score Fallbacks:** If the similarity score in Semantic Search 1 is below a specific threshold, default to a broader multi-cluster broad search, or append a fallback search to a catch-all "General Knowledge" index. |
| **Stale Categorical Summaries** | New documents are appended to a cluster, but the high-level categorical summary isn't updated, leading to outdated cluster descriptions. | **Event-Driven Summary Invalidation:** Treat category summary updates like cache invalidation. Use an async worker queue (e.g., Celery/Redis) triggered on document injection to incrementally re-generate the cluster's text summary whenever a critical volume of data shifts. |
