import base64
import hashlib
import os
import re
import logging
import json
import spacy
import tiktoken
import nltk
import pandas as pd

from abc import ABC, abstractmethod
from typing import List, Dict, Set, Iterable, Callable, Any, Union, Optional, Literal, Collection, Protocol,cast
from pydantic import BaseModel, Field
from dataclasses import dataclass, field

from doc.proc.pipeline.pipeline_base import PipelineExecutionContext
from doc.proc.step.step_base import StepBase, StepExecutionError, StepInputOutput, StepInstanceConfig
from doc.proc.models.docproc_request import DocProcRequest
from doc.proc.models.docproc_state import DocProcState

import graphrag.config.defaults as defs
from graphrag.config.enums import ChunkStrategyType
from graphrag.config.models.chunking_config import ChunkingConfig

logger = logging.getLogger("doc.proc.step.content_chunker") # need to specify the logger name as this module is loaded dynamically

EncodedText = list[int]
DecodeFn = Callable[[EncodedText], str]
EncodeFn = Callable[[str], EncodedText]
LengthFn = Callable[[str], int]

@dataclass
class TextChunk:
    """Text chunk class definition."""

    text_chunk: str
    source_doc_indices: list[int]
    n_tokens: int | None = None

@dataclass(frozen=True)
class Tokenizer:
    """Tokenizer data class."""

    chunk_overlap: int
    """Overlap in tokens between chunks"""
    tokens_per_chunk: int
    """Maximum number of tokens per chunk"""
    decode: DecodeFn
    """ Function to decode a list of token ids to a string"""
    encode: EncodeFn
    """ Function to encode a string to a list of token ids"""


class TextSplitter(ABC):
    """Text splitter class definition."""

    _chunk_size: int
    _chunk_overlap: int
    _length_function: LengthFn
    _keep_separator: bool
    _add_start_index: bool
    _strip_whitespace: bool

    def __init__(
        self,
        # based on text-ada-002-embedding max input buffer length
        # https://platform.openai.com/docs/guides/embeddings/second-generation-models
        chunk_size: int = 8191,
        chunk_overlap: int = 100,
        length_function: LengthFn = len,
        keep_separator: bool = False,
        add_start_index: bool = False,
        strip_whitespace: bool = True,
    ):
        """Init method definition."""
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap
        self._length_function = length_function
        self._keep_separator = keep_separator
        self._add_start_index = add_start_index
        self._strip_whitespace = strip_whitespace

    @abstractmethod
    def split_text(self, text: str | list[str]) -> Iterable[str]:
        """Split text method definition."""


class NoopTextSplitter(TextSplitter):
    """Noop text splitter class definition."""

    def split_text(self, text: str | list[str]) -> Iterable[str]:
        """Split text method definition."""
        return [text] if isinstance(text, str) else text


class TokenTextSplitter(TextSplitter):
    """Token text splitter class definition."""

    _allowed_special: Literal["all"] | set[str]
    _disallowed_special: Literal["all"] | Collection[str]

    def __init__(
        self,
        encoding_name: str = defs.ENCODING_MODEL,
        model_name: str | None = None,
        allowed_special: Literal["all"] | set[str] | None = None,
        disallowed_special: Literal["all"] | Collection[str] = "all",
        **kwargs: Any,
    ):
        """Init method definition."""
        super().__init__(**kwargs)
        if model_name is not None:
            try:
                enc = tiktoken.encoding_for_model(model_name)
            except KeyError:
                logger.exception("Model %s not found, using %s", model_name, encoding_name)
                enc = tiktoken.get_encoding(encoding_name)
        else:
            enc = tiktoken.get_encoding(encoding_name)
        self._tokenizer = enc
        self._allowed_special = allowed_special or set()
        self._disallowed_special = disallowed_special

    def encode(self, text: str) -> list[int]:
        """Encode the given text into an int-vector."""
        return self._tokenizer.encode(
            text,
            allowed_special=self._allowed_special,
            disallowed_special=self._disallowed_special,
        )

    def num_tokens(self, text: str) -> int:
        """Return the number of tokens in a string."""
        return len(self.encode(text))

    def split_text(self, text: str | list[str]) -> list[str]:
        """Split text method."""
        if isinstance(text, list):
            text = " ".join(text)
        elif cast("bool", pd.isna(text)) or text == "":
            return []
        if not isinstance(text, str):
            msg = f"Attempting to split a non-string value, actual is {type(text)}"
            raise TypeError(msg)

        tokenizer = Tokenizer(
            chunk_overlap=self._chunk_overlap,
            tokens_per_chunk=self._chunk_size,
            decode=self._tokenizer.decode,
            encode=lambda text: self.encode(text),
        )

        return split_single_text_on_tokens(text=text, tokenizer=tokenizer)


def split_single_text_on_tokens(text: str, tokenizer: Tokenizer) -> list[str]:
    """Split a single text and return chunks using the tokenizer."""
    result = []
    input_ids = tokenizer.encode(text)

    start_idx = 0
    cur_idx = min(start_idx + tokenizer.tokens_per_chunk, len(input_ids))
    chunk_ids = input_ids[start_idx:cur_idx]

    while start_idx < len(input_ids):
        chunk_text = tokenizer.decode(list(chunk_ids))
        result.append(chunk_text)  # Append chunked text as string
        if cur_idx == len(input_ids):
            break
        start_idx += tokenizer.tokens_per_chunk - tokenizer.chunk_overlap
        cur_idx = min(start_idx + tokenizer.tokens_per_chunk, len(input_ids))
        chunk_ids = input_ids[start_idx:cur_idx]

    return result


# Adapted from - https://github.com/langchain-ai/langchain/blob/77b359edf5df0d37ef0d539f678cf64f5557cb54/libs/langchain/langchain/text_splitter.py#L471
# So we could have better control over the chunking process
def split_multiple_texts_on_tokens(
    texts: list[str], tokenizer: Tokenizer
) -> list[TextChunk]:
    """Split multiple texts and return chunks with metadata using the tokenizer."""
    result = []
    mapped_ids = []

    for source_doc_idx, text in enumerate(texts):
        encoded = tokenizer.encode(text)
        mapped_ids.append((source_doc_idx, encoded))

    input_ids = [
        (source_doc_idx, id) for source_doc_idx, ids in mapped_ids for id in ids
    ]

    start_idx = 0
    cur_idx = min(start_idx + tokenizer.tokens_per_chunk, len(input_ids))
    chunk_ids = input_ids[start_idx:cur_idx]

    while start_idx < len(input_ids):
        chunk_text = tokenizer.decode([id for _, id in chunk_ids])
        doc_indices = list({doc_idx for doc_idx, _ in chunk_ids})
        result.append(TextChunk(chunk_text, doc_indices, len(chunk_ids)))
        if cur_idx == len(input_ids):
            break
        start_idx += tokenizer.tokens_per_chunk - tokenizer.chunk_overlap
        cur_idx = min(start_idx + tokenizer.tokens_per_chunk, len(input_ids))
        chunk_ids = input_ids[start_idx:cur_idx]

    return result

def get_encoding_fn(encoding_name):
    """Get the encoding model."""
    enc = tiktoken.get_encoding(encoding_name)

    def encode(text: str) -> list[int]:
        if not isinstance(text, str):
            text = f"{text}"
        return enc.encode(text)

    def decode(tokens: list[int]) -> str:
        return enc.decode(tokens)

    return encode, decode

ChunkInput = str | list[str] | list[tuple[str, str]]
"""Input to a chunking strategy. Can be a string, a list of strings, or a list of tuples of (id, text)."""

ChunkStrategy = Callable[
    [list[str], ChunkingConfig], Iterable[TextChunk]
]

class ContentChunkerStep(StepBase):

    def __init__(self, instance_config: StepInstanceConfig, **kwargs):
        super().__init__(instance_config=instance_config, **kwargs)
        
        # Initialize settings with default values if not provided
        if not self.settings:
            self.settings = {}

        self.chunking_strategy = self.settings.get("chunking_strategy", "tokens")

        if self.chunking_strategy == "nlp":
            self.nlp = spacy.load('en_core_web_sm')

        self.chunking_config = ChunkingConfig()
        self.rechunk = self.settings.get("rechunk", False)

    async def run(self, input_data: dict, context: "PipelineExecutionContext") -> Dict:
        """
        Process a single document to extract content.
        
        :param document: Document dictionary containing file path and other metadata.
        :param context: PipelineExecutionContext instance.
        :param ai_model_inference_service: AI Model Inference Service instance.
        :return: Dictionary with processing statistics.
        """

        # Get the source
        document = input_data.data.get("document", {})

        content = ''
        chunks = document.get("chunks", [])
        existing_chunks = False

        if chunks and len(chunks) > 0:
            existing_chunks = True

        if (len(chunks) > 0 and self.rechunk):
            content = ""
            for chunk in chunks:
                content += chunk.get("raw_text","") + "\n"
        
        if (len(chunks) == 0):
            content = document.get("content","")
            encoding = document.get("encoding","")
            if encoding == "base64" and content:
                try:
                    content = base64.b64decode(content).decode('utf-8')
                except Exception as e:
                    raise StepExecutionError(f"Error decoding base64 content for document {document.get('id','unknown')}: {e}", cancel_request=True)

        if (not existing_chunks) or (existing_chunks and self.rechunk):
            chunks = []
            text_chunks = []

            if content != None:
                
                if self.chunking_strategy == "nlp":
                    text_chunks = self.run_nlp([content], self.chunking_config)
                elif self.chunking_strategy == "tokens":
                    text_chunks = self.run_tokens([content], self.chunking_config)
                elif self.chunking_strategy == "sentences":
                    text_chunks = self.run_sentences([content], self.chunking_config)

                for text_chunk in text_chunks:
                    chunk_data = {
                            'chunk_id': len(chunks),
                            'chunk_type': 'page',
                            'chunk_num': len(chunks),
                            'text': text_chunk.text_chunk,
                            'length' : len(text_chunk.text_chunk),
                            'size' : len(text_chunk.text_chunk),
                            'raw_text': text_chunk.text_chunk
                        }
                        
                    chunks.append(chunk_data)

        document['chunks'] = chunks
            
        return input_data

    def run_nlp(self,
        input: list[str],
        config: ChunkingConfig
    ) -> Iterable[TextChunk]:
        doc = self.nlp(input)
        sentences = list(doc.sents)
        for sentence in sentences:
            yield TextChunk(
                text_chunk=sentence.text,
                source_doc_indices=[0],
                n_tokens=len(sentence.text)
            )

    def run_tokens(
        self,
        input: list[str],
        config: ChunkingConfig
    ) -> Iterable[TextChunk]:
        """Chunks text into chunks based on encoding tokens."""
        tokens_per_chunk = config.size
        chunk_overlap = config.overlap
        encoding_name = config.encoding_model

        encode, decode = get_encoding_fn(encoding_name)
        return split_multiple_texts_on_tokens(
            input,
            Tokenizer(
                chunk_overlap=chunk_overlap,
                tokens_per_chunk=tokens_per_chunk,
                encode=encode,
                decode=decode,
            )
        )


    def run_sentences(self,
        input: list[str], _config: ChunkingConfig
    ) -> Iterable[TextChunk]:
        """Chunks text into multiple parts by sentence."""
        for doc_idx, text in enumerate(input):
            sentences = nltk.sent_tokenize(text)
            for sentence in sentences:
                yield TextChunk(
                    text_chunk=sentence,
                    source_doc_indices=[doc_idx],
                )