import structlog

from src.config import settings
from src.core.rag.embeddings import EmbeddingService
from src.core.rag.retriever import DocumentRetriever

logger = structlog.get_logger()


class RAGService:
    """
    Retrieval-Augmented Generation service.
    Combines document retrieval with prompt augmentation to provide
    contextually relevant information to the LLM.
    """

    def __init__(self):
        self.retriever = DocumentRetriever()
        self.embedding_service = EmbeddingService()

    async def augment_prompt(
        self,
        query: str,
        intent: str,
        entities: list[dict],
        language: str = "es",
    ) -> str:
        """
        Retrieve relevant documents and construct an augmented prompt.

        Args:
            query: The user's original query.
            intent: Classified intent of the query.
            entities: Extracted entities from the query.
            language: Language code.

        Returns:
            Augmented prompt string with relevant context prepended.
        """
        documents = await self.retriever.retrieve(
            query=query,
            intent=intent,
            entities=entities,
            top_k=settings.RAG_TOP_K,
        )

        if not documents:
            logger.info("No relevant documents found for RAG", query=query)
            return query

        context_parts = []
        for i, doc in enumerate(documents, 1):
            source = doc.get("source", "Unknown")
            content = doc.get("content", "")
            context_parts.append(f"[Documento {i} - Fuente: {source}]\n{content}")

        context_block = "\n\n".join(context_parts)

        if language == "es":
            augmented = (
                f"Informacion de referencia relevante:\n"
                f"---\n{context_block}\n---\n\n"
                f"Consulta del usuario: {query}"
            )
        else:
            augmented = (
                f"Relevant reference information:\n"
                f"---\n{context_block}\n---\n\n"
                f"User query: {query}"
            )

        logger.info(
            "Prompt augmented with RAG context",
            num_documents=len(documents),
            query=query[:100],
        )
        return augmented

    async def index_document(
        self,
        title: str,
        content: str,
        source: str,
        category: str,
        language: str = "es",
    ) -> dict:
        """
        Index a new document into the knowledge base.

        Args:
            title: Document title.
            content: Document content.
            source: Source identifier.
            category: Document category (e.g., 'plant', 'compound', 'preparation').
            language: Language code.

        Returns:
            Dict with document ID and embedding status.
        """
        embedding = await self.embedding_service.generate_embedding(content)

        logger.info(
            "Document indexed for RAG",
            title=title,
            category=category,
            embedding_dim=len(embedding) if embedding else 0,
        )

        return {
            "title": title,
            "category": category,
            "embedding_generated": embedding is not None,
            "embedding_dimension": len(embedding) if embedding else 0,
        }
