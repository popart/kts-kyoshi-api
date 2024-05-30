# Use an official Python runtime as a parent image
FROM python:3.12.3-bookworm

# Set the working directory in the container
WORKDIR /app

# Install poetry
RUN apt update
RUN apt install pipx -y
RUN pipx install poetry
ENV PATH=/root/.local/bin:$PATH

# Copy the current directory contents into the container at /app
COPY ./pyproject.toml /app
COPY ./poetry.lock /app
RUN poetry install

# Copy code last to save on caching
COPY ./src /app

# Make port 5555 available to the world outside this container
EXPOSE 5555

# Run app.py when the container launches
CMD ["poetry", "run", "python", "app.py"]
