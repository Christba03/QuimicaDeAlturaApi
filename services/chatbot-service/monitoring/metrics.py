from prometheus_client import Counter, Gauge, Histogram, Info

# Service info
CHATBOT_SERVICE_INFO = Info(
    "chatbot_service",
    "Chatbot service information",
)
CHATBOT_SERVICE_INFO.info(
    {
        "version": "1.0.0",
        "service": "chatbot-service",
        "description": "AI Chatbot for Mexican medicinal plants",
    }
)

# Chat metrics
CHAT_MESSAGES_TOTAL = Counter(
    "chatbot_messages_total",
    "Total number of chat messages processed",
    ["role", "language"],
)

CHAT_RESPONSE_TIME = Histogram(
    "chatbot_response_time_seconds",
    "Time to generate a chatbot response",
    ["intent"],
    buckets=[0.5, 1.0, 2.0, 3.0, 5.0, 10.0, 15.0, 30.0],
)

LLM_TOKEN_USAGE = Counter(
    "chatbot_llm_tokens_total",
    "Total LLM tokens consumed",
    ["type"],  # input, output
)

LLM_REQUEST_DURATION = Histogram(
    "chatbot_llm_request_duration_seconds",
    "Duration of LLM API requests",
    ["model", "streaming"],
    buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 30.0, 60.0],
)

LLM_ERRORS_TOTAL = Counter(
    "chatbot_llm_errors_total",
    "Total LLM API errors",
    ["error_type"],
)

# Conversation metrics
ACTIVE_CONVERSATIONS = Gauge(
    "chatbot_active_conversations",
    "Number of currently active conversations",
)

CONVERSATIONS_CREATED_TOTAL = Counter(
    "chatbot_conversations_created_total",
    "Total number of conversations created",
    ["language"],
)

# Intent classification metrics
INTENT_CLASSIFICATIONS_TOTAL = Counter(
    "chatbot_intent_classifications_total",
    "Total intent classifications",
    ["intent"],
)

ENTITY_EXTRACTIONS_TOTAL = Counter(
    "chatbot_entity_extractions_total",
    "Total entities extracted",
    ["entity_type"],
)

# RAG metrics
RAG_RETRIEVALS_TOTAL = Counter(
    "chatbot_rag_retrievals_total",
    "Total RAG retrieval operations",
    ["search_type"],  # vector, keyword
)

RAG_DOCUMENTS_RETRIEVED = Histogram(
    "chatbot_rag_documents_retrieved",
    "Number of documents retrieved per query",
    buckets=[0, 1, 2, 3, 5, 10],
)

RAG_RETRIEVAL_DURATION = Histogram(
    "chatbot_rag_retrieval_duration_seconds",
    "Duration of RAG retrieval operations",
    buckets=[0.05, 0.1, 0.25, 0.5, 1.0, 2.0],
)

# Feedback metrics
FEEDBACK_TOTAL = Counter(
    "chatbot_feedback_total",
    "Total feedback submissions",
    ["rating"],  # positive, negative, neutral
)

# WebSocket metrics
WEBSOCKET_CONNECTIONS = Gauge(
    "chatbot_websocket_connections",
    "Number of active WebSocket connections",
)

WEBSOCKET_MESSAGES_TOTAL = Counter(
    "chatbot_websocket_messages_total",
    "Total WebSocket messages",
    ["direction"],  # inbound, outbound
)
