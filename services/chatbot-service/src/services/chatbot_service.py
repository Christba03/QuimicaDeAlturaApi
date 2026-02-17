from datetime import datetime
from typing import AsyncGenerator
from uuid import UUID, uuid4

import structlog

from src.config import settings
from src.core.llm.anthropic_client import AnthropicClient
from src.core.nlu.entity_extractor import EntityExtractor
from src.core.nlu.intent_classifier import IntentClassifier
from src.core.rag.retriever import DocumentRetriever
from src.schemas.chat import ChatResponse
from src.services.conversation_service import ConversationService

logger = structlog.get_logger()

SYSTEM_PROMPT_ES = """Eres un asistente experto en plantas medicinales mexicanas para la plataforma
Quimica de Altura. Tu objetivo es ayudar a los usuarios a aprender sobre plantas medicinales
tradicionales de Mexico, sus compuestos activos, usos etnobotanicos y preparaciones.

Directrices:
- Responde siempre con informacion cientificamente respaldada cuando sea posible.
- Menciona siempre las precauciones y contraindicaciones relevantes.
- No proporciones diagnosticos medicos. Recomienda siempre consultar a un profesional de la salud.
- Si no estas seguro de algo, dilo claramente.
- Responde en el idioma solicitado por el usuario.
- Usa la informacion de contexto proporcionada por el sistema RAG cuando este disponible.
"""

SYSTEM_PROMPT_EN = """You are an expert assistant on Mexican medicinal plants for the
Quimica de Altura platform. Your goal is to help users learn about traditional Mexican
medicinal plants, their active compounds, ethnobotanical uses, and preparations.

Guidelines:
- Always respond with scientifically backed information when possible.
- Always mention relevant precautions and contraindications.
- Do not provide medical diagnoses. Always recommend consulting a healthcare professional.
- If you are unsure about something, say so clearly.
- Respond in the language requested by the user.
- Use context information provided by the RAG system when available.
"""


class ChatbotService:
    """Main chatbot service orchestrating NLU, RAG, and LLM components."""

    def __init__(self):
        self.llm_client = AnthropicClient()
        self.intent_classifier = IntentClassifier()
        self.entity_extractor = EntityExtractor()
        self.retriever = DocumentRetriever()
        self.conversation_service = ConversationService()

    def _get_system_prompt(self, language: str) -> str:
        return SYSTEM_PROMPT_ES if language == "es" else SYSTEM_PROMPT_EN

    async def process_message(
        self,
        user_id: UUID,
        conversation_id: UUID | None,
        message: str,
        language: str = "es",
    ) -> ChatResponse:
        """Process a user message and generate a chatbot response."""
        # Classify intent
        intent = await self.intent_classifier.classify(message, language)
        logger.info("Intent classified", intent=intent, user_id=str(user_id))

        # Extract entities
        entities = await self.entity_extractor.extract(message, language)
        logger.info("Entities extracted", entities=entities)

        # Get or create conversation
        if conversation_id is None:
            conversation = await self.conversation_service.create_conversation(
                user_id=user_id, title=message[:100], language=language
            )
            conversation_id = conversation.id
        else:
            conversation = await self.conversation_service.get_conversation(conversation_id)

        # Retrieve relevant documents via RAG
        rag_context = await self.retriever.retrieve(
            query=message,
            intent=intent,
            entities=entities,
            top_k=settings.RAG_TOP_K,
        )

        # Build conversation history
        history = await self.conversation_service.get_messages(
            conversation_id=conversation_id,
            limit=settings.MAX_CONVERSATION_HISTORY,
        )

        messages = []
        for msg in history:
            messages.append({"role": msg.role, "content": msg.content})

        # Add RAG context to user message
        augmented_message = message
        if rag_context:
            context_text = "\n\n".join(
                [f"[Fuente: {doc['source']}]\n{doc['content']}" for doc in rag_context]
            )
            augmented_message = (
                f"Contexto relevante:\n{context_text}\n\nPregunta del usuario: {message}"
            )

        messages.append({"role": "user", "content": augmented_message})

        # Generate LLM response
        system_prompt = self._get_system_prompt(language)
        response_text = await self.llm_client.generate(
            system_prompt=system_prompt,
            messages=messages,
        )

        # Save user message
        await self.conversation_service.add_message(
            conversation_id=conversation_id,
            role="user",
            content=message,
            intent=intent,
            entities=entities,
        )

        # Save assistant response
        assistant_msg = await self.conversation_service.add_message(
            conversation_id=conversation_id,
            role="assistant",
            content=response_text,
        )

        # Generate suggested follow-up replies
        suggested_replies = self._generate_suggestions(intent, language)

        sources = [doc["source"] for doc in rag_context] if rag_context else None

        return ChatResponse(
            conversation_id=conversation_id,
            message_id=assistant_msg.id if assistant_msg else uuid4(),
            response=response_text,
            intent=intent,
            entities=entities if entities else None,
            sources=sources,
            suggested_replies=suggested_replies,
            created_at=datetime.utcnow(),
        )

    async def process_message_stream(
        self,
        user_id: UUID,
        conversation_id: UUID | None,
        message: str,
        language: str = "es",
    ) -> AsyncGenerator[str, None]:
        """Process a message and stream the response token by token."""
        intent = await self.intent_classifier.classify(message, language)
        entities = await self.entity_extractor.extract(message, language)

        if conversation_id is None:
            conversation = await self.conversation_service.create_conversation(
                user_id=user_id, title=message[:100], language=language
            )
            conversation_id = conversation.id

        rag_context = await self.retriever.retrieve(
            query=message, intent=intent, entities=entities, top_k=settings.RAG_TOP_K
        )

        history = await self.conversation_service.get_messages(
            conversation_id=conversation_id,
            limit=settings.MAX_CONVERSATION_HISTORY,
        )

        messages = [{"role": msg.role, "content": msg.content} for msg in history]

        augmented_message = message
        if rag_context:
            context_text = "\n\n".join(
                [f"[Fuente: {doc['source']}]\n{doc['content']}" for doc in rag_context]
            )
            augmented_message = (
                f"Contexto relevante:\n{context_text}\n\nPregunta del usuario: {message}"
            )

        messages.append({"role": "user", "content": augmented_message})
        system_prompt = self._get_system_prompt(language)

        # Save user message
        await self.conversation_service.add_message(
            conversation_id=conversation_id,
            role="user",
            content=message,
            intent=intent,
            entities=entities,
        )

        full_response = ""
        async for chunk in self.llm_client.generate_stream(
            system_prompt=system_prompt,
            messages=messages,
        ):
            full_response += chunk
            yield chunk

        # Save complete assistant response
        await self.conversation_service.add_message(
            conversation_id=conversation_id,
            role="assistant",
            content=full_response,
        )

    def _generate_suggestions(self, intent: str, language: str) -> list[str]:
        """Generate contextual follow-up suggestions based on detected intent."""
        suggestions_map = {
            "plant_query": {
                "es": [
                    "Cuales son sus compuestos activos?",
                    "Como se prepara?",
                    "Tiene contraindicaciones?",
                ],
                "en": [
                    "What are its active compounds?",
                    "How is it prepared?",
                    "Does it have contraindications?",
                ],
            },
            "symptom_query": {
                "es": [
                    "Que plantas me recomiendas?",
                    "Es seguro combinar plantas?",
                    "Donde puedo conseguirlas?",
                ],
                "en": [
                    "What plants do you recommend?",
                    "Is it safe to combine plants?",
                    "Where can I find them?",
                ],
            },
            "compound_query": {
                "es": [
                    "En que plantas se encuentra?",
                    "Cuales son sus efectos?",
                    "Hay estudios cientificos?",
                ],
                "en": [
                    "In which plants is it found?",
                    "What are its effects?",
                    "Are there scientific studies?",
                ],
            },
        }
        default = {
            "es": [
                "Cuentame mas",
                "Que plantas medicinales conoces?",
                "Necesito ayuda con un sintoma",
            ],
            "en": [
                "Tell me more",
                "What medicinal plants do you know?",
                "I need help with a symptom",
            ],
        }
        suggestions = suggestions_map.get(intent, default)
        return suggestions.get(language, suggestions.get("es", []))
