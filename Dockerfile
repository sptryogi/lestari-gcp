FROM python:3.10-slim

# Install OS dependencies (tambahkan yang dibutuhkan untuk openpyxl dan Excel)
RUN apt-get update && apt-get install -y \
    git gcc libgl1-mesa-glx libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Expose port
EXPOSE 8501

# Start Streamlit
CMD ["streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true", "--server.runOnSave=false" "--server.runOnSave=false"]
