# Product Requirements Document: Sahabat AI Aggregator Platform v1.1

**Version:** 1.1
**Status:** Final
**Owner:** AI Platform & Products
**Date:** 24 September 2025

---

### 1. Introduction & Vision

This document outlines the requirements for building the Sahabat AI Aggregator Platform v1.1. The primary goal is to create a multi-modal, multi-model AI platform that serves as a central gateway for various generative AI tasks.

The platform's vision is **"AI for ALL"**, aiming to provide accessible and powerful AI tools to Indonesian consumers and B2B enterprises, with a focus on cost-efficiency, scalability, and a superior user experience. This version focuses on the core aggregator functionality.

---

### 2. Core Features

-   **F1: Multi-Modal Interactions:** Users can submit queries via text and can also upload images, audio, and documents for analysis by the platform.
-   **F2: Multi-Model Generation:** The platform will generate responses in multiple formats, including Text, Images, and Video, by routing requests to the most appropriate AI model.
-   **F3: Conversational Context:** The system must maintain session state, remember conversation history, and use it as context for follow-up queries. History will be stored for up to 90 days for paid users and 15 days for free users.
-   **F4: Tiered User Access:** The platform will support three distinct user tiers with different quota limits as defined in the Business Requirement Document (BRD): Free, Paid, and IOH Bundle.
-   **F5: User Profile & Quota Visibility:** Users must be able to view their current subscription tier and their quota usage for different models and task complexities from a profile screen.

---

### 3. System Architecture & Flow

The platform will be built on a Hybrid Three-Tier Architecture to ensure a clean separation between business logic, AI orchestration, and model inferencing.

#### **Tier 1: Pre-processing API Gateway (The "Front Door")**

-   **Description:** A high-performance, non-AI service that is the single entry point for all user traffic.
-   **Tech Stack:** Python/FastAPI.
-   **Responsibilities:**
    -   Handles user authentication (Guest, Agnostic, IOH users).
    -   Connects to the PostgreSQL database to perform all quota checks against the user's profile.
    -   Rejects requests that are out-of-quota immediately with a `429 Too Many Requests` error.
    -   Creates and passes a `user_context` object (e.g., `{"tier": "Paid"}`) and a `session_id` to the ADK agent system.

#### **Tier 2: Google ADK Agent System (The "Brain")**

-   **Description:** The AI orchestration layer where all intelligent reasoning and task delegation occurs.
-   **Tech Stack:** Google ADK (Python).
-   **Components:**
    -   **OrchestratorAgent:** The single entry point from the Gateway. This LlmAgent makes one LLM call to perform several critical tasks:
        -   Classify the user's intent.
        -   Determine the `target_agent` (e.g., `TextGenerationAgent`).
        -   Assess the request `complexity` ('Low', 'Medium', 'Complex').
        -   **Perform a guardrail check** to ensure the prompt adheres to safety guidelines (Social, Political, Religious).
    -   **SpecialistAgents:** A consolidated set of agents responsible for specific tasks:
        -   `TextGenerationAgent`
        -   `ImageGenerationAgent`
        -   `VideoGenerationAgent`
        -   `MultiModalQueryAgent` (Handles requests with user-uploaded files).
    -   **Session & Memory Management:**
        -   **Vertex AI Session Service:** Manages short-term conversation history (session state) to maintain context during a single conversation.
        -   **Vertex AI Memory Bank:** Manages long-term, persistent user-level memory across multiple sessions to enable a personalized experience.

#### **Tier 3: LiteLLM Proxy (The "Inferencing Layer")**

-   **Description:** A centralized server that manages all communication with the underlying AI models.
-   **Tech Stack:** LiteLLM Proxy (running in Docker).
-   **Responsibilities:**
    -   Securely stores all third-party API keys.
    -   Receives requests from the ADK Specialist Agents.
    -   Reads the metadata (tags) in the request and uses routing rules in its `config.yaml` to select the final model.
    -   Handles fallbacks and retries.
    -   **Caching will be disabled for v1.1.**

---

### 4. Functional Requirements

| ID | Feature | Description |
| :--- | :--- | :--- |
| F-01 | User Quota Enforcement | The API Gateway MUST check a user's quota against the PostgreSQL database before every AI request. If quota is exceeded, the API MUST return a 429 error and the request MUST NOT proceed to the ADK system. |
| F-02 | Intent, Complexity & Safety Analysis | The OrchestratorAgent MUST analyze the user's prompt to determine the correct SpecialistAgent, assess task complexity, and perform a safety guardrail check. This MUST be done in a single LLM call. |
| F-03 | Metadata-Based Routing | Specialist Agents MUST pass business context (complexity, user_tier, etc.) as metadata to the LiteLLM Proxy. The LiteLLM Proxy's configuration MUST contain the routing rules to select the final model. |
| F-04 | Session State Persistence | The **Vertex AI Session Service** MUST correctly save and retrieve conversation history, keyed by a `session_id`, to maintain context. The **Vertex AI Memory Bank** will be used for long-term memory. |
| F-05 | Multi-modal Input Triage | The API Gateway MUST identify requests containing file uploads. These requests will be classified as "Complex" by default at the gateway for quota-checking purposes. The OrchestratorAgent will perform a more detailed analysis. |
| F-06 | Centralized API Key Management | All external API keys MUST be stored and managed within the LiteLLM Proxy. They MUST NOT be present in the ADK agent code. |

---

### 5. Non-Functional Requirements

-   **Performance:** For P95 of users, simple text-generation queries ("Low" complexity) should have a time-to-first-token of < 1.5 seconds.
-   **Scalability:** The system must be architected to handle 10,000 concurrent users. All components must be containerized and deployable via Kubernetes.
-   **Reliability:** The LiteLLM Proxy should be configured with fallbacks for critical models to ensure high availability.
-   **Safety:** The system must enforce Social, Political, and Religious guardrails at the OrchestratorAgent level to prevent the generation of harmful or inappropriate content.

---

### 6. Model Routing Strategy

The `OrchestratorAgent` will classify each user prompt into a complexity tier to optimize the balance between cost, performance, and quality.

-   **Low Complexity:**
    -   **Trigger:** Simple, factual queries, short prompts (<20 words).
    -   **Examples:** "What is the capital of Indonesia?", "Translate 'hello'".
    -   **Model Strategy:** Route to the most cost-effective and fastest models (e.g., Sahabat LLM, Gemini 1.5 Flash).

-   **Medium Complexity:**
    -   **Trigger:** Requests requiring summarization, comparison, or creative text generation from a moderately detailed prompt.
    -   **Examples:** "Summarize this article," "Write a professional email."
    -   **Model Strategy:** Route to high-quality, efficient models (e.g., Gemini 1.5 Flash).

-   **High Complexity:**
    -   **Trigger:** Multi-step reasoning, deep analysis, code generation, or handling large documents.
    -   **Examples:** "Analyze this financial report," "Write a Python script for a web scraper."
    -   **Model Strategy:** Route to the most powerful frontier models (e.g., Gemini 1.5 Pro, GPT-4o).

---

### 7. Response Presentation Layer

To ensure a rich user experience and a clean separation between backend and frontend, all `SpecialistAgents` are responsible for formatting their final output into a standardized JSON object.

-   **Standard:** The primary content of the response (e.g., the text answer) will be formatted using **Markdown**.
-   **Responsibility:** Each `SpecialistAgent` will use a single LLM call to generate the answer and format it in Markdown simultaneously by using detailed system instructions in its prompt.
-   **Benefit:** This allows the backend to send well-structured, formatted content (including headings, lists, bold text, code blocks, etc.) in a simple text format that any frontend can easily render.

---

### 8. Out of Scope (for v1.1)

-   **Research Agent:** A "Perplexity-style" web search and research agent.
-   **Agent Factory:** The capability for third parties to create and deploy their own agents.
-   **eCommerce & Payments:** Direct integration with payment gateways within the chat flow.
-   **Response Caching:** Caching of LLM responses in the LiteLLM proxy is disabled for this version.