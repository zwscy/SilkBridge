# ── Stage 1: compile silk-v3-decoder ─────────────────────────────────────────
FROM debian:bookworm-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    git gcc g++ make ca-certificates libc-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build
RUN git clone --depth=1 https://github.com/kn007/silk-v3-decoder.git && \
    cd silk-v3-decoder/silk && make

# ── Stage 2: runtime image ────────────────────────────────────────────────────
FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder --chmod=755 /build/silk-v3-decoder/silk/decoder /usr/local/bin/silk-v3-decoder

RUN groupadd --gid 1001 appuser && \
    useradd --uid 1001 --gid 1001 --no-create-home appuser

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

USER appuser

EXPOSE 8080

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
