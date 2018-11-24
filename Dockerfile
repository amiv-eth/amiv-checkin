FROM python:3.7-alpine

# Create user with home directory and no password and change workdir
RUN adduser -Dh /checkin checkin
WORKDIR /checkin
# API will run on port 80
EXPOSE 8080

# Install bjoern and dependencies for install (we need to keep libev)
RUN apk add --no-cache --virtual .deps \
        musl-dev python-dev gcc git && \
    apk add --no-cache libev-dev && \
    apk add --no-cache libffi-dev libressl-dev && \
    pip install bjoern

# Copy files to /api directory, install requirements
COPY ./ /checkin
RUN pip install -r /checkin/requirements.txt

# Cleanup dependencies
RUN apk del .deps

# Update permissions for entrypoint
RUN chmod 755 entrypoint.sh

# Switch user
USER checkin

# Start application
CMD [ "./entrypoint.sh" ]
