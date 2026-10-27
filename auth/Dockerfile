# Build context is the repo root (see docker-compose.yml) so the shared library can be copied in.
FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /srv
# Install the shared library from the repo first. requirements.txt pins ca-auth-lib==0.1.0
# exactly; the already-installed copy satisfies the pin, and if lib/ca_auth_lib/pyproject.toml
# is bumped without updating the pin, the next install fails loudly instead of drifting.
COPY lib/ca_auth_lib /tmp/ca_auth_lib
RUN pip install --no-cache-dir /tmp/ca_auth_lib && rm -rf /tmp/ca_auth_lib
COPY auth/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY auth/ .
EXPOSE 8000
CMD ["sh", "-c", "python manage.py migrate --noinput && python manage.py runserver 0.0.0.0:8000"]
