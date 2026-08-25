# iil_testkit/oberflaeche.py — platform#2326, KONZ-platform-051
"""Was ein gruener Routen-Test nicht sieht: ob ein Mensch hinkommt, und was er liest.

Zwei Befundklassen aus ausschreibungs-hub (2026-08-24/25), beide erst im Browser
gefunden, beide fuer jeden Django-Hub gueltig:

1. **Verwaiste Screens.** Ein Routen-Test ruft ``reverse()`` und prueft einen
   Statuscode. Ob irgendein Template dorthin verlinkt, ist ihm keine Frage wert.
   Beim ersten Test ueber ALLE Routen waren es 14 verwaiste Screens, nicht die
   zwei, die der Browser gezeigt hatte — darunter Station 4 und 5 einer Kette.
2. **Mehrzeilige ``{# … #}``.** Djangos Hash-Kommentar ist einzeilig; ueber einen
   Zeilenumbruch hinweg landet er WOERTLICH auf der Seite. In ``base.html`` heisst
   das: auf jeder Seite.

Gegenueber der Erstfassung in ausschreibungs-hub sind drei Dinge anders:

* Template-Verzeichnisse kommen aus ``settings.TEMPLATES[*]['DIRS']`` und
  ``get_app_template_dirs('templates')`` statt aus einem festen ``apps/``-Pfad —
  risk-hub liegt unter ``src/``, billing-hub hat nur ``templates/``. Verzeichnisse
  ausserhalb ``BASE_DIR`` (site-packages, ``django.contrib.admin``) fallen weg.
* Jede Datei wird einmal gelesen, nicht einmal je parametrisiertem Testfall.
* Weiterleitungen zaehlen als zweite Quelle: eine Route, die nur ueber
  ``redirect('name')``/``reverse('name')`` in einer View erreicht wird (Erfolgsseite
  nach POST), ist begehbar — aber sie steht getrennt im Befund, damit niemand
  ``reverse()`` in einem Test als Link verbucht (Tests, Migrationen und
  Management-Commands werden nicht durchsucht).

Die Rechenkerne (``verwaiste_routen``, ``mehrzeilige_kommentare``) sind reine
Funktionen ohne Django — die Positivkontrolle laeuft ueber sie, nicht ueber
Routennamen eines bestimmten Repos.

Usage (im Repo — ``tests/test_oberflaeche.py``)::

    import pytest
    from iil_testkit.oberflaeche import (
        erreichbarkeit, mehrzeilige_kommentare, template_dateien,
    )

    OHNE_LINK_ERLAUBT = {
        "login": "Einstiegspunkt — LOGIN_URL, nicht verlinkt.",
        "stripe_webhook": "Wird von Stripe aufgerufen.",
    }

    BEFUND = erreichbarkeit(erlaubt=OHNE_LINK_ERLAUBT)

    def test_should_find_routes_and_links_at_all():
        # Gegenprobe gegen die eigene Null: Schwellen sind Sache des Repos.
        assert len(BEFUND.routen) > 30
        assert len(BEFUND.verlinkt) > 15

    @pytest.mark.parametrize("route", BEFUND.zu_pruefen, ids=str)
    def test_should_be_reachable_from_a_template(route):
        if route in OHNE_LINK_ERLAUBT:
            pytest.skip(OHNE_LINK_ERLAUBT[route])
        assert route not in BEFUND.verwaist, BEFUND.begruendung(route)

    @pytest.mark.parametrize("pfad", template_dateien(), ids=lambda p: p.name)
    def test_should_not_use_multiline_hash_comment(pfad):
        assert not mehrzeilige_kommentare(pfad.read_text(encoding="utf-8", errors="ignore"))

``SKIP`` ist auch hier kein ``PASS``: eine Route in ``OHNE_LINK_ERLAUBT`` ist eine
Entscheidung mit Grund, kein stilles Weglassen.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from pathlib import Path

__all__ = [
    "KEINE_SEITE",
    "MEHRZEILIG",
    "Erreichbarkeit",
    "erreichbarkeit",
    "mehrzeilige_kommentare",
    "python_dateien",
    "routen_namen",
    "template_dateien",
    "verlinkte_namen",
    "verwaiste_routen",
    "weitergeleitete_namen",
]

#: Routennamen, die keine ganze Seite rendern und deshalb nicht verlinkt sein muessen.
#: Repos erweitern das ueber ``erreichbarkeit(muster=...)``, nicht durch Kopie.
KEINE_SEITE = re.compile(
    r"(^admin:|^api:|^oidc|healthz|livez|schema|swagger|redoc|"
    r"password_reset|password_change|_partial$|-partial$|_row$|_status$|-status$|_rerun$|-rerun$)",
    re.I,
)

#: ``{#`` … ``#}`` ueber mindestens einen Zeilenumbruch hinweg.
MEHRZEILIG = re.compile(r"\{#((?:[^#]|#(?!\}))*\n(?:[^#]|#(?!\}))*)#\}")

_URL_TAG = re.compile(r"{%\s*url\s+['\"]([^'\"]+)['\"]")
_PY_ZIEL = re.compile(r"\b(?:reverse|reverse_lazy|redirect)\(\s*['\"]([A-Za-z0-9_:.\-]+)['\"]")

#: Verzeichnisnamen, in denen ``reverse()`` kein Beleg fuer Erreichbarkeit ist.
_KEIN_WEG = frozenset(
    {
        "tests",
        "test",
        "migrations",
        "management",
        ".venv",
        "venv",
        "node_modules",
        "staticfiles",
        "static",
    }
)


# --------------------------------------------------------------------------- #
# Reine Rechenkerne — ohne Django, damit die Positivkontrolle nicht am Repo haengt
# --------------------------------------------------------------------------- #


def verwaiste_routen(
    routen: Iterable[str],
    verlinkt: Iterable[str],
    *,
    weitergeleitet: Iterable[str] = (),
    erlaubt: Mapping[str, str] | None = None,
    muster: re.Pattern[str] = KEINE_SEITE,
) -> list[str]:
    """Seitenrendernde Routen, die weder verlinkt noch weitergeleitet noch erlaubt sind."""
    weg = set(verlinkt) | set(weitergeleitet)
    frei = set(erlaubt or {})
    return sorted(r for r in set(routen) if not muster.search(r) and r not in weg and r not in frei)


def mehrzeilige_kommentare(text: str) -> list[str]:
    """Alle ``{# … #}``, die einen Zeilenumbruch enthalten — Django gibt sie woertlich aus."""
    return MEHRZEILIG.findall(text)


# --------------------------------------------------------------------------- #
# Django-Seite: Routen, Templates, Python-Quellen des Repos
# --------------------------------------------------------------------------- #


def routen_namen(resolver=None) -> list[str]:
    """Alle benannten Routen, namespace-qualifiziert (``app:name``)."""
    if resolver is None:
        from django.urls import get_resolver

        resolver = get_resolver()

    def sammle(res, prefix: str = "") -> list[str]:
        aus: list[str] = []
        for muster in res.url_patterns:
            if hasattr(muster, "url_patterns"):
                unter = prefix + (f"{muster.namespace}:" if muster.namespace else "")
                aus += sammle(muster, unter)
            elif muster.name:
                aus.append(prefix + muster.name)
        return aus

    return sorted(set(sammle(resolver)))


def _basis() -> Path:
    from django.conf import settings

    return Path(settings.BASE_DIR).resolve()


def _innerhalb(pfad: Path, basis: Path) -> bool:
    pfad = pfad.resolve()
    return pfad == basis or basis in pfad.parents


def template_dateien(extra: Iterable[Path] = ()) -> list[Path]:
    """Alle ``*.html`` aus ``TEMPLATES[*]['DIRS']`` und App-Template-Ordnern in ``BASE_DIR``.

    Was ausserhalb liegt (site-packages, ``django.contrib.*``), gehoert nicht dem
    Repo und wird nicht bewertet.
    """
    from django.conf import settings
    from django.template.utils import get_app_template_dirs

    basis = _basis()
    ordner: set[Path] = set()
    for konf in getattr(settings, "TEMPLATES", []):
        ordner.update(Path(d) for d in konf.get("DIRS", []))
    ordner.update(Path(d) for d in get_app_template_dirs("templates"))
    ordner.update(Path(d) for d in extra)
    dateien = {
        p
        for d in ordner
        if _innerhalb(d, basis)
        for p in d.rglob("*.html")
        if not _in_kein_weg(p, basis)
    }
    return sorted(dateien)


def _in_kein_weg(pfad: Path, basis: Path) -> bool:
    try:
        teile = pfad.resolve().relative_to(basis).parts
    except ValueError:
        return True
    return any(t in _KEIN_WEG for t in teile[:-1])


def python_dateien() -> list[Path]:
    """``*.py`` des Repos ohne Tests, Migrationen, Management-Commands und Umgebungen."""
    basis = _basis()
    return sorted(p for p in basis.rglob("*.py") if not _in_kein_weg(p, basis))


def verlinkte_namen(dateien: Iterable[Path]) -> set[str]:
    """Routennamen, auf die ein Template per ``{% url %}`` zeigt — jede Datei einmal gelesen."""
    namen: set[str] = set()
    for p in dateien:
        namen.update(_URL_TAG.findall(p.read_text(encoding="utf-8", errors="ignore")))
    return namen


def weitergeleitete_namen(dateien: Iterable[Path]) -> set[str]:
    """Routennamen, die eine View per ``redirect``/``reverse``/``reverse_lazy`` ansteuert."""
    namen: set[str] = set()
    for p in dateien:
        namen.update(_PY_ZIEL.findall(p.read_text(encoding="utf-8", errors="ignore")))
    return namen


@dataclass(frozen=True)
class Erreichbarkeit:
    """Ergebnis eines Laufs — die drei Quellen getrennt, damit der Befund lesbar bleibt."""

    routen: tuple[str, ...]
    verlinkt: frozenset[str]
    weitergeleitet: frozenset[str]
    verwaist: tuple[str, ...]
    erlaubt: Mapping[str, str] = field(default_factory=dict)
    muster: re.Pattern[str] = KEINE_SEITE

    @property
    def zu_pruefen(self) -> list[str]:
        """Seitenrendernde Routen — die Menge, ueber die ein Repo parametrisiert."""
        return [r for r in self.routen if not self.muster.search(r)]

    @property
    def nur_per_weiterleitung(self) -> list[str]:
        """Begehbar, aber aus keinem Template verlinkt — lesenswert, kein Fehler."""
        return sorted(
            r for r in self.zu_pruefen if r in self.weitergeleitet and r not in self.verlinkt
        )

    def begruendung(self, route: str) -> str:
        return (
            f"Route {route!r} rendert eine Seite, wird aber aus keinem Template verlinkt und von "
            f"keiner View angesteuert — erreichbar nur ueber die getippte URL. Entweder verlinken, "
            f"oder mit Begruendung in OHNE_LINK_ERLAUBT eintragen."
        )


def erreichbarkeit(
    *,
    erlaubt: Mapping[str, str] | None = None,
    muster: re.Pattern[str] = KEINE_SEITE,
    weiterleitungen: bool = True,
    templates: Iterable[Path] | None = None,
) -> Erreichbarkeit:
    """Ein Lauf ueber Routen, Templates und (optional) Python-Quellen des Repos."""
    routen = routen_namen()
    dateien = list(templates) if templates is not None else template_dateien()
    verlinkt = verlinkte_namen(dateien)
    weiter = weitergeleitete_namen(python_dateien()) if weiterleitungen else set()
    verwaist = verwaiste_routen(
        routen, verlinkt, weitergeleitet=weiter, erlaubt=erlaubt, muster=muster
    )
    return Erreichbarkeit(
        routen=tuple(routen),
        verlinkt=frozenset(verlinkt),
        weitergeleitet=frozenset(weiter),
        verwaist=tuple(verwaist),
        erlaubt=dict(erlaubt or {}),
        muster=muster,
    )
