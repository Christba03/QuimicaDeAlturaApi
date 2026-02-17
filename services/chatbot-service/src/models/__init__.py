from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


from src.models.conversation import Conversation
from src.models.message import Message
from src.models.knowledge_document import KnowledgeDocument

__all__ = ["Base", "Conversation", "Message", "KnowledgeDocument"]
