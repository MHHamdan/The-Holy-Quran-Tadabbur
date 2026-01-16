# TorchServe Docker Image for Tadabbur Cross-Encoder
# Arabic: صورة Docker لخدمة نموذج إعادة الترتيب
#
# Build:
#   docker build -t tadabbur-torchserve:latest .
#
# Run:
#   docker run -p 8080:8080 -p 8081:8081 -p 8082:8082 \
#     -v $(pwd)/models:/models \
#     tadabbur-torchserve:latest

FROM pytorch/torchserve:0.9.0-cpu

# For GPU support, use:
# FROM pytorch/torchserve:0.9.0-gpu

LABEL maintainer="Tadabbur Team"
LABEL description="TorchServe for Cross-Encoder Reranking Model"

# Set environment variables
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install additional dependencies
USER root
RUN pip install --no-cache-dir \
    transformers>=4.30.0 \
    sentence-transformers>=2.2.0 \
    numpy>=1.24.0

# Create directories
RUN mkdir -p /models /snapshots /logs

# Copy configuration
COPY config.properties /home/model-server/config.properties
COPY cross_encoder_handler.py /home/model-server/handlers/

# Set permissions
RUN chown -R model-server:model-server /models /snapshots /logs /home/model-server

USER model-server

# Expose ports
# 8080 - Inference API
# 8081 - Management API
# 8082 - Metrics API
EXPOSE 8080 8081 8082

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8080/ping || exit 1

# Start TorchServe
CMD ["torchserve", \
     "--start", \
     "--model-store", "/models", \
     "--ts-config", "/home/model-server/config.properties", \
     "--foreground"]
