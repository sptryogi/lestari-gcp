FROM python:3.10-slim

# Install OS dependencies
RUN apt-get update && apt-get install -y git gcc && rm -rf /var/lib/apt/lists/*

# Set working dir
WORKDIR /app

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy code
COPY . .

# Expose port
EXPOSE 8501

# Start Streamlit
CMD ["streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0"]
