FROM python:3.11-alpine

LABEL maintainer="podtriage-team"
LABEL version="1.0"
LABEL description="Kubernetes Pod Health & Incident Triage Engine"

WORKDIR /app

# Copy CLI engine directly
COPY podtriage.py /app/podtriage.py

# Ensure executable permissions
RUN chmod +x /app/podtriage.py

ENTRYPOINT ["python", "/app/podtriage.py"]
