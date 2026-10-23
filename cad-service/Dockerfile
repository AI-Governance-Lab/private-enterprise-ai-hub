# CAD service: DWG/DXF area extraction + XLSX reconciliation.
# libredwg is compiled from source (no upstream .deb in Debian). For AutoCAD
# 2018+ (AC1032) higher reliability, upgrade to ODA File Converter — see
# CAD_README.md.

# ---------- Stage 1: build libredwg ----------
FROM debian:trixie-slim AS libredwg-builder

ARG LIBREDWG_VERSION=0.13.3

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        autoconf automake libtool pkg-config \
        perl \
        python3 \
        libpcre2-dev \
        curl ca-certificates \
        texinfo \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /src
RUN curl -fsSL "https://ftp.gnu.org/gnu/libredwg/libredwg-${LIBREDWG_VERSION}.tar.gz" -o libredwg.tar.gz \
    && tar -xzf libredwg.tar.gz --strip-components=1 \
    && rm libredwg.tar.gz \
    && ./configure --disable-bindings --enable-write --prefix=/usr/local \
    && make -j"$(nproc)" \
    && make install-strip \
    && ldconfig

# ---------- Stage 2: runtime ----------
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    LD_LIBRARY_PATH=/usr/local/lib

RUN apt-get update && apt-get install -y --no-install-recommends \
        libpcre2-8-0 \
        curl \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy libredwg binaries + shared libs from builder stage
COPY --from=libredwg-builder /usr/local/bin/dwg2dxf /usr/local/bin/
COPY --from=libredwg-builder /usr/local/bin/dwgread /usr/local/bin/
COPY --from=libredwg-builder /usr/local/lib/libredwg.so* /usr/local/lib/
RUN ldconfig

# Optional ODA File Converter (uncomment if you drop the .deb in build context):
# COPY ODAFileConverter_*.deb /tmp/oda.deb
# RUN apt-get update && apt-get install -y --no-install-recommends /tmp/oda.deb \
#     xvfb libglu1-mesa && rm -rf /var/lib/apt/lists/* /tmp/oda.deb

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app.py .

EXPOSE 8090

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -fsS http://127.0.0.1:8090/health || exit 1

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8090", "--workers", "1"]
