"""
Tests for iil_testkit.contract.verifier — ADR-155 Contract Testing.

Covers all 5 verifier types and all review fixes (B1-B4, K1, K3, M3).
"""
from __future__ import annotations

import inspect
from typing import Any

import pytest

from iil_testkit.contract import (
    BaseContractVerifier,
    CallableContractVerifier,
    ContractVerifier,
    ResponseShapeVerifier,
    TaskContractVerifier,
)


# ── Test Fixtures: Provider-Klassen ──────────────────────────────────────────


class DummyService:
    """Fake Service-Klasse für Tests."""

    def __init__(self, router: object, *, timeout: int = 30) -> None:
        self._router = router
        self._timeout = timeout

    def process(self, document: str, *, format: str = "pdf") -> dict[str, Any]:
        """Verarbeitet ein Dokument.

        Returns:
            Dict mit Keys: content, pages, metadata

        :raises ValueError: Wenn document leer ist.
        :raises FileNotFoundError: Wenn Datei nicht gefunden.
        """
        return {"content": "", "pages": 0, "metadata": {}}

    def analyze(self, text: str) -> list[str]:
        """Analysiert Text."""
        return []


class DummyServiceNoDoc:
    """Service ohne Exception-Doku."""

    def validate(self, data: str) -> bool:
        return True


def free_function(text: str, *, quality: str = "standard") -> dict[str, Any]:
    """Eine freistehende Funktion."""
    return {"result": text}


def free_function_no_annotation(text):
    return text


# ── Fake Celery Task ─────────────────────────────────────────────────────────


class FakeCeleryTask:
    """Simuliert einen Celery Task mit .run-Methode."""
    name = "app.tasks.fake_task"
    acks_late = True

    def run(self, document_id: int, *, force: bool = False) -> str:
        return "done"

    def delay(self, *args: Any, **kwargs: Any) -> None:
        pass


class FakeCeleryTaskNoAcksLate:
    name = "app.tasks.no_acks"

    def run(self, item_id: int) -> None:
        pass


# ══════════════════════════════════════════════════════════════════════════════
# Tests: ContractVerifier (Klassen)
# ══════════════════════════════════════════════════════════════════════════════


class TestContractVerifierInit:
    def test_should_reject_non_class(self) -> None:
        with pytest.raises(TypeError, match="erwartet eine Klasse"):
            ContractVerifier(free_function)  # type: ignore[arg-type]

    def test_should_accept_class(self) -> None:
        verifier = ContractVerifier(DummyService)
        assert verifier._name == "DummyService"


class TestContractVerifierInitParams:
    def test_should_pass_with_correct_params(self) -> None:
        verifier = ContractVerifier(DummyService)
        verifier.assert_init_params(["router"])

    def test_should_pass_with_optional_params(self) -> None:
        verifier = ContractVerifier(DummyService)
        verifier.assert_init_params(["router", "timeout"])

    def test_should_fail_with_wrong_param(self) -> None:
        verifier = ContractVerifier(DummyService)
        with pytest.raises(AssertionError, match="nicht existieren"):
            verifier.assert_init_params(["llm_router"])

    def test_should_detect_new_required_params_exhaustive(self) -> None:
        """Fix K1: exhaustive mode prüft beide Richtungen."""
        verifier = ContractVerifier(DummyService)
        # Consumer kennt nur 'timeout', aber 'router' ist auch required
        with pytest.raises(AssertionError, match="neue Required-Parameter"):
            verifier.assert_init_params(["timeout"], exhaustive=True)

    def test_should_pass_exhaustive_with_all_required(self) -> None:
        verifier = ContractVerifier(DummyService)
        verifier.assert_init_params(["router", "timeout"], exhaustive=True)


class TestContractVerifierMethodParams:
    def test_should_pass_with_correct_params(self) -> None:
        verifier = ContractVerifier(DummyService)
        verifier.assert_method_params("process", ["document"])

    def test_should_fail_with_wrong_param(self) -> None:
        verifier = ContractVerifier(DummyService)
        with pytest.raises(AssertionError, match="nicht existieren"):
            verifier.assert_method_params("process", ["doc_path"])


class TestContractVerifierMethodExists:
    def test_should_pass_for_existing_method(self) -> None:
        verifier = ContractVerifier(DummyService)
        verifier.assert_method_exists("process")

    def test_should_fail_for_missing_method(self) -> None:
        verifier = ContractVerifier(DummyService)
        with pytest.raises(AssertionError, match="nicht gefunden"):
            verifier.assert_method_exists("nonexistent_method")


class TestContractVerifierNoParam:
    def test_should_pass_when_param_absent(self) -> None:
        verifier = ContractVerifier(DummyService)
        verifier.assert_no_param("process", "doc_path")

    def test_should_fail_when_param_exists(self) -> None:
        verifier = ContractVerifier(DummyService)
        with pytest.raises(AssertionError, match="sollte nicht existieren"):
            verifier.assert_no_param("process", "document")

    def test_should_accept_method_object(self) -> None:
        verifier = ContractVerifier(DummyService)
        verifier.assert_no_param(DummyService.process, "doc_path")

    def test_should_accept_method_string(self) -> None:
        verifier = ContractVerifier(DummyService)
        verifier.assert_no_param("process", "doc_path")


class TestContractVerifierEnumValues:
    def test_should_pass_with_subset(self) -> None:
        verifier = ContractVerifier(DummyService)
        verifier.assert_enum_values({"a", "b", "c"}, ["a", "b"])

    def test_should_fail_with_missing_values(self) -> None:
        verifier = ContractVerifier(DummyService)
        with pytest.raises(AssertionError, match="Fehlende Werte"):
            verifier.assert_enum_values({"a", "b"}, ["a", "c"])

    def test_should_pass_not_enum_value(self) -> None:
        verifier = ContractVerifier(DummyService)
        verifier.assert_not_enum_value({"a", "b"}, "c")

    def test_should_fail_not_enum_value_present(self) -> None:
        verifier = ContractVerifier(DummyService)
        with pytest.raises(AssertionError, match="existiert in Registry"):
            verifier.assert_not_enum_value({"a", "b"}, "a")


# ══════════════════════════════════════════════════════════════════════════════
# Tests: Exception-Contracts (Fix B2)
# ══════════════════════════════════════════════════════════════════════════════


class TestContractVerifierAssertRaises:
    def test_should_pass_with_documented_exception(self) -> None:
        """Fix B2: assert statt warnings.warn — CI-Gate funktioniert."""
        verifier = ContractVerifier(DummyService)
        verifier.assert_raises("process", [ValueError, FileNotFoundError])

    def test_should_fail_with_undocumented_exception(self) -> None:
        """Fix B2: Muss fehlschlagen wenn Exception nicht im Docstring."""
        verifier = ContractVerifier(DummyServiceNoDoc)
        with pytest.raises(AssertionError, match="nicht im Docstring"):
            verifier.assert_raises("validate", [ValueError])

    def test_should_reject_non_exception_class(self) -> None:
        verifier = ContractVerifier(DummyService)
        with pytest.raises(AssertionError, match="keine Exception-Klasse"):
            verifier.assert_raises("process", [str])  # type: ignore[list-item]


# ══════════════════════════════════════════════════════════════════════════════
# Tests: Return-Shape-Contracts (Fix B1, B3)
# ══════════════════════════════════════════════════════════════════════════════


class TestContractVerifierReturnAnnotation:
    def test_should_pass_with_correct_generic_type(self) -> None:
        """Fix B1: dict[str, Any] == dict[str, Any] ohne __origin__ Short-Circuit."""
        verifier = ContractVerifier(DummyService)
        verifier.assert_return_annotation("process", dict[str, Any])

    def test_should_fail_with_wrong_type(self) -> None:
        """Fix B1: list ≠ dict[str, Any]."""
        verifier = ContractVerifier(DummyService)
        with pytest.raises(AssertionError, match="Return-Typ"):
            verifier.assert_return_annotation("process", list)

    def test_should_check_return_origin(self) -> None:
        verifier = ContractVerifier(DummyService)
        verifier.assert_return_origin("process", dict)

    def test_should_fail_wrong_origin(self) -> None:
        verifier = ContractVerifier(DummyService)
        with pytest.raises(AssertionError, match="Generic-Origin"):
            verifier.assert_return_origin("process", list)


class TestContractVerifierReturnKeys:
    def test_should_pass_with_documented_keys(self) -> None:
        """Fix B3: assert statt warnings.warn."""
        verifier = ContractVerifier(DummyService)
        verifier.assert_return_keys("process", ["content", "pages", "metadata"])

    def test_should_fail_with_undocumented_key(self) -> None:
        """Fix B3: Muss fehlschlagen wenn Key nicht im Docstring."""
        verifier = ContractVerifier(DummyService)
        with pytest.raises(AssertionError, match="Return-Keys nicht im Docstring"):
            verifier.assert_return_keys("process", ["content", "unknown_key"])


# ══════════════════════════════════════════════════════════════════════════════
# Tests: CallableContractVerifier
# ══════════════════════════════════════════════════════════════════════════════


class TestCallableContractVerifier:
    def test_should_create_via_factory(self) -> None:
        verifier = ContractVerifier.for_callable(free_function)
        assert isinstance(verifier, CallableContractVerifier)

    def test_should_pass_with_correct_params(self) -> None:
        verifier = ContractVerifier.for_callable(free_function)
        verifier.assert_params(["text"])

    def test_should_fail_with_wrong_param(self) -> None:
        verifier = ContractVerifier.for_callable(free_function)
        with pytest.raises(AssertionError, match="Fehlende Parameter"):
            verifier.assert_params(["content"])

    def test_should_pass_no_param(self) -> None:
        verifier = ContractVerifier.for_callable(free_function)
        verifier.assert_no_param("content")

    def test_should_fail_no_param_when_exists(self) -> None:
        verifier = ContractVerifier.for_callable(free_function)
        with pytest.raises(AssertionError, match="sollte nicht existieren"):
            verifier.assert_no_param("text")

    def test_should_check_return_annotation(self) -> None:
        verifier = ContractVerifier.for_callable(free_function)
        verifier.assert_return_annotation(dict[str, Any])

    def test_should_reject_non_callable(self) -> None:
        with pytest.raises(TypeError, match="erwartet ein callable"):
            CallableContractVerifier("not_a_function")  # type: ignore[arg-type]


# ══════════════════════════════════════════════════════════════════════════════
# Tests: TaskContractVerifier (Fix B4)
# ══════════════════════════════════════════════════════════════════════════════


class TestTaskContractVerifier:
    def test_should_create_via_factory(self) -> None:
        verifier = ContractVerifier.for_task(FakeCeleryTask())
        assert isinstance(verifier, TaskContractVerifier)

    def test_should_resolve_run_method(self) -> None:
        """Fix B4: Korrekte Auflösung über type(task).run."""
        task = FakeCeleryTask()
        verifier = ContractVerifier.for_task(task)
        verifier.assert_params(["document_id"])

    def test_should_fail_with_wrong_param(self) -> None:
        task = FakeCeleryTask()
        verifier = ContractVerifier.for_task(task)
        with pytest.raises(AssertionError, match="Fehlende Parameter"):
            verifier.assert_params(["doc_id"])

    def test_should_pass_no_param(self) -> None:
        task = FakeCeleryTask()
        verifier = ContractVerifier.for_task(task)
        verifier.assert_no_param("doc_id")

    def test_should_fail_no_param_when_exists(self) -> None:
        task = FakeCeleryTask()
        verifier = ContractVerifier.for_task(task)
        with pytest.raises(AssertionError, match="sollte nicht existieren"):
            verifier.assert_no_param("document_id")

    def test_should_check_acks_late(self) -> None:
        task = FakeCeleryTask()
        verifier = ContractVerifier.for_task(task)
        verifier.assert_is_acks_late()

    def test_should_fail_acks_late_not_set(self) -> None:
        task = FakeCeleryTaskNoAcksLate()
        verifier = ContractVerifier.for_task(task)
        with pytest.raises(AssertionError, match="acks_late"):
            verifier.assert_is_acks_late()

    def test_should_resolve_plain_function(self) -> None:
        """Fix B4: Direkte Funktion (kein Celery-Setup) als Task."""
        verifier = ContractVerifier.for_task(free_function)
        verifier.assert_params(["text"])

    def test_should_reject_non_callable(self) -> None:
        """Fix B4: TypeError statt inspect.signature-Crash."""
        with pytest.raises(TypeError, match="Kann Task-Funktion nicht auflösen"):
            ContractVerifier.for_task(42)


# ══════════════════════════════════════════════════════════════════════════════
# Tests: ResponseShapeVerifier (Fix K3)
# ══════════════════════════════════════════════════════════════════════════════


class TestResponseShapeVerifier:
    def test_should_pass_with_matching_shape(self) -> None:
        verifier = ResponseShapeVerifier({"name": str, "score": float})
        verifier.assert_response({"name": "test", "score": 0.95, "extra": True})

    def test_should_fail_with_missing_keys(self) -> None:
        verifier = ResponseShapeVerifier({"name": str, "score": float})
        with pytest.raises(AssertionError, match="Fehlende Keys"):
            verifier.assert_response({"name": "test"})

    def test_should_pass_type_check(self) -> None:
        verifier = ResponseShapeVerifier({"name": str, "score": float})
        verifier.assert_response_types({"name": "test", "score": 0.95})

    def test_should_fail_type_mismatch(self) -> None:
        verifier = ResponseShapeVerifier({"name": str, "score": float})
        with pytest.raises(AssertionError, match="Response-Type-Mismatch"):
            verifier.assert_response_types({"name": "test", "score": "not_a_float"})

    def test_should_check_status_code(self) -> None:
        class FakeResponse:
            status_code = 200

        verifier = ResponseShapeVerifier({})
        verifier.assert_status_code(FakeResponse(), 200)

    def test_should_fail_wrong_status_code(self) -> None:
        class FakeResponse:
            status_code = 404

        verifier = ResponseShapeVerifier({})
        with pytest.raises(AssertionError, match="HTTP Status 404"):
            verifier.assert_status_code(FakeResponse(), 200)


# ══════════════════════════════════════════════════════════════════════════════
# Tests: BaseContractVerifier Protocol (Fix M3)
# ══════════════════════════════════════════════════════════════════════════════


class TestBaseContractVerifierProtocol:
    def test_should_be_abc(self) -> None:
        """Fix M3: Alle Verifier erben von BaseContractVerifier."""
        assert issubclass(ContractVerifier, BaseContractVerifier)
        assert issubclass(CallableContractVerifier, BaseContractVerifier)
        assert issubclass(TaskContractVerifier, BaseContractVerifier)

    def test_should_have_assert_params(self) -> None:
        assert hasattr(BaseContractVerifier, "assert_params")
        assert hasattr(BaseContractVerifier, "assert_no_param")

    def test_should_not_instantiate_directly(self) -> None:
        with pytest.raises(TypeError):
            BaseContractVerifier()  # type: ignore[abstract]
