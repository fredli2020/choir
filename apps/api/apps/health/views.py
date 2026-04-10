from django.db import connections
from rest_framework.decorators import api_view
from rest_framework.response import Response


@api_view(["GET"])
def live(request):
    return Response({"status": "ok"})


@api_view(["GET"])
def ready(request):
    database_ok = True

    try:
        with connections["default"].cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except Exception:
        database_ok = False

    status = "ok" if database_ok else "error"
    http_status = 200 if database_ok else 503
    return Response({"status": status, "database": database_ok}, status=http_status)
