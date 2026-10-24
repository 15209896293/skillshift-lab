from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "agent-first"))

from agent_first import DEEPSEEK_V41_FLASH_PRICE_SNAPSHOT, DeepSeekUsage, estimate_cost_fen
from agent_first.deepseek_usage import parse_deepseek_usage


def response(*, cached: object = 250_000, total: object = 1_500_000) -> dict[str, object]:
    return {
        "id": "synthetic-id",
        "model": "deepseek-v4.1-flash",
        "usage": {
            "prompt_tokens": 1_000_000,
            "completion_tokens": 500_000,
            "total_tokens": total,
            "prompt_tokens_details": {"cached_tokens": cached},
            "prompt_cache_hit_tokens": cached,
            "prompt_cache_miss_tokens": 1_000_000 - cached if isinstance(cached, int) and not isinstance(cached, bool) else 0,
        },
    }


class DeepSeekUsageContractTests(unittest.TestCase):
    def test_usage_requires_consistent_integer_fields_and_cache_counts(self) -> None:
        parsed = parse_deepseek_usage(response())
        self.assertEqual(750_000, parsed.prompt_cache_miss_tokens)
        self.assertEqual(1_500_000, parsed.total_tokens)

    def test_missing_wrong_or_boolean_usage_is_rejected_without_echo(self) -> None:
        wrong_cache_breakdown = response()
        wrong_cache_breakdown["usage"]["prompt_cache_miss_tokens"] = 999
        for malformed in (
            {"id": "synthetic-id"},
            response(total=3),
            response(cached=True),
            wrong_cache_breakdown,
            {**response(), "model": ""},
        ):
            with self.subTest(malformed=malformed):
                with self.assertRaisesRegex(ValueError, "metadata"):
                    parse_deepseek_usage(malformed)

    def test_cost_uses_explicit_peak_offpeak_snapshot_and_rounds_up_to_fen(self) -> None:
        usage = parse_deepseek_usage(response())
        snapshot = DEEPSEEK_V41_FLASH_PRICE_SNAPSHOT
        self.assertEqual("deepseek-v4.1-flash-2026-09-10-r1", snapshot.snapshot_id)
        # Peak: .25M * 4 + .75M * 200 + .5M * 800 = 551 fen.
        self.assertEqual(551, estimate_cost_fen(usage, snapshot, peak=True))
        # Off-peak rates are half the peak snapshot.
        self.assertEqual(276, estimate_cost_fen(usage, snapshot, peak=False))
        one_token = DeepSeekUsage("id", "model", 1, 0, 1, 0, 1)
        self.assertEqual(1, estimate_cost_fen(one_token, snapshot, peak=True))


if __name__ == "__main__":
    unittest.main()
