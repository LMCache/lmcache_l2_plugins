FROM python:3.12-bookworm

# CPU extensions are required for real server/worker transfers.
ENV NO_GPU_EXT=1 MAX_JOBS=1 LMCACHE_TRACK_USAGE=false DO_NOT_TRACK=1
RUN python -m pip install --no-cache-dir uv \
    && uv pip install --system torch --index-url https://download.pytorch.org/whl/cpu
ARG LMCACHE_REF=dev
RUN git clone https://github.com/LMCache/LMCache.git /opt/LMCache \
    && git -C /opt/LMCache checkout "$LMCACHE_REF" \
    && git -C /opt/LMCache rev-parse HEAD | tee /opt/lmcache-revision.txt \
    && uv pip install --system -r /opt/LMCache/requirements/build.txt \
    && uv pip install --system --no-build-isolation /opt/LMCache
WORKDIR /opt/plugins
COPY pyproject.toml README.md ./
COPY lmcache_l2_plugins ./lmcache_l2_plugins
RUN uv pip install --system ".[autumn,test]" pytest-timeout \
    && uv pip freeze --system > /opt/runtime-versions.txt
COPY tests/e2e/test_server_roundtrip.py ./tests/e2e/test_server_roundtrip.py
CMD ["python", "-m", "pytest", "-v", "-s", "--timeout=180", "--junitxml=/artifacts/junit.xml", "--basetemp=/artifacts/pytest", "tests/e2e/test_server_roundtrip.py"]
