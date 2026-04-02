"""
iil_testkit/contract — Contract Testing für das iil-Platform-Ökosystem.

Fix H4: Package-Struktur mit expliziten Exports.

Öffentliche API:
    from iil_testkit.contract import (
        ContractVerifier,
        CallableContractVerifier,
        TaskContractVerifier,
        ResponseShapeVerifier,
        BaseContractVerifier,
    )

ADR: ADR-155
"""
from iil_testkit.contract.verifier import (
    BaseContractVerifier,
    CallableContractVerifier,
    ContractVerifier,
    ResponseShapeVerifier,
    TaskContractVerifier,
)

__all__ = [
    "BaseContractVerifier",
    "CallableContractVerifier",
    "ContractVerifier",
    "ResponseShapeVerifier",
    "TaskContractVerifier",
]
