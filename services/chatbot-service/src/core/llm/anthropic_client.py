from typing import AsyncGenerator

import anthropic
import structlog

from src.config import settings

logger = structlog.get_logger()


class AnthropicClient:
    """Wrapper around the Anthropic Claude API with streaming support."""

    def __init__(self):
        self.client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = settings.ANTHROPIC_MODEL
        self.max_tokens = settings.ANTHROPIC_MAX_TOKENS
        self.temperature = settings.ANTHROPIC_TEMPERATURE

    async def generate(
        self,
        system_prompt: str,
        messages: list[dict],
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> str:
        """
        Generate a complete response from Claude.

        Args:
            system_prompt: System-level instructions for the model.
            messages: List of message dicts with 'role' and 'content' keys.
            max_tokens: Override default max tokens.
            temperature: Override default temperature.

        Returns:
            The full text response from Claude.
        """
        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens or self.max_tokens,
                temperature=temperature or self.temperature,
                system=system_prompt,
                messages=messages,
            )
            text = response.content[0].text
            logger.info(
                "LLM response generated",
                model=self.model,
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
            )
            return text

        except anthropic.APIConnectionError as e:
            logger.error("Anthropic API connection error", error=str(e))
            raise
        except anthropic.RateLimitError as e:
            logger.error("Anthropic API rate limit exceeded", error=str(e))
            raise
        except anthropic.APIStatusError as e:
            logger.error(
                "Anthropic API status error",
                status_code=e.status_code,
                error=str(e),
            )
            raise

    async def generate_stream(
        self,
        system_prompt: str,
        messages: list[dict],
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> AsyncGenerator[str, None]:
        """
        Stream a response from Claude token by token.

        Args:
            system_prompt: System-level instructions for the model.
            messages: List of message dicts with 'role' and 'content' keys.
            max_tokens: Override default max tokens.
            temperature: Override default temperature.

        Yields:
            Text chunks as they are generated.
        """
        try:
            async with self.client.messages.stream(
                model=self.model,
                max_tokens=max_tokens or self.max_tokens,
                temperature=temperature or self.temperature,
                system=system_prompt,
                messages=messages,
            ) as stream:
                async for text in stream.text_stream:
                    yield text

            logger.info("LLM streaming response completed", model=self.model)

        except anthropic.APIConnectionError as e:
            logger.error("Anthropic API connection error during stream", error=str(e))
            raise
        except anthropic.RateLimitError as e:
            logger.error("Anthropic API rate limit exceeded during stream", error=str(e))
            raise
        except anthropic.APIStatusError as e:
            logger.error(
                "Anthropic API status error during stream",
                status_code=e.status_code,
                error=str(e),
            )
            raise
