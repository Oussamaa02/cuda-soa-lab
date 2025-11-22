# app/main.py
import io
import time
import numpy as np
import subprocess
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse, Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from prometheus_client import REGISTRY
from prometheus_client import Counter, Histogram, Gauge
from prometheus_client import CollectorRegistry

from gpu_kernel import gpu_matrix_add
from prometheus_metrics import REQUEST_COUNT, REQUEST_LATENCY, GPU_MEMORY_USED, GPU_MEMORY_TOTAL, metrics_response

app = FastAPI(title="GPU Matrix Add Service")

# Health
@app.get("/health")
def health():
    return {"status": "ok"}

def read_npz_file(upload: UploadFile):
    contents = upload.file.read()
    try:
        bio = io.BytesIO(contents)
        npz = np.load(bio, allow_pickle=False)
        arr = npz[npz.files[0]]
        return arr
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"invalid .npz file: {e}")
    finally:
        upload.file.close()

# GPU info endpoint: uses nvidia-smi (csv, noheader, nounits)
@app.get("/gpu-info")
def gpu_info():
    try:
        cmd = ["nvidia-smi",
               "--query-gpu=index,memory.used,memory.total,utilization.gpu",
               "--format=csv,noheader,nounits"]
        out = subprocess.check_output(cmd, universal_newlines=True)
        gpus = []
        for line in out.strip().splitlines():
            parts = [p.strip() for p in line.split(",")]
            idx, mem_used, mem_total, util = parts
            g = {"gpu": idx, "memory_used_MB": int(mem_used), "memory_total_MB": int(mem_total), "utilization_gpu": int(util)}
            gpus.append(g)

            # update gauges for Prometheus
            GPU_MEMORY_USED.labels(gpu_index=idx).set(int(mem_used))
            GPU_MEMORY_TOTAL.labels(gpu_index=idx).set(int(mem_total))

        return {"gpus": gpus}
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="nvidia-smi not found on host")
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"nvidia-smi failed: {e}")

# /add endpoint: accepts two .npz uploads
@app.post("/add")
def add_matrices(file_a: UploadFile = File(...), file_b: UploadFile = File(...)):
    endpoint = "/add"
    method = "POST"
    start = time.perf_counter()

    try:
        a = read_npz_file(file_a)
        b = read_npz_file(file_b)
        if a.shape != b.shape:
            REQUEST_COUNT.labels(endpoint=endpoint, method=method, status="400").inc()
            raise HTTPException(status_code=400, detail="Matrices must have the same shape")

        # convert to float32 (numba/cuda prefers float32)
        a = a.astype(np.float32)
        b = b.astype(np.float32)

        # run on GPU
        t0 = time.perf_counter()
        c = gpu_matrix_add(a, b)
        t1 = time.perf_counter()
        elapsed = t1 - t0

        total_elapsed = time.perf_counter() - start
        REQUEST_COUNT.labels(endpoint=endpoint, method=method, status="200").inc()
        REQUEST_LATENCY.labels(endpoint=endpoint, method=method).observe(total_elapsed)

        rows, cols = a.shape
        return {"matrix_shape": [rows, cols], "elapsed_time": float(elapsed), "device": "GPU"}
    except HTTPException:
        raise
    except Exception as e:
        REQUEST_COUNT.labels(endpoint=endpoint, method=method, status="500").inc()
        raise HTTPException(status_code=500, detail=str(e))

# /metrics endpoint for Prometheus to scrape
@app.get("/metrics")
def metrics():
    data, content_type = metrics_response()
    return Response(content=data, media_type=content_type)
