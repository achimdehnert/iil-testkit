"""Oberflaechen-Checks — Positivkontrolle ueber reine Funktionen und ein Mini-Repo.

Der Mini-Repo unter ``tests/oberflaeche_fixture/`` hat genau einen verwaisten
Screen (``verwaist``), einen nur per Weiterleitung erreichbaren (``danke``), ein
Fragment (``angebote:liste_row``) und ein ``reverse()`` in einem ``tests/``-Ordner,
das NICHT als Weg zaehlen darf.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from iil_testkit.oberflaeche import (
    KEINE_SEITE,
    erreichbarkeit,
    mehrzeilige_kommentare,
    python_dateien,
    routen_namen,
    template_dateien,
    verlinkte_namen,
    verwaiste_routen,
    weitergeleitete_namen,
)

FIXTURE = Path(__file__).parent / "oberflaeche_fixture"


# --------------------------------------------------------------------------- #
# Reine Kerne — kein Django noetig
# --------------------------------------------------------------------------- #


def test_should_report_only_unlinked_page_routes():
    verwaist = verwaiste_routen(
        ["start", "danke", "verwaist", "angebote:liste_row", "admin:index"],
        verlinkt={"start"},
        weitergeleitet={"danke"},
    )
    assert verwaist == ["verwaist"]


def test_should_treat_allowed_routes_as_a_decision_not_a_gap():
    verwaist = verwaiste_routen(
        ["verwaist"], verlinkt=set(), erlaubt={"verwaist": "Landing, wird direkt angesteuert."}
    )
    assert verwaist == []


def test_should_skip_fragment_patterns_by_default():
    assert KEINE_SEITE.search("angebote:liste_row")
    assert KEINE_SEITE.search("api:foo")
    assert not KEINE_SEITE.search("angebote:liste")


def test_should_detect_a_multiline_comment_when_one_exists():
    assert mehrzeilige_kommentare("{# eine\n zweite Zeile #}")
    assert not mehrzeilige_kommentare("{# alles in einer Zeile #}")
    assert not mehrzeilige_kommentare("{% comment %} eine\n zweite Zeile {% endcomment %}")


# --------------------------------------------------------------------------- #
# Django-Seite gegen den Mini-Repo
# --------------------------------------------------------------------------- #


@pytest.fixture
def mini_repo(settings):
    settings.BASE_DIR = FIXTURE
    settings.ROOT_URLCONF = "tests.oberflaeche_fixture.urls"
    settings.TEMPLATES = [
        {
            "BACKEND": "django.template.backends.django.DjangoTemplates",
            "DIRS": [FIXTURE / "templates"],
            "APP_DIRS": True,
        }
    ]
    from django.urls import clear_url_caches

    clear_url_caches()
    yield
    clear_url_caches()


def test_should_collect_namespaced_route_names(mini_repo):
    assert routen_namen() == [
        "angebote:liste",
        "angebote:liste_row",
        "danke",
        "senden",
        "start",
        "verwaist",
    ]


def test_should_only_read_templates_inside_base_dir(mini_repo):
    dateien = template_dateien()
    assert [p.name for p in dateien] == ["basis.html"]
    # django.contrib.* liegt in site-packages und gehoert nicht dem Repo.
    assert all(FIXTURE in p.resolve().parents for p in dateien)


def test_should_read_links_from_both_quote_styles(mini_repo):
    assert verlinkte_namen(template_dateien()) == {"start", "angebote:liste", "senden"}


def test_should_not_count_reverse_in_tests_as_a_way(mini_repo):
    dateien = python_dateien()
    assert all("tests" not in p.relative_to(FIXTURE).parts[:-1] for p in dateien)
    assert weitergeleitete_namen(dateien) == {"danke"}


def test_should_find_exactly_the_orphan_in_the_mini_repo(mini_repo):
    befund = erreichbarkeit()
    assert befund.verwaist == ("verwaist",)
    assert befund.nur_per_weiterleitung == ["danke"]
    assert "angebote:liste_row" not in befund.zu_pruefen
    assert "verwaist" in befund.begruendung("verwaist")


def test_should_let_a_reason_take_the_orphan_off_the_list(mini_repo):
    befund = erreichbarkeit(erlaubt={"verwaist": "Direkte Landing-URL."})
    assert befund.verwaist == ()


def test_should_count_the_orphan_when_redirects_are_ignored(mini_repo):
    befund = erreichbarkeit(weiterleitungen=False)
    assert befund.verwaist == ("danke", "verwaist")
