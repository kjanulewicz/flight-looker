FROM ubuntu:22.04

# Prevent interactive prompts during build
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    curl \
    wget \
    gnupg2 \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install NordVPN CLI
RUN curl -sSf https://downloads.nordcdn.com/apps/linux/install.sh -o /tmp/nordvpn-install.sh && \
    bash /tmp/nordvpn-install.sh || \
    (apt-get update && \
     wget -qO - https://repo.nordvpn.com/gpg/nordvpn_public.asc | apt-key add - && \
     echo "deb https://repo.nordvpn.com/deb/nordvpn/debian stable main" > /etc/apt/sources.list.d/nordvpn.list && \
     apt-get update && \
     apt-get install -y nordvpn && \
     rm -rf /var/lib/apt/lists/*)

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies (excluding nordvpn-api which is not available on PyPI)
RUN grep -v "nordvpn-api" requirements.txt > /tmp/requirements-filtered.txt && \
    pip3 install --no-cache-dir -r /tmp/requirements-filtered.txt

# Copy application files
COPY . .

# Create necessary directories
RUN mkdir -p charts data logs

# Set Python path
ENV PYTHONPATH=/app

# Create entrypoint script to start NordVPN daemon
RUN echo '#!/bin/bash\n\
# Start NordVPN daemon\n\
service nordvpn start 2>/dev/null || true\n\
sleep 2\n\
# Execute the main command\n\
exec "$@"\n\
' > /entrypoint.sh && chmod +x /entrypoint.sh

# Set entrypoint
ENTRYPOINT ["/entrypoint.sh"]

# Default command
CMD ["python3", "top_deals.py", "--help"]
