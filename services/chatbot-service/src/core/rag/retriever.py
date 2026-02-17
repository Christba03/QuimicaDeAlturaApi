import structlog
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine

from src.config import settings
from src.core.rag.embeddings import EmbeddingService
from src.models.knowledge_document import KnowledgeDocument

logger = structlog.get_logger()


class DocumentRetriever:
    """
    Retrieves relevant documents from the knowledge base using
    vector similarity search for the RAG pipeline.
    """

    def __init__(self):
        self.engine = create_async_engine(settings.DATABASE_URL, echo=settings.DEBUG)
        self.embedding_service = EmbeddingService()

    async def retrieve(
        self,
        query: str,
        intent: str | None = None,
        entities: list[dict] | None = None,
        top_k: int = 5,
    ) -> list[dict]:
        """
        Retrieve the most relevant documents for a query.

        Uses embedding similarity search, optionally filtered by intent-based
        category and extracted entities.

        Args:
            query: The user's query text.
            intent: Classified intent to filter document categories.
            entities: Extracted entities to refine the search.
            top_k: Maximum number of documents to return.

        Returns:
            List of dicts with 'content', 'source', 'title', and 'score' keys.
        """
        query_embedding = await self.embedding_service.generate_embedding(query)

        if query_embedding is None:
            logger.warning("Could not generate query embedding, falling back to keyword search")
            return await self._keyword_search(query, intent, top_k)

        return await self._vector_search(query_embedding, intent, entities, top_k)

    async def _vector_search(
        self,
        query_embedding: list[float],
        intent: str | None,
        entities: list[dict] | None,
        top_k: int,
    ) -> list[dict]:
        """Perform vector similarity search using cosine distance."""
        async with AsyncSession(self.engine) as session:
            # Build base query with cosine similarity
            # Using raw SQL for array operations
            embedding_str = ",".join(str(v) for v in query_embedding)
            similarity_sql = text(
                f"""
                SELECT
                    id, title, content, source, category,
                    1 - (
                        embedding <=> ARRAY[{embedding_str}]::float[]
                    ) as similarity
                FROM knowledge_documents
                WHERE embedding IS NOT NULL
                {'AND category = :category' if intent else ''}
                ORDER BY similarity DESC
                LIMIT :top_k
                """
            )

            params = {"top_k": top_k}
            if intent:
                category = self._intent_to_category(intent)
                params["category"] = category

            result = await session.execute(similarity_sql, params)
            rows = result.fetchall()

            documents = []
            for row in rows:
                score = float(row.similarity)
                if score >= settings.RAG_SIMILARITY_THRESHOLD:
                    documents.append(
                        {
                            "title": row.title,
                            "content": row.content,
                            "source": row.source,
                            "category": row.category,
                            "score": score,
                        }
                    )

            logger.info(
                "Vector search completed",
                results_count=len(documents),
                top_k=top_k,
            )
            return documents

    async def _keyword_search(
        self,
        query: str,
        intent: str | None,
        top_k: int,
    ) -> list[dict]:
        """Fallback keyword-based search using PostgreSQL full-text search."""
        async with AsyncSession(self.engine) as session:
            search_sql = text(
                """
                SELECT id, title, content, source, category,
                       ts_rank(to_tsvector('spanish', content), plainto_tsquery('spanish', :query)) as rank
                FROM knowledge_documents
                WHERE to_tsvector('spanish', content) @@ plainto_tsquery('spanish', :query)
                ORDER BY rank DESC
                LIMIT :top_k
                """
            )

            result = await session.execute(
                search_sql, {"query": query, "top_k": top_k}
            )
            rows = result.fetchall()

            documents = [
                {
                    "title": row.title,
                    "content": row.content,
                    "source": row.source,
                    "category": row.category,
                    "score": float(row.rank),
                }
                for row in rows
            ]

            logger.info(
                "Keyword search completed",
                results_count=len(documents),
                query=query[:100],
            )
            return documents

    @staticmethod
    def _intent_to_category(intent: str) -> str:
        """Map intents to knowledge document categories."""
        mapping = {
            "plant_query": "plant",
            "symptom_query": "symptom",
            "compound_query": "compound",
            "preparation_query": "preparation",
            "safety_query": "safety",
            "general_info": "general",
        }
        return mapping.get(intent, "general")
