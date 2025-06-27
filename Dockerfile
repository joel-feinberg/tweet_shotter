FROM python:3.9-slim

WORKDIR /app

# Install system dependencies including Chrome
# Includes fonts, language packs, and X11 for headless Chrome
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    gnupg \
    fonts-liberation \
    libfreetype6 \
    libxcb1 \
    xdg-utils \
    libpng16-16 \
    libnss3 \
    libx11-xcb1 \
    libxcb-dri3-0 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxfixes3 \
    libxi6 \
    libxrandr2 \
    libxrender1 \
    libxss1 \
    libxtst6 \
    xvfb \
    unzip \
    # Add jq here as it's needed for the new chromedriver step
    jq \
    && rm -rf /var/lib/apt/lists/*

# Install Chrome
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Set up ChromeDriver (<<<<< THIS SECTION IS UPDATED for rmdir fix >>>>>)
RUN \
    # Fetch the download URL for the latest stable ChromeDriver for Linux64
    CHROMEDRIVER_INFO_URL="https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions-with-downloads.json" && \
    CHROMEDRIVER_DOWNLOAD_URL=$(wget -qO- "${CHROMEDRIVER_INFO_URL}" | jq -r '.channels.Stable.downloads.chromedriver[] | select(.platform=="linux64") | .url') && \
    \
    # Check if the URL was successfully retrieved
    if [ -z "${CHROMEDRIVER_DOWNLOAD_URL}" ]; then \
      echo "ERROR: Failed to retrieve ChromeDriver download URL." >&2; \
      exit 1; \
    fi && \
    \
    echo "INFO: Downloading ChromeDriver from ${CHROMEDRIVER_DOWNLOAD_URL}" && \
    wget -q "${CHROMEDRIVER_DOWNLOAD_URL}" -O /tmp/chromedriver.zip && \
    \
    # Prepare destination directory
    mkdir -p /app/drivers && \
    unzip -q /tmp/chromedriver.zip -d /app/drivers && \
    \
    # ChromeDriver from CfT is often in a subdirectory like 'chromedriver-linux64' within the zip
    # Move it to the expected location /app/drivers/chromedriver
    if [ -f /app/drivers/chromedriver-linux64/chromedriver ]; then \
      echo "INFO: Moving chromedriver from /app/drivers/chromedriver-linux64/chromedriver to /app/drivers/chromedriver" && \
      mv /app/drivers/chromedriver-linux64/chromedriver /app/drivers/chromedriver && \
      # Use rm -rf to remove the directory even if it contains other files like LICENSE
      echo "INFO: Removing /app/drivers/chromedriver-linux64 directory" && \
      rm -rf /app/drivers/chromedriver-linux64; \
    elif [ ! -f /app/drivers/chromedriver ]; then \
      echo "ERROR: ChromeDriver executable not found at /app/drivers/chromedriver or /app/drivers/chromedriver-linux64/chromedriver after unzip." >&2; \
      ls -lR /app/drivers; \
      exit 1; \
    else \
      echo "INFO: ChromeDriver found directly at /app/drivers/chromedriver"; \
    fi && \
    \
    chmod +x /app/drivers/chromedriver && \
    \
    # Verify chromedriver
    echo "INFO: ChromeDriver version: $(/app/drivers/chromedriver --version)" && \
    \
    rm /tmp/chromedriver.zip && \
    echo "INFO: ChromeDriver setup complete."

# Configure WebDriverManager cache directories
# Create the cache directory structure that WebDriverManager expects
RUN mkdir -p /app/.wdm/drivers/chromedriver && \
    # Get Chrome version to match with ChromeDriver
    CHROME_VERSION=$(google-chrome --version | grep -oE '[0-9]+\.[0-9]+\.[0-9]+') && \
    CHROMEDRIVER_VERSION=$(/app/drivers/chromedriver --version | grep -oE '[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+') && \
    \
    # Create the expected cache directory structure for WebDriverManager
    mkdir -p "/app/.wdm/drivers/chromedriver/${CHROMEDRIVER_VERSION}/linux64" && \
    \
    # Copy the pre-installed chromedriver to the cache location
    cp /app/drivers/chromedriver "/app/.wdm/drivers/chromedriver/${CHROMEDRIVER_VERSION}/linux64/chromedriver" && \
    chmod +x "/app/.wdm/drivers/chromedriver/${CHROMEDRIVER_VERSION}/linux64/chromedriver" && \
    \
    echo "INFO: ChromeDriver cached for WebDriverManager at /app/.wdm/drivers/chromedriver/${CHROMEDRIVER_VERSION}/linux64/chromedriver"

# Copy requirements first (for better caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application files
COPY . .

# Make sure the output directory exists
RUN mkdir -p /app/output_screenshots

# Create a non-root user to run the application
RUN useradd -m appuser
RUN chown -R appuser:appuser /app
USER appuser

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=app.py
# Ensure PATH includes /app/drivers if your app relies on chromedriver being in PATH
# Alternatively, configure Selenium to use /app/drivers/chromedriver directly
ENV PATH="/app/drivers:${PATH}"

# Configure WebDriverManager environment variables
ENV WDM_LOCAL=1
ENV WDM_LOG=0
ENV WDM_SSL_VERIFY=0
# Set the WebDriverManager cache directory to our pre-populated cache
ENV WDM_CACHE_ROOT="/app/.wdm"

# Expose the port that Flask will run on
EXPOSE 5000

# Run with Gunicorn production server
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "--timeout", "120", "app:app"]