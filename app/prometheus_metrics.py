# app/prometheus_metrics.py
from prometheus_client import Counter, Histogram, Gauge, generate_latest, REGISTRY, CollectorRegistry, CONTENT_TYPE_LATEST

REQUEST_COUNT = Counter('gpu_service_requests_total', 'Total number of /add requests', ['endpoint', 'method', 'status'])
REQUEST_LATENCY = Histogram('gpu_service_request_latency_seconds', 'Latency for /add', ['endpoint', 'method'])
GPU_MEMORY_USED = Gauge('gpu_memory_used_mb', 'GPU memory used in MB', ['gpu_index'])
GPU_MEMORY_TOTAL = Gauge('gpu_memory_total_mb', 'GPU total memory in MB', ['gpu_index'])

def metrics_response():
    data = generate_latest(REGISTRY)
    return data, CONTENT_TYPE_LATEST
