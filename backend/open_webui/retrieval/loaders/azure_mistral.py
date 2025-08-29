import base64
import logging
import os
import sys
import time
from typing import Any, Dict, List

import requests
from langchain_core.documents import Document

from open_webui.env import SRC_LOG_LEVELS, GLOBAL_LOG_LEVEL

logging.basicConfig(stream=sys.stdout, level=GLOBAL_LOG_LEVEL)
log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS["RAG"])


class AzureMistralLoader:
    def __init__(
        self,
        api_key: str,
        endpoint: str,
        file_path: str,
        model: str = "mistral-document-ai-2505",
        timeout: int = 300,
        include_image_base64: bool = False,
    ):
        if not api_key:
            raise ValueError("API key cannot be empty.")
        if not endpoint:
            raise ValueError("Azure Mistral OCR endpoint cannot be empty.")
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found at {file_path}")

        self.api_key = api_key
        self.endpoint = endpoint.rstrip("/")
        self.file_path = file_path
        self.model = model
        self.timeout = timeout
        self.include_image_base64 = include_image_base64

        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "OpenWebUI-AzureMistralLoader/1.0",
        }

    def _process_results(self, ocr_response: Dict[str, Any]) -> List[Document]:
        pages_data = ocr_response.get("pages")
        if not pages_data:
            log.warning("No pages found in OCR response.")
            return [
                Document(
                    page_content="No text content found",
                    metadata={"error": "no_pages", "file_name": os.path.basename(self.file_path)},
                )
            ]

        documents: List[Document] = []
        total_pages = len(pages_data)
        for page_data in pages_data:
            page_content = page_data.get("markdown")
            page_index = page_data.get("index")
            if page_content is None or page_index is None:
                continue
            cleaned_content = page_content.strip() if isinstance(page_content, str) else str(page_content).strip()
            if not cleaned_content:
                continue
            documents.append(
                Document(
                    page_content=cleaned_content,
                    metadata={
                        "page": page_index,
                        "page_label": page_index + 1,
                        "total_pages": total_pages,
                        "file_name": os.path.basename(self.file_path),
                        "processing_engine": "mistral-ocr-azure",
                        "content_length": len(cleaned_content),
                    },
                )
            )
        if not documents:
            return [
                Document(
                    page_content="No valid text content found in document",
                    metadata={
                        "error": "no_valid_pages",
                        "total_pages": total_pages,
                        "file_name": os.path.basename(self.file_path),
                    },
                )
            ]
        return documents

    def load(self) -> List[Document]:
        start_time = time.time()
        try:
            with open(self.file_path, "rb") as f:
                file_bytes = f.read()
            b64 = base64.b64encode(file_bytes).decode("utf-8")
            data_url = f"data:application/pdf;base64,{b64}"

            payload: Dict[str, Any] = {
                "model": self.model,
                "document": {
                    "type": "document_url",
                    "document_url": data_url,
                },
                "include_image_base64": self.include_image_base64,
            }

            url = f"{self.endpoint}/providers/mistral/azure/ocr"
            resp = requests.post(url, headers=self.headers, json=payload, timeout=self.timeout)
            resp.raise_for_status()
            ocr_response = resp.json()

            docs = self._process_results(ocr_response)
            elapsed = time.time() - start_time
            log.info(f"Azure Mistral OCR completed in {elapsed:.2f}s, produced {len(docs)} documents")
            return docs
        except Exception as e:
            log.error(f"Azure Mistral OCR failed: {e}")
            return [
                Document(
                    page_content=f"Error during processing: {e}",
                    metadata={
                        "error": "processing_failed",
                        "file_name": os.path.basename(self.file_path),
                    },
                )
            ]


