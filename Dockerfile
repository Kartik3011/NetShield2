# 1. Base Image: Use the official Python image for simplicity and size reduction.
FROM python:3.11-slim

# Set environment variables for non-interactive commands
ENV DEBIAN_FRONTEND=noninteractive

# 2. Install System Dependencies (CRITICAL: Installs FFmpeg and git)
# FFmpeg is still necessary for the 'Content Forensic' page (yt-dlp audio extraction).
# git is often needed for installing some Python packages or dependencies.
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ffmpeg \
        git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 3. Environment Variables: Set the port Streamlit will use
ENV PORT=8501
EXPOSE 8501

# 4. Set working directory
WORKDIR /app

# 5. Copy requirements
COPY requirements.txt .

# 6. Install Python libraries (CRITICAL FIX: Use --break-system-packages for Python 3.11+)
# This flag overrides the 'externally-managed-environment' error.
RUN pip install --no-cache-dir -r requirements.txt --break-system-packages

# 7. Copy all other application code
COPY . .

# 8. Create Streamlit secrets file
# This step forces the creation of the secrets.toml file 
RUN mkdir -p /root/.streamlit/ && \
    sh -c 'printf "[secrets]\n\
    YOUTUBE_API_KEY=\"$YOUTUBE_API_KEY\"\n\
    ASSEMBLYAI_API_KEY=\"$ASSEMBLYAI_API_KEY\"\n\
    GROQ_API_KEY=\"$GROQ_API_KEY\"\n\
    NVIDIA_API_KEY=\"$NVIDIA_API_KEY\"\n\
    NEWS_API_KEY=\"$NEWS_API_KEY\"\n\
    " > /root/.streamlit/secrets.toml'

# 9. Entrypoint: Command to run the Streamlit app
ENTRYPOINT ["streamlit", "run", "Dashboard.py", "--server.port=8501", "--server.address=0.0.0.0"]
