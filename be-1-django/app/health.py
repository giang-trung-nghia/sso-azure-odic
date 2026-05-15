from django.http import JsonResponse


def health(_request):
    return JsonResponse(
        {
            "status": "ok",
            "service": "be-1-django",
        }
    )
