"""
AI Foundation layer — the infrastructure the future AI Safety Copilot is built on, not the
copilot itself. Three building blocks compose together for every future capability (incident
explanation, recommendation explanation, analytics Q&A, report summarization, SOP lookup):

    Context Builder (app.ai.context)  -- assembles structured operational data from the
                                         existing Postgres tables (Incident/Timeline/Risk/
                                         Recommendation/...), no vector search involved.
    Prompt Templates (app.ai.prompts) -- reusable, named system+user prompt shapes.
    AI Provider (app.ai.providers)    -- swappable LLM backend; Gemini is the only
                                         implementation today.

app.ai.service.AIService is the one seam that wires these three together
(`generate(template_id, context, **vars)`); it has no capability-specific methods, so a future
capability is a new call site plus (if needed) a new ContextBuilder method or prompt template
— never new architecture.

Safety documentation (OSHA PSM, H2S guide, hot work, LOTO, ...) is a second knowledge source
this layer is designed to support, via semantic/vector retrieval feeding the same AIContext
shape the Context Builder already produces for structured data — deliberately not implemented
yet (no document ingestion, no embeddings, no vector DB in this phase).
"""
