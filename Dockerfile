FROM python:3.9-slim
WORKDIR /app
RUN useradd -m myuser
USER myuser
COPY . /app
RUN pip install --no-cache-dir requests==2.26.0
HEALTHCHECK --interval=30s --timeout=10s CMD ["curl","-f","http://localhost/health"]
CMD ["pytest"]