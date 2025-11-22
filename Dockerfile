# Dockerfile
ARG CUDA_TAG=12.8.0-runtime-ubuntu22.04
FROM nvidia/cuda:${CUDA_TAG}

ENV DEBIAN_FRONTEND=noninteractive
# install python and build deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip python3-dev build-essential wget ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY app/requirements.txt /app/requirements.txt

# pip install (do not force binary wheels that are incompatible)
RUN python3 -m pip install --upgrade pip setuptools wheel
RUN python3 -m pip install -r /app/requirements.txt

COPY app /app

# student_port should be set at build or run time; default 8000 for the FastAPI HTTP service
ARG STUDENT_PORT=8127
ENV STUDENT_PORT=${STUDENT_PORT}
EXPOSE ${STUDENT_PORT}
EXPOSE 8127

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${STUDENT_PORT} --workers 1"]
