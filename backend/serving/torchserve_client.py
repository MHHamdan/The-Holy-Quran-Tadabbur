"""
TorchServe Client for Tadabbur Backend
Arabic: عميل TorchServe للواجهة الخلفية

This client provides an async interface for communicating with
the TorchServe cross-encoder model serving endpoint.
"""

import asyncio
import logging
import os
import time
from dataclasses import dataclass
from typing import List, Optional, Tuple

import aiohttp

logger = logging.getLogger(__name__)


@dataclass
class TorchServeConfig:
    """Configuration for TorchServe client."""
    host: str = os.getenv("TORCHSERVE_HOST", "localhost")
    inference_port: int = int(os.getenv("TORCHSERVE_INFERENCE_PORT", "8080"))
    management_port: int = int(os.getenv("TORCHSERVE_MANAGEMENT_PORT", "8081"))
    metrics_port: int = int(os.getenv("TORCHSERVE_METRICS_PORT", "8082"))
    model_name: str = os.getenv("TORCHSERVE_MODEL_NAME", "cross_encoder")
    timeout: float = float(os.getenv("TORCHSERVE_TIMEOUT", "30.0"))
    max_retries: int = int(os.getenv("TORCHSERVE_MAX_RETRIES", "3"))
    retry_delay: float = float(os.getenv("TORCHSERVE_RETRY_DELAY", "0.5"))


@dataclass
class RerankerResult:
    """Result from cross-encoder reranking."""
    scores: List[float]
    request_id: str
    latency_ms: float
    from_cache: bool = False


class TorchServeClient:
    """
    Async client for TorchServe cross-encoder model.

    Usage:
        client = TorchServeClient()
        async with client:
            result = await client.rerank(query, documents)
    """

    def __init__(self, config: Optional[TorchServeConfig] = None):
        self.config = config or TorchServeConfig()
        self._session: Optional[aiohttp.ClientSession] = None
        self._healthy = False
        self._last_health_check = 0.0
        self._health_check_interval = 30.0

    @property
    def inference_url(self) -> str:
        return f"http://{self.config.host}:{self.config.inference_port}"

    @property
    def management_url(self) -> str:
        return f"http://{self.config.host}:{self.config.management_port}"

    @property
    def metrics_url(self) -> str:
        return f"http://{self.config.host}:{self.config.metrics_port}"

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def connect(self):
        """Initialize HTTP session."""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            self._session = aiohttp.ClientSession(timeout=timeout)
            logger.info(f"Connected to TorchServe at {self.inference_url}")

    async def close(self):
        """Close HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None
            logger.info("TorchServe client connection closed")

    async def is_healthy(self, force_check: bool = False) -> bool:
        """
        Check if TorchServe is healthy.

        Args:
            force_check: Force health check even if recently checked

        Returns:
            True if healthy, False otherwise
        """
        now = time.time()
        if not force_check and (now - self._last_health_check) < self._health_check_interval:
            return self._healthy

        try:
            await self.connect()
            async with self._session.get(f"{self.inference_url}/ping") as response:
                self._healthy = response.status == 200
                self._last_health_check = now
                return self._healthy
        except Exception as e:
            logger.warning(f"TorchServe health check failed: {e}")
            self._healthy = False
            self._last_health_check = now
            return False

    async def rerank(
        self,
        query: str,
        documents: List[str],
        request_id: str = ""
    ) -> RerankerResult:
        """
        Rerank documents using cross-encoder model.

        Args:
            query: Search query
            documents: List of documents to rerank
            request_id: Optional request ID for tracing

        Returns:
            RerankerResult with scores and metadata
        """
        if not documents:
            return RerankerResult(
                scores=[],
                request_id=request_id,
                latency_ms=0.0
            )

        start_time = time.time()

        # Prepare request payload
        pairs = [{"query": query, "document": doc} for doc in documents]
        payload = {
            "pairs": pairs,
            "request_id": request_id
        }

        # Make request with retries
        result = await self._request_with_retry(
            method="POST",
            url=f"{self.inference_url}/predictions/{self.config.model_name}",
            json=payload
        )

        latency_ms = (time.time() - start_time) * 1000

        return RerankerResult(
            scores=result.get("scores", []),
            request_id=result.get("request_id", request_id),
            latency_ms=latency_ms
        )

    async def rerank_batch(
        self,
        query: str,
        document_batches: List[List[str]],
        request_id: str = ""
    ) -> List[RerankerResult]:
        """
        Rerank multiple document batches concurrently.

        Args:
            query: Search query
            document_batches: List of document batches
            request_id: Base request ID

        Returns:
            List of RerankerResults
        """
        tasks = [
            self.rerank(query, docs, f"{request_id}_{i}")
            for i, docs in enumerate(document_batches)
        ]
        return await asyncio.gather(*tasks)

    async def _request_with_retry(
        self,
        method: str,
        url: str,
        **kwargs
    ) -> dict:
        """
        Make HTTP request with retry logic.

        Args:
            method: HTTP method
            url: Request URL
            **kwargs: Additional request arguments

        Returns:
            Response JSON

        Raises:
            Exception: If all retries fail
        """
        await self.connect()
        last_error = None

        for attempt in range(self.config.max_retries):
            try:
                async with self._session.request(method, url, **kwargs) as response:
                    if response.status == 200:
                        return await response.json()

                    error_text = await response.text()
                    logger.warning(
                        f"TorchServe request failed (attempt {attempt + 1}): "
                        f"status={response.status}, error={error_text}"
                    )
                    last_error = Exception(f"HTTP {response.status}: {error_text}")

            except asyncio.TimeoutError:
                logger.warning(f"TorchServe request timeout (attempt {attempt + 1})")
                last_error = asyncio.TimeoutError("Request timeout")

            except aiohttp.ClientError as e:
                logger.warning(f"TorchServe connection error (attempt {attempt + 1}): {e}")
                last_error = e

            if attempt < self.config.max_retries - 1:
                await asyncio.sleep(self.config.retry_delay * (attempt + 1))

        raise last_error or Exception("All retries failed")

    async def get_model_status(self) -> dict:
        """
        Get model status from management API.

        Returns:
            Model status dictionary
        """
        await self.connect()
        async with self._session.get(
            f"{self.management_url}/models/{self.config.model_name}"
        ) as response:
            if response.status == 200:
                return await response.json()
            return {"status": "unknown", "error": await response.text()}

    async def get_metrics(self) -> str:
        """
        Get Prometheus metrics from metrics API.

        Returns:
            Metrics in Prometheus format
        """
        await self.connect()
        async with self._session.get(f"{self.metrics_url}/metrics") as response:
            if response.status == 200:
                return await response.text()
            return ""

    async def scale_workers(self, min_workers: int = 1, max_workers: int = 4) -> bool:
        """
        Scale model workers.

        Args:
            min_workers: Minimum number of workers
            max_workers: Maximum number of workers

        Returns:
            True if successful
        """
        await self.connect()
        params = {
            "min_worker": min_workers,
            "max_worker": max_workers
        }
        async with self._session.put(
            f"{self.management_url}/models/{self.config.model_name}",
            params=params
        ) as response:
            return response.status == 200


# Singleton instance
_client: Optional[TorchServeClient] = None


def get_torchserve_client() -> TorchServeClient:
    """Get or create TorchServe client singleton."""
    global _client
    if _client is None:
        _client = TorchServeClient()
    return _client


async def rerank_with_torchserve(
    query: str,
    documents: List[str],
    request_id: str = ""
) -> Tuple[List[float], float]:
    """
    Convenience function for reranking with TorchServe.

    Args:
        query: Search query
        documents: Documents to rerank
        request_id: Optional request ID

    Returns:
        Tuple of (scores, latency_ms)
    """
    client = get_torchserve_client()
    result = await client.rerank(query, documents, request_id)
    return result.scores, result.latency_ms
