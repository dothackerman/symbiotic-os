FROM mcr.microsoft.com/devcontainers/python:3.12-bookworm

# No root at runtime
USER vscode

WORKDIR /workspace

# Install only what is needed for symbiotic-os builds
RUN pip install --user pytest python-dotenv

# No network access enforced at container run time via --network=none
# This Dockerfile intentionally installs nothing that requires outbound calls at build time
# beyond the base image pip packages above.
