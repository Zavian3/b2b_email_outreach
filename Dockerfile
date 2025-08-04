# Multi-stage Dockerfile for Peekr B2B Automation
FROM python:3.9-slim as base

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Add streamlit to requirements for dashboard
RUN pip install streamlit plotly

# Copy application code
COPY . .

# Create non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port for dashboard
EXPOSE 8501

# Default command (can be overridden)
CMD ["python", "peekr_automation_master.py"]