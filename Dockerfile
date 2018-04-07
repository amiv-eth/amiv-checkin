FROM python:3.6-alpine

# Create user with home directory and no password and change workdir
RUN adduser -Dh /checkin checkin
WORKDIR /checkin
# API will run on port 80
EXPOSE 8080
# Environment variable for config, use path for docker secrets as default
#ENV AMIVAPI_CONFIG=/run/secrets/amivapi_config

# Install bjoern and dependencies for install (we need to keep libev)
RUN apk add --no-cache --virtual .deps \
        musl-dev python-dev gcc git && \
    apk add --no-cache libev-dev && \
    pip install bjoern

# Copy files to /api directory, install requirements
COPY ./ /checkin
RUN pip install -r /checkin/requirements.txt

# Cleanup dependencies
RUN apk del .deps

# Switch user
USER checkin

# Start bjoern
CMD ["python3", "run_docker.py"]

