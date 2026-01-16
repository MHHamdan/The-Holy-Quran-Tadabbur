#!/usr/bin/env python3
"""
Model Packaging Script for TorchServe
Arabic: سكريبت تحزيم النموذج لخدمة TorchServe

This script downloads and packages the cross-encoder model
into a MAR (Model Archive) file for TorchServe deployment.

Usage:
    python package_model.py [--model-name MODEL_NAME] [--output-dir OUTPUT_DIR]

Example:
    python package_model.py --model-name cross-encoder/ms-marco-MiniLM-L-6-v2 --output-dir ./models
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


# Default model configuration
DEFAULT_CONFIG = {
    "model_name": "cross-encoder/ms-marco-MiniLM-L-6-v2",
    "handler": "cross_encoder_handler.py",
    "max_length": 512,
    "use_fp16": True,
    "batch_size": 32,
}

# Alternative models for different use cases
AVAILABLE_MODELS = {
    "minilm": "cross-encoder/ms-marco-MiniLM-L-6-v2",  # Fast, good quality
    "tinybert": "cross-encoder/ms-marco-TinyBERT-L-2-v2",  # Fastest, smaller
    "multilingual": "amberoad/bert-multilingual-passage-reranking-msmarco",  # Multi-language
    "distilbert": "cross-encoder/ms-marco-MiniLM-L-12-v2",  # Better quality, slower
}


def download_model(model_name: str, output_dir: str) -> str:
    """
    Download model from Hugging Face Hub.

    Args:
        model_name: Hugging Face model identifier
        output_dir: Directory to save model files

    Returns:
        Path to downloaded model directory
    """
    print(f"Downloading model: {model_name}")

    try:
        from transformers import AutoTokenizer, AutoModelForSequenceClassification

        # Download tokenizer
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        tokenizer.save_pretrained(output_dir)

        # Download model
        model = AutoModelForSequenceClassification.from_pretrained(model_name)
        model.save_pretrained(output_dir)

        print(f"Model downloaded to: {output_dir}")
        return output_dir

    except Exception as e:
        print(f"Error downloading model: {e}")
        sys.exit(1)


def create_model_config(output_dir: str, config: dict):
    """
    Create model configuration file.

    Args:
        output_dir: Directory to save config
        config: Configuration dictionary
    """
    config_path = os.path.join(output_dir, "config.json")

    # Read existing config and merge
    existing_config = {}
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            existing_config = json.load(f)

    # Add serving-specific config
    existing_config.update({
        "max_length": config.get("max_length", 512),
        "use_fp16": config.get("use_fp16", True),
        "serving_config": {
            "batch_size": config.get("batch_size", 32),
            "max_batch_delay": 100,
        }
    })

    with open(config_path, 'w') as f:
        json.dump(existing_config, f, indent=2)

    print(f"Created config: {config_path}")


def package_mar(
    model_dir: str,
    handler_path: str,
    output_dir: str,
    model_name: str = "cross_encoder",
    version: str = "1.0"
) -> str:
    """
    Package model into MAR archive.

    Args:
        model_dir: Directory containing model files
        handler_path: Path to handler script
        output_dir: Directory to save MAR file
        model_name: Name for the model archive
        version: Model version

    Returns:
        Path to created MAR file
    """
    mar_file = os.path.join(output_dir, f"{model_name}.mar")

    # Build torch-model-archiver command
    cmd = [
        "torch-model-archiver",
        "--model-name", model_name,
        "--version", version,
        "--serialized-file", os.path.join(model_dir, "pytorch_model.bin"),
        "--handler", handler_path,
        "--extra-files", f"{os.path.join(model_dir, 'config.json')},{os.path.join(model_dir, 'tokenizer.json')},{os.path.join(model_dir, 'special_tokens_map.json')},{os.path.join(model_dir, 'tokenizer_config.json')},{os.path.join(model_dir, 'vocab.txt')}",
        "--export-path", output_dir,
        "--force"
    ]

    print(f"Running: {' '.join(cmd)}")

    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"Created MAR archive: {mar_file}")
        return mar_file

    except subprocess.CalledProcessError as e:
        print(f"Error creating MAR archive: {e.stderr}")
        sys.exit(1)
    except FileNotFoundError:
        print("torch-model-archiver not found. Install with: pip install torch-model-archiver")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Package Cross-Encoder model for TorchServe")
    parser.add_argument(
        "--model-name",
        default=DEFAULT_CONFIG["model_name"],
        help=f"Model name from Hugging Face Hub (default: {DEFAULT_CONFIG['model_name']})"
    )
    parser.add_argument(
        "--model-alias",
        choices=list(AVAILABLE_MODELS.keys()),
        help="Use a pre-configured model alias"
    )
    parser.add_argument(
        "--output-dir",
        default="./models",
        help="Output directory for MAR file (default: ./models)"
    )
    parser.add_argument(
        "--handler",
        default="cross_encoder_handler.py",
        help="Path to handler script"
    )
    parser.add_argument(
        "--max-length",
        type=int,
        default=512,
        help="Maximum input sequence length (default: 512)"
    )
    parser.add_argument(
        "--no-fp16",
        action="store_true",
        help="Disable FP16 inference"
    )
    parser.add_argument(
        "--version",
        default="1.0",
        help="Model version (default: 1.0)"
    )

    args = parser.parse_args()

    # Resolve model name from alias
    model_name = args.model_name
    if args.model_alias:
        model_name = AVAILABLE_MODELS[args.model_alias]
        print(f"Using model alias '{args.model_alias}': {model_name}")

    # Create output directory
    output_dir = os.path.abspath(args.output_dir)
    os.makedirs(output_dir, exist_ok=True)

    # Find handler
    script_dir = os.path.dirname(os.path.abspath(__file__))
    handler_path = args.handler
    if not os.path.isabs(handler_path):
        handler_path = os.path.join(script_dir, handler_path)

    if not os.path.exists(handler_path):
        print(f"Handler not found: {handler_path}")
        sys.exit(1)

    # Create temporary directory for model files
    with tempfile.TemporaryDirectory() as temp_dir:
        model_dir = os.path.join(temp_dir, "model")
        os.makedirs(model_dir)

        # Download model
        download_model(model_name, model_dir)

        # Create config
        config = {
            "max_length": args.max_length,
            "use_fp16": not args.no_fp16,
            "batch_size": 32,
        }
        create_model_config(model_dir, config)

        # Package MAR
        mar_path = package_mar(
            model_dir=model_dir,
            handler_path=handler_path,
            output_dir=output_dir,
            model_name="cross_encoder",
            version=args.version
        )

        print(f"\nModel packaged successfully!")
        print(f"MAR file: {mar_path}")
        print(f"\nTo deploy with TorchServe:")
        print(f"  torchserve --start --model-store {output_dir} --models cross_encoder={mar_path}")


if __name__ == "__main__":
    main()
