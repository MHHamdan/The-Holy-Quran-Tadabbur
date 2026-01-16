# Tadabbur Model Serving with TorchServe

Production-ready model serving infrastructure for the cross-encoder reranking model.

## Quick Start

### 1. Package the Model

```bash
# Install dependencies
pip install torch-model-archiver transformers

# Package the model
python package_model.py --output-dir ./models

# For specific model variants:
python package_model.py --model-alias tinybert --output-dir ./models  # Fastest
python package_model.py --model-alias multilingual --output-dir ./models  # Multi-language
```

### 2. Start TorchServe

```bash
# Using Docker Compose
docker-compose -f docker-compose.serving.yml up -d

# Or manually with Docker
docker build -t tadabbur-torchserve:latest .
docker run -d -p 8080:8080 -p 8081:8081 -p 8082:8082 \
  -v $(pwd)/models:/models \
  tadabbur-torchserve:latest
```

### 3. Test the Endpoint

```bash
# Health check
curl http://localhost:8080/ping

# Inference request
curl -X POST http://localhost:8080/predictions/cross_encoder \
  -H "Content-Type: application/json" \
  -d '{
    "pairs": [
      {"query": "What is patience?", "document": "Patience is a virtue in Islam."},
      {"query": "What is patience?", "document": "The weather is nice today."}
    ]
  }'
```

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Tadabbur API   │────▶│   Nginx LB      │────▶│   TorchServe    │
│    (Backend)    │     │   (Optional)    │     │  (Model Server) │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                        │
                                                        ▼
                                               ┌─────────────────┐
                                               │  Cross-Encoder  │
                                               │     Model       │
                                               └─────────────────┘
```

## Files

| File | Description |
|------|-------------|
| `config.properties` | TorchServe configuration |
| `cross_encoder_handler.py` | Custom model handler for inference |
| `Dockerfile` | Docker image for TorchServe |
| `docker-compose.serving.yml` | Docker Compose deployment |
| `nginx.conf` | Load balancer configuration |
| `package_model.py` | Model packaging script |
| `torchserve_client.py` | Python client for backend integration |

## API Endpoints

| Endpoint | Port | Description |
|----------|------|-------------|
| `/predictions/{model}` | 8080 | Inference API |
| `/ping` | 8080 | Health check |
| `/models` | 8081 | Model management |
| `/metrics` | 8082 | Prometheus metrics |

## Configuration

Environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `TORCHSERVE_HOST` | `localhost` | TorchServe hostname |
| `TORCHSERVE_INFERENCE_PORT` | `8080` | Inference API port |
| `TORCHSERVE_MODEL_NAME` | `cross_encoder` | Model name |
| `TORCHSERVE_TIMEOUT` | `30.0` | Request timeout (seconds) |

## GPU Support

For GPU inference, use the GPU Dockerfile:

```dockerfile
FROM pytorch/torchserve:0.9.0-gpu
```

And update `config.properties`:

```properties
device_type=gpu
number_of_gpu=1
```

## Scaling

### Horizontal Scaling

1. Add more TorchServe instances to `docker-compose.serving.yml`
2. Update `nginx.conf` upstream servers
3. Enable the load balancer profile:

```bash
docker-compose -f docker-compose.serving.yml --profile loadbalancer up -d
```

### Worker Scaling

Scale workers via Management API:

```bash
curl -X PUT "http://localhost:8081/models/cross_encoder?min_worker=2&max_worker=8"
```

## Monitoring

Prometheus metrics available at `http://localhost:8082/metrics`:

- `ts_model_latency` - Model inference latency
- `ts_queue_latency` - Queue waiting time
- `ts_inference_count` - Total inference count
- `ts_inference_latency_seconds` - Detailed latency histogram

## Integration with Backend

```python
from serving.torchserve_client import get_torchserve_client, rerank_with_torchserve

# Option 1: Using the client directly
async with get_torchserve_client() as client:
    result = await client.rerank(query, documents)
    print(f"Scores: {result.scores}, Latency: {result.latency_ms}ms")

# Option 2: Convenience function
scores, latency = await rerank_with_torchserve(query, documents)
```

## Troubleshooting

### Model not loading

```bash
# Check model status
curl http://localhost:8081/models/cross_encoder

# Check TorchServe logs
docker logs tadabbur-torchserve
```

### Slow inference

1. Enable GPU if available
2. Increase batch size in `config.properties`
3. Enable FP16 inference
4. Scale workers

### Out of memory

1. Reduce `batch_size` in config
2. Use smaller model variant (TinyBERT)
3. Reduce `max_workers`
