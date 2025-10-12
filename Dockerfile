# syntax=docker/dockerfile:1
FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install netcat for database connection checking
RUN apt-get update && apt-get install -y netcat-traditional && rm -rf /var/lib/apt/lists/*

WORKDIR /code

COPY requirements.txt /code/
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy entrypoint script first and make it executable
COPY entrypoint.sh /code/entrypoint.sh
RUN chmod +x /code/entrypoint.sh

COPY . /code/

ENTRYPOINT ["bash", "/code/entrypoint.sh"]
CMD ["gunicorn", "main.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4"]
