FROM python:3.11-slim

# Tools needed to fetch the upstream proxy source at build time
RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Pull the real, maintained mtprotoproxy source straight from upstream.
# Pinning to the "stable" branch as recommended by the project's own README.
RUN git clone --depth 1 -b stable https://github.com/alexbers/mtprotoproxy.git /app/mtprotoproxy

WORKDIR /app/mtprotoproxy

# Your own config + entrypoint override the ones that ship in the repo
COPY config.py /app/mtprotoproxy/config.py
COPY main.py /app/mtprotoproxy/main.py
COPY requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r /app/requirements.txt

# Koyeb routes traffic to whatever port you expose; using 8080 as requested
EXPOSE 8080

CMD ["python3", "main.py"]
