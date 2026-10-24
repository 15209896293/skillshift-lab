"""Strict synthetic DeepSeek usage metadata and versioned local cost estimates."""

from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Mapping


@dataclass(frozen=True)
class DeepSeekUsage:
    request_id: str
    model_id: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    prompt_cache_hit_tokens: int
    prompt_cache_miss_tokens: int


@dataclass(frozen=True)
class DeepSeekPriceSnapshot:
    snapshot_id: str
    peak_cache_hit_fen_per_million: int
    peak_cache_miss_fen_per_million: int
    peak_output_fen_per_million: int
    offpeak_cache_hit_fen_per_million: int
    offpeak_cache_miss_fen_per_million: int
    offpeak_output_fen_per_million: int


DEEPSEEK_V41_FLASH_PRICE_SNAPSHOT = DeepSeekPriceSnapshot(
    snapshot_id="deepseek-v4.1-flash-2026-09-10-r1",
    peak_cache_hit_fen_per_million=4,
    peak_cache_miss_fen_per_million=200,
    peak_output_fen_per_million=800,
    offpeak_cache_hit_fen_per_million=2,
    offpeak_cache_miss_fen_per_million=100,
    offpeak_output_fen_per_million=400,
)


def _nonnegative_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def parse_deepseek_usage(response: Mapping[str, object]) -> DeepSeekUsage:
    """Parse mandatory provider metadata; errors intentionally omit raw response data."""
    try:
        request_id = response["id"]
        model_id = response["model"]
        raw_usage = response["usage"]
        if not isinstance(request_id, str) or not request_id.strip() or len(request_id) > 256:
            raise ValueError
        if not isinstance(model_id, str) or not model_id.strip() or len(model_id) > 128:
            raise ValueError
        if not isinstance(raw_usage, Mapping):
            raise ValueError
        prompt = raw_usage["prompt_tokens"]
        completion = raw_usage["completion_tokens"]
        total = raw_usage["total_tokens"]
        details = raw_usage["prompt_tokens_details"]
        if not isinstance(details, Mapping):
            raise ValueError
        hit = raw_usage["prompt_cache_hit_tokens"]
        miss = raw_usage["prompt_cache_miss_tokens"]
        cached_detail = details["cached_tokens"]
        values = (prompt, completion, total, hit, miss, cached_detail)
        if not all(_nonnegative_int(value) for value in values):
            raise ValueError
        if hit + miss != prompt or cached_detail != hit:
            raise ValueError
        if total != prompt + completion or hit + miss != prompt:
            raise ValueError
        return DeepSeekUsage(request_id, model_id, prompt, completion, total, hit, miss)
    except (KeyError, TypeError, ValueError):
        raise ValueError("DeepSeek usage metadata is missing or inconsistent") from None


def estimate_cost_fen(usage: DeepSeekUsage, snapshot: DeepSeekPriceSnapshot, *, peak: bool) -> int:
    """Return a local estimate rounded up to fen; this is not provider settlement."""
    if not isinstance(peak, bool) or not snapshot.snapshot_id:
        raise ValueError("an explicit price snapshot and peak/offpeak selection are required")
    token_values = (
        usage.prompt_tokens,
        usage.completion_tokens,
        usage.total_tokens,
        usage.prompt_cache_hit_tokens,
        usage.prompt_cache_miss_tokens,
    )
    if not all(_nonnegative_int(value) for value in token_values):
        raise ValueError("usage token counts must be nonnegative integers")
    if (usage.prompt_tokens != usage.prompt_cache_hit_tokens + usage.prompt_cache_miss_tokens
            or usage.total_tokens != usage.prompt_tokens + usage.completion_tokens):
        raise ValueError("usage token counts are inconsistent")
    prefix = "peak" if peak else "offpeak"
    hit_rate = getattr(snapshot, f"{prefix}_cache_hit_fen_per_million")
    miss_rate = getattr(snapshot, f"{prefix}_cache_miss_fen_per_million")
    output_rate = getattr(snapshot, f"{prefix}_output_fen_per_million")
    if not all(_nonnegative_int(rate) for rate in (hit_rate, miss_rate, output_rate)):
        raise ValueError("price rates must be nonnegative integer fen per million tokens")
    numerator = (
        usage.prompt_cache_hit_tokens * hit_rate
        + usage.prompt_cache_miss_tokens * miss_rate
        + usage.completion_tokens * output_rate
    )
    return (numerator + 999_999) // 1_000_000
