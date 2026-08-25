"""Mini-Repo fuer die Oberflaechen-Checks: vier Routen, drei Wege, ein Waisenkind."""

from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import include, path


def leer(_request):
    return HttpResponse("")


def nach_danke(_request):
    # Der einzige Weg zu 'danke' — eine Weiterleitung, kein Link.
    return redirect("danke")


unter = [
    path("liste/", leer, name="liste"),
    path("liste/zeile/", leer, name="liste_row"),  # Fragment, per Muster ausgenommen
]

urlpatterns = [
    path("", leer, name="start"),
    path("danke/", leer, name="danke"),
    path("senden/", nach_danke, name="senden"),
    path("verwaist/", leer, name="verwaist"),
    path("angebote/", include((unter, "angebote"), namespace="angebote")),
]
