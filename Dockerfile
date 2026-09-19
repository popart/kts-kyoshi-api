# Use an official Python runtime as a parent image
FROM python:3.14-slim-trixie

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set the working directory in the container
WORKDIR /app

# Copy dependency files first to leverage layer caching
COPY ./pyproject.toml ./uv.lock /app/

# Install dependencies (no dev group, no project itself)
RUN uv sync --frozen --no-dev --no-install-project

# Copy code last to save on caching
COPY ./src /app

# Make port 5555 available to the world outside this container
EXPOSE 5555

# Run app.py when the container launches
CMD ["uv", "run", "--no-sync", "python", "app.py"]
