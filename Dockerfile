FROM python:3.12 AS base

WORKDIR /app

# TA-Lib
RUN wget https://github.com/ta-lib/ta-lib/releases/download/v0.6.4/ta-lib-0.6.4-src.tar.gz && \
  tar -xzf ta-lib-0.6.4-src.tar.gz && \
  cd ta-lib-0.6.4/ && \
  ./configure --prefix=/usr --build=aarch64-unknown-linux-gnu && \
  make && \
  make install

RUN rm -R ta-lib-0.6.4-src.tar.gz

COPY . .

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

FROM base AS runner
WORKDIR /app

EXPOSE 8000

# when running the container, add --db-path and a bind mount to the host's db file
ENTRYPOINT ["mcp", "run", "src/server.py"]