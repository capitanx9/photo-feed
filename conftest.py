import os

os.environ.setdefault("DJANGO_SECRET_KEY", "test-secret")
os.environ.setdefault("DJANGO_DEBUG", "1")
os.environ.setdefault("ALLOWED_HOSTS", "testserver")
os.environ.setdefault("POSTGRES_DB", "api")
os.environ.setdefault("POSTGRES_USER", "api")
os.environ.setdefault("POSTGRES_PASSWORD", "api")
os.environ.setdefault("POSTGRES_HOST", "localhost")
os.environ.setdefault("POSTGRES_PORT", "5432")
