"""A request nested past Python's recursion limit is a 500 from DRF, not a 400.

Runs without a database or a server: Django's test client sends each request
through the full request handler, the way a production server would.
"""
import django
from django.conf import settings

settings.configure(
    DEBUG=False,
    ALLOWED_HOSTS=["testserver"],
    ROOT_URLCONF=__name__,
    SECRET_KEY="reproduction-only",
    INSTALLED_APPS=[
        "django.contrib.auth",
        "django.contrib.contenttypes",
        "rest_framework",
    ],
)
django.setup()

from django.test import Client  # noqa: E402
from django.urls import path  # noqa: E402
from rest_framework import serializers  # noqa: E402
from rest_framework.response import Response  # noqa: E402
from rest_framework.views import APIView  # noqa: E402


class ConfigSerializer(serializers.Serializer):
    config = serializers.JSONField()


class ConfigView(APIView):
    def post(self, request):
        serializer = ConfigSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data)


urlpatterns = [path("config/", ConfigView.as_view())]

# Deep enough for any interpreter: 3.13 stops near 10,000 levels, and 3.14 at
# whatever the thread's stack allows.
DEPTH = 200_000
NESTED = "[" * DEPTH + "]" * DEPTH


def show(label, response):
    if response.status_code == 500:
        detail = repr(response.exc_info[1])
    else:
        detail = response.content.decode()
    print(f"{label}: {response.status_code} {detail}")


client = Client(raise_request_exception=False)
show(
    "malformed JSON body ",
    client.post("/config/", '{"config": [}', content_type="application/json"),
)
show(
    "nested JSON body    ",
    client.post(
        "/config/", '{"config": ' + NESTED + "}", content_type="application/json"
    ),
)
# Django's test client sends a dict as multipart/form-data, so JSONField decodes
# the field's string itself.
show("nested form field   ", client.post("/config/", {"config": NESTED}))
