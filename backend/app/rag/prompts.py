"""
Prompt templates for the RAG pipeline.
Includes system prompts and context-injection templates.
"""

# ---------------------------------------------------------------------------
# System prompt — defines the AI assistant's behaviour
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """You are an intelligent document assistant powered by RAG (Retrieval-Augmented Generation).

Your role:
- Answer questions accurately based ONLY on the provided context documents.
- If the context does not contain enough information to answer, say so clearly.
- Always cite which source document(s) your answer is based on.
- Be concise, professional, and helpful.
- Format your answers using markdown when appropriate (lists, bold, code blocks).
- Never fabricate or hallucinate information not present in the context.

Rules:
1. Only use information from the provided CONTEXT to answer.
2. If multiple documents are relevant, synthesize information from all of them.
3. When quoting directly, use quotation marks.
4. If the question is unrelated to the documents, politely state that you can only answer questions about the uploaded documents.
"""

# ---------------------------------------------------------------------------
# QA prompt — injected with context and question
# ---------------------------------------------------------------------------
QA_PROMPT_TEMPLATE = """Use the following context to answer the user's question. If you cannot find the answer in the context, say "I don't have enough information in the uploaded documents to answer this question."

CONTEXT:
{context}

CONVERSATION HISTORY:
{chat_history}

USER QUESTION: {question}

ANSWER (cite your sources):"""


# ---------------------------------------------------------------------------
# Condensed question prompt — for multi-turn conversations
# ---------------------------------------------------------------------------
CONDENSE_QUESTION_TEMPLATE = """Given the following conversation history and a follow-up question, rephrase the follow-up question to be a standalone question that captures all necessary context.

CONVERSATION HISTORY:
{chat_history}

FOLLOW-UP QUESTION: {question}

STANDALONE QUESTION:"""
