FROM python:3.11-slim-bullseye

ENV VIRTUAL_ENV=/usr/local
# Install basics
RUN apt-get update -y && apt-get install -y zip wget apt-transport-https ca-certificates gnupg curl
# Install mc
RUN curl https://dl.min.io/client/mc/release/linux-amd64/mc -o /usr/bin/mc && chmod +x /usr/bin/mc
# Install gcloud
RUN echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list && curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | gpg --dearmor -o /usr/share/keyrings/cloud.google.gpg && apt-get update -y && apt-get install google-cloud-sdk -y

# Install the python stuff.
COPY deps/requirements.txt requirements.txt
RUN pip install uv && uv pip install -r requirements.txt

COPY . .
