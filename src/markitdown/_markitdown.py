"""Core MarkItDown conversion engine.

This module provides the main MarkItDown class responsible for converting
various file formats and URLs into Markdown text.
"""

from __future__ import annotations

import os
import re
import mimetypes
from pathlib import Path
from typing import Optional, Union
from dataclasses import dataclass


@dataclass
class DocumentConverterResult:
    """Result of a document conversion operation."""

    title: Optional[str]
    text_content: str

    def __str__(self) -> str:
        return self.text_content


class MarkItDown:
    """Main class for converting documents to Markdown format.

    Supports conversion from local files, URLs, and raw content
    for a variety of common document types.

    Example:
        >>> md = MarkItDown()
        >>> result = md.convert("document.pdf")
        >>> print(result.text_content)
    """

    def __init__(
        self,
        mlm_client=None,
        mlm_model: Optional[str] = None,
    ) -> None:
        """Initialize MarkItDown.

        Args:
            mlm_client: Optional multimodal language model client for
                        image description (e.g., an OpenAI client).
            mlm_model: Model identifier to use with the mlm_client.
        """
        self._mlm_client = mlm_client
        self._mlm_model = mlm_model
        self._converters: list = []
        self._register_default_converters()

    def _register_default_converters(self) -> None:
        """Register built-in converters in priority order."""
        # Converters are tried in registration order; first match wins.
        from markitdown._converters import (
            PlainTextConverter,
            HtmlConverter,
            RssConverter,
        )

        self._converters.extend([
            RssConverter(),
            HtmlConverter(),
            PlainTextConverter(),
        ])

    def convert(
        self,
        source: Union[str, Path],
        **kwargs,
    ) -> DocumentConverterResult:
        """Convert a file or URL to Markdown.

        Args:
            source: A file path (str or Path) or a URL string.
            **kwargs: Additional keyword arguments forwarded to converters.

        Returns:
            A DocumentConverterResult containing the Markdown text.

        Raises:
            FileNotFoundError: If a local file path does not exist.
            ValueError: If no suitable converter is found for the source.
        """
        source_str = str(source)

        # Detect URLs
        if re.match(r"^https?://", source_str, re.IGNORECASE):
            return self._convert_url(source_str, **kwargs)

        # Treat as local file
        path = Path(source_str)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        return self._convert_local(path, **kwargs)

    def _convert_local(
        self,
        path: Path,
        **kwargs,
    ) -> DocumentConverterResult:
        """Convert a local file to Markdown.

        Iterates through registered converters and returns the result
        from the first one that accepts the given file. Falls back to
        PlainTextConverter for unknown types.
        """
        # Resolve MIME type from file extension; default to plain text
        # if mimetypes can't figure it out (e.g. uncommon extensions).
        mime_type, _ = mimetypes.guess_type(str(path))
        if mime_type is None:
            mime_type = "text/plain"

        with open(path, "rb") as f:
            for converter in self._converters:
                result = converter.convert(path, mime_type, f, **kwargs)
                if result is not None:
                    return result

        raise ValueError(f"No converter found for file: {path}")
