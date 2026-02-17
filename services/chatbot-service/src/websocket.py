import json
from uuid import UUID, uuid4

import structlog
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from src.services.chatbot_service import ChatbotService

logger = structlog.get_logger()
router = APIRouter()


class ConnectionManager:
    """Manages active WebSocket connections."""

    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info("WebSocket client connected", client_id=client_id)

    def disconnect(self, client_id: str):
        self.active_connections.pop(client_id, None)
        logger.info("WebSocket client disconnected", client_id=client_id)

    async def send_message(self, client_id: str, message: dict):
        websocket = self.active_connections.get(client_id)
        if websocket:
            await websocket.send_json(message)

    async def send_stream_chunk(self, client_id: str, chunk: str, message_id: str):
        await self.send_message(
            client_id,
            {
                "type": "stream_chunk",
                "message_id": message_id,
                "content": chunk,
            },
        )

    async def send_stream_end(self, client_id: str, message_id: str, full_response: str):
        await self.send_message(
            client_id,
            {
                "type": "stream_end",
                "message_id": message_id,
                "content": full_response,
            },
        )


manager = ConnectionManager()


@router.websocket("/ws/chat/{client_id}")
async def websocket_chat(websocket: WebSocket, client_id: str):
    """WebSocket endpoint for real-time streaming chat."""
    await manager.connect(websocket, client_id)
    service = ChatbotService()

    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)

            user_id = UUID(payload.get("user_id", str(uuid4())))
            conversation_id = payload.get("conversation_id")
            if conversation_id:
                conversation_id = UUID(conversation_id)
            message = payload.get("message", "")
            language = payload.get("language", "es")

            if not message.strip():
                await manager.send_message(
                    client_id,
                    {"type": "error", "detail": "Empty message"},
                )
                continue

            message_id = str(uuid4())

            await manager.send_message(
                client_id,
                {"type": "stream_start", "message_id": message_id},
            )

            try:
                full_response = ""
                async for chunk in service.process_message_stream(
                    user_id=user_id,
                    conversation_id=conversation_id,
                    message=message,
                    language=language,
                ):
                    full_response += chunk
                    await manager.send_stream_chunk(client_id, chunk, message_id)

                await manager.send_stream_end(client_id, message_id, full_response)

            except Exception as e:
                logger.error("Error during streaming", error=str(e))
                await manager.send_message(
                    client_id,
                    {
                        "type": "error",
                        "message_id": message_id,
                        "detail": "Failed to generate response",
                    },
                )

    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception as e:
        logger.error("WebSocket error", error=str(e), client_id=client_id)
        manager.disconnect(client_id)
