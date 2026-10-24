"""Deterministic, no-tool educational workflow used only for the R0 Gate A demo."""

from .domain import EducationWorkflow, ReviewKind, WorkflowError, build_synthetic_template
from .deepseek_contract import (
    DEEPSEEK_SYNTHETIC_MAX_TOKENS,
    DEEPSEEK_SYNTHETIC_MAX_INPUT_BYTES,
    DEEPSEEK_SYNTHETIC_MODEL_ID,
    DeepSeekChatContractAdapter,
    build_deepseek_school_synthetic_profile,
)
from .deepseek_runtime import DeepSeekSyntheticRuntimeAdapter
from .deepseek_usage import DeepSeekUsage, DeepSeekPriceSnapshot, DEEPSEEK_V41_FLASH_PRICE_SNAPSHOT, estimate_cost_fen
from .model_gateway import (
    AccessMode,
    DomesticModelGatewayAdapter,
    FallbackGuidanceAdapter,
    ModelGatewayPolicyError,
    ModelProfile,
    ModelUnavailableError,
    ProviderId,
)
from .school_budget import SchoolMonthlySyntheticBudgetPermit, SchoolSyntheticProbePolicy
from .scripted_guidance import ScriptedGuidanceAdapter

__all__ = [
    "EducationWorkflow",
    "DEEPSEEK_SYNTHETIC_MAX_TOKENS",
    "DEEPSEEK_SYNTHETIC_MAX_INPUT_BYTES",
    "DeepSeekUsage",
    "DeepSeekPriceSnapshot",
    "DEEPSEEK_V41_FLASH_PRICE_SNAPSHOT",
    "estimate_cost_fen",
    "DEEPSEEK_SYNTHETIC_MODEL_ID",
    "DeepSeekChatContractAdapter",
    "DeepSeekSyntheticRuntimeAdapter",
    "AccessMode",
    "DomesticModelGatewayAdapter",
    "FallbackGuidanceAdapter",
    "ModelGatewayPolicyError",
    "ModelProfile",
    "ModelUnavailableError",
    "ProviderId",
    "build_deepseek_school_synthetic_profile",
    "ReviewKind",
    "ScriptedGuidanceAdapter",
    "SchoolMonthlySyntheticBudgetPermit",
    "SchoolSyntheticProbePolicy",
    "WorkflowError",
    "build_synthetic_template",
]
