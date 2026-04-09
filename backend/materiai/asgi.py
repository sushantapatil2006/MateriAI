"""
ASGI config for MateriAI project.
"""
import os
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "materiai.settings")
application = get_asgi_application()
