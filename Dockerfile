FROM nikhilbadyal/docker-py-revanced-base

# Copy and install Python dependencies
COPY requirements.txt .
RUN python -m pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

## Chrome dependencies
RUN apt-get update -y && \
    apt-get install -y --no-install-recommends \
    curl gnupg2 unzip xvfb

# Install chrome and chromedriver
COPY ./src/browser/setup_browser.sh /setup_chrome_webdriver.sh
RUN sed -i 's/\r$//g' /setup_chrome_webdriver.sh && \
    sed -i 's/sudo\s//g' /setup_chrome_webdriver.sh
RUN bash /setup_chrome_webdriver.sh

# Copy entrypoint script
COPY ./entrypoint /entrypoint
RUN sed -i 's/\r$//g' /entrypoint && chmod +x /entrypoint

# Copy application code
COPY . ${APP_HOME}

# Set the default command to run the entrypoint script
CMD [ "bash", "/entrypoint" ]
