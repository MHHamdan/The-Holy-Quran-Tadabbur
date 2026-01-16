"""
Cross-Encoder Handler for TorchServe
Arabic: معالج نموذج إعادة الترتيب للخدمة الإنتاجية

This handler provides efficient batch inference for the cross-encoder
reranking model used in the Tadabbur RAG pipeline.
"""

import json
import logging
import os
from abc import ABC
from typing import List, Dict, Any, Tuple

import torch
from ts.torch_handler.base_handler import BaseHandler

logger = logging.getLogger(__name__)


class CrossEncoderHandler(BaseHandler, ABC):
    """
    Custom handler for Cross-Encoder models in TorchServe.

    Supports:
    - Batch inference for multiple query-document pairs
    - FP16 inference for faster GPU processing
    - Dynamic batching with configurable max delay
    """

    def __init__(self):
        super(CrossEncoderHandler, self).__init__()
        self.initialized = False
        self.model = None
        self.tokenizer = None
        self.device = None
        self.use_fp16 = False
        self.max_length = 512

    def initialize(self, context):
        """
        Initialize model and tokenizer.

        Args:
            context: TorchServe context with model directory info
        """
        self.manifest = context.manifest
        properties = context.system_properties
        model_dir = properties.get("model_dir")

        # Detect device
        if torch.cuda.is_available():
            self.device = torch.device("cuda")
            self.use_fp16 = True
            logger.info("Using CUDA for inference")
        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            self.device = torch.device("mps")
            self.use_fp16 = False  # MPS doesn't fully support FP16
            logger.info("Using MPS for inference")
        else:
            self.device = torch.device("cpu")
            self.use_fp16 = False
            logger.info("Using CPU for inference")

        # Load model configuration
        config_path = os.path.join(model_dir, "config.json")
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
                self.max_length = config.get("max_length", 512)
                self.use_fp16 = config.get("use_fp16", self.use_fp16)

        # Load tokenizer and model
        try:
            from transformers import AutoTokenizer, AutoModelForSequenceClassification

            self.tokenizer = AutoTokenizer.from_pretrained(model_dir)
            self.model = AutoModelForSequenceClassification.from_pretrained(model_dir)
            self.model.to(self.device)

            if self.use_fp16 and self.device.type == "cuda":
                self.model.half()
                logger.info("Model converted to FP16")

            self.model.eval()

            # Warmup
            self._warmup()

            self.initialized = True
            logger.info(f"Cross-encoder model loaded successfully on {self.device}")

        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise

    def _warmup(self):
        """Warmup model with dummy data for consistent latency."""
        logger.info("Warming up model...")
        dummy_texts = [
            ("What is patience?", "Patience is a virtue mentioned in the Quran."),
            ("Tell me about prayer", "Prayer is one of the pillars of Islam.")
        ]

        with torch.no_grad():
            for query, doc in dummy_texts:
                inputs = self.tokenizer(
                    query, doc,
                    padding=True,
                    truncation=True,
                    max_length=self.max_length,
                    return_tensors="pt"
                ).to(self.device)

                if self.use_fp16 and self.device.type == "cuda":
                    with torch.cuda.amp.autocast():
                        _ = self.model(**inputs)
                else:
                    _ = self.model(**inputs)

        logger.info("Warmup complete")

    def preprocess(self, data: List[Dict]) -> Tuple[torch.Tensor, List[Dict]]:
        """
        Preprocess input data for batch inference.

        Expected input format:
        {
            "pairs": [
                {"query": "...", "document": "..."},
                ...
            ]
        }

        Args:
            data: List of request dictionaries

        Returns:
            Tokenized inputs and metadata
        """
        all_pairs = []
        metadata = []

        for request in data:
            body = request.get("body", request)

            # Handle both string and dict inputs
            if isinstance(body, (bytes, bytearray)):
                body = json.loads(body.decode('utf-8'))
            elif isinstance(body, str):
                body = json.loads(body)

            pairs = body.get("pairs", [])

            # Track request boundaries for response assembly
            metadata.append({
                "start_idx": len(all_pairs),
                "count": len(pairs),
                "request_id": body.get("request_id", "")
            })

            all_pairs.extend(pairs)

        if not all_pairs:
            return None, metadata

        # Tokenize all pairs
        queries = [p.get("query", "") for p in all_pairs]
        documents = [p.get("document", "") for p in all_pairs]

        inputs = self.tokenizer(
            queries,
            documents,
            padding=True,
            truncation=True,
            max_length=self.max_length,
            return_tensors="pt"
        ).to(self.device)

        return inputs, metadata

    def inference(self, inputs: torch.Tensor) -> torch.Tensor:
        """
        Run model inference.

        Args:
            inputs: Tokenized input tensors

        Returns:
            Model logits/scores
        """
        if inputs is None:
            return None

        with torch.no_grad():
            if self.use_fp16 and self.device.type == "cuda":
                with torch.cuda.amp.autocast():
                    outputs = self.model(**inputs)
            else:
                outputs = self.model(**inputs)

        # Get scores (assuming single-class reranking model)
        if hasattr(outputs, 'logits'):
            scores = outputs.logits
            if scores.shape[-1] == 1:
                scores = scores.squeeze(-1)
            elif scores.shape[-1] == 2:
                # Binary classification: use positive class score
                scores = torch.softmax(scores, dim=-1)[:, 1]
        else:
            scores = outputs[0]

        return scores

    def postprocess(self, scores: torch.Tensor, metadata: List[Dict]) -> List[Dict]:
        """
        Postprocess scores into response format.

        Args:
            scores: Model output scores
            metadata: Request metadata for assembly

        Returns:
            List of response dictionaries
        """
        if scores is None:
            return [{"scores": [], "request_id": m.get("request_id", "")} for m in metadata]

        # Convert to list
        scores_list = scores.cpu().tolist()
        if not isinstance(scores_list, list):
            scores_list = [scores_list]

        responses = []
        for meta in metadata:
            start = meta["start_idx"]
            count = meta["count"]
            request_scores = scores_list[start:start + count]

            responses.append({
                "scores": request_scores,
                "count": len(request_scores),
                "request_id": meta.get("request_id", "")
            })

        return responses


# Export handler for TorchServe
_service = CrossEncoderHandler()


def handle(data, context):
    """Entry point for TorchServe."""
    try:
        if not _service.initialized:
            _service.initialize(context)

        if data is None:
            return None

        inputs, metadata = _service.preprocess(data)
        scores = _service.inference(inputs)
        return _service.postprocess(scores, metadata)

    except Exception as e:
        logger.error(f"Handler error: {e}")
        raise
