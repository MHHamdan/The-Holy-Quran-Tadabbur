"""
Hugging Face is the only AI/model platform used by the backend.

Every model call (chat generation, embeddings, reranking, speech-to-text,
zero-shot classification) goes through Hugging Face Inference Providers from
this server. The HF token is read from the server environment only and is
never returned to clients, logged, or embedded in frontend/mobile builds.
"""
