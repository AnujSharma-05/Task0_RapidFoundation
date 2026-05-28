This Repository is to track the learning progress in the "Expected" order below. Each phase builds on the one before it. The codes and workflow is documented to the best of the capabilities and editorials would also be produced in order to share the detailed learnings from time to time.

The commit log is crucial for atomic progress.

## Phase 1

1. Python fundamentals for backend engineering
2. Object-Oriented Programming (OOPs) in Python
3. Functions, decorators, and modular coding
4. Exception handling and debugging
5. JSON handling and file processing

## Planned Project: Evolving Backend + AI System

Phases 2 and 3 are folded into one project so the backend, data, realtime, and AI layers are learned together. The project evolves in versions.

### V1: Skeleton API

Goal: Create an API that accepts a PDF file and returns a processing status.

Covered skills:

1. FastAPI routing and HTTP methods
2. Pydantic models for API contracts
3. Async file I/O for large uploads
4. Dependency Injection for validators and services

### V2: Real-Time Processing Layer

Goal: While the PDF is being processed, the client receives live progress updates.

Covered skills:

1. WebSockets for persistent bidirectional communication
2. Background tasks for heavy parsing work
3. PostgreSQL for task state persistence
4. Request/response lifecycle boundaries

### V3: RAG and AI Layer

Goal: Turn parsed text into vectors and answer user questions from the uploaded PDF.

Covered skills:

1. Embeddings and semantic representation
2. Vector databases such as Chroma or Pinecone
3. RAG pipeline design and prompt orchestration
4. JWT authentication and user-level access control

### Why this project works

1. It forces AsyncIO and background processing because AI and vector search are slow.
2. It forces Pydantic validation because LLM output can be messy.
3. It forces chunking and indexing because a PDF is too large for one prompt.

### Optional additions

If you want to extend the plan later, add:

1. File upload limits and validation rules
2. Retry and failure recovery for document processing
3. Conversation history and query logging
4. Simple evaluation tests for RAG answers

## Phase 2 and 3 Skills Inside the Project

6. AsyncIO and asynchronous programming
7. Event loop and concurrency understanding
8. FastAPI fundamentals and API development
9. Request/response lifecycle understanding
10. Pydantic models and validation
11. Dependency Injection in FastAPI
12. Middleware and backend architecture basics

13. Authentication basics (JWT, hashing, RBAC concepts)
14. WebSockets and real-time communication
15. PostgreSQL and SQL fundamentals
16. Database querying and indexing basics
17. Vector databases and embeddings
18. RAG (Retrieval-Augmented Generation) fundamentals
19. LLM workflow understanding
20. API integration and orchestration

21. AI PDF Chatbot backend project using FastAPI + VectorDB + LLM integration 