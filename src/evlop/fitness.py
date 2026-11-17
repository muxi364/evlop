"""Darwinian fitness scoring, Jaccard deduplication/merge, and lifecycle governance."""

from __future__ import annotations

from datetime import datetime, timezone
import math
import re

from evlop.models import EvlopConfig, Gene

_TOKEN_RE = re.compile(r"[a-z0-9_\-]+|[\u4e00-\u9fff]")


def tokenize(text: str) -> set[str]:
    """Extract normalized alphanumeric words and individual CJK character tokens."""
    return set(_TOKEN_RE.findall(text.lower()))


def jaccard_similarity(text_a: str, text_b: str) -> float:
    """Compute Jaccard token overlap similarity in [0.0, 1.0]."""
    tokens_a = tokenize(text_a)
    tokens_b = tokenize(text_b)
    if not tokens_a and not tokens_b:
        return 1.0
    if not tokens_a or not tokens_b:
        return 0.0
    intersection = len(tokens_a & tokens_b)
    union = len(tokens_a | tokens_b)
    return intersection / union if union else 0.0


def _days_since(iso_ts: str, now: datetime) -> float:
    """Compute elapsed days since `iso_ts`, clamped to >= 0.0 on future/malformed timestamps."""
    if not iso_ts:
        return 0.0
    try:
        normalized = iso_ts[:-1] + "+00:00" if iso_ts.endswith("Z") else iso_ts
        parsed = datetime.fromisoformat(normalized)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        delta_days = (now - parsed).total_seconds() / 86400.0
        return max(0.0, delta_days)
    except (ValueError, TypeError):
        return 0.0


def compute_fitness(gene: Gene, config: EvlopConfig, now: datetime | None = None) -> float:
    """
    Compute Darwinian Fitness Score for a Gene:
    Fitness(g) = ((S + 1) / (S + F + 2)) * (1 + 0.5 * ln(1 + S)) * V_bonus * 2^(-delta_t / H)
    """
    ref_now = now or datetime.now(timezone.utc)
    if ref_now.tzinfo is None:
        ref_now = ref_now.replace(tzinfo=timezone.utc)

    s = max(0, gene.success_count)
    f = max(0, gene.failure_count)

    smoothed_rate = (s + 1.0) / (s + f + 2.0)
    volume_boost = 1.0 + 0.5 * math.log(1.0 + s)
    v_bonus = 1.5 if gene.verified_gate else 0.8

    delta_days = _days_since(gene.last_used_at, ref_now)
    half_life = max(1.0, config.half_life_days)
    decay = math.pow(2.0, -delta_days / half_life)

    return round(smoothed_rate * volume_boost * v_bonus * decay, 4)


def _merge_two_genes(primary: Gene, duplicate: Gene) -> Gene:
    """Merge duplicate gene statistics and retain richer strategy text."""
    richer_strategy = (
        duplicate.strategy if len(duplicate.strategy) > len(primary.strategy) else primary.strategy
    )
    richer_anti = (
        duplicate.anti_pattern
        if len(duplicate.anti_pattern) > len(primary.anti_pattern)
        else primary.anti_pattern
    )
    created_at = (
        min(primary.created_at, duplicate.created_at)
        if (primary.created_at and duplicate.created_at)
        else (primary.created_at or duplicate.created_at)
    )
    last_used_at = max(primary.last_used_at, duplicate.last_used_at)

    return Gene(
        id=primary.id,
        title=primary.title,
        category=primary.category,
        trigger=primary.trigger if len(primary.trigger) >= len(duplicate.trigger) else duplicate.trigger,
        strategy=richer_strategy,
        anti_pattern=richer_anti,
        success_count=primary.success_count + duplicate.success_count,
        failure_count=primary.failure_count + duplicate.failure_count,
        verified_gate=bool(primary.verified_gate or duplicate.verified_gate),
        created_at=created_at,
        last_used_at=last_used_at,
        status=primary.status,
        fitness=primary.fitness,
    )


def govern_genes(
    genes: list[Gene],
    config: EvlopConfig,
    now: datetime | None = None,
    similarity_threshold: float = 0.65,
) -> list[Gene]:
    """
    Deduplicate near-identical genes, recalculate Darwinian fitness scores,
    update status ('promoted', 'candidate', 'archived'), and sort by fitness descending.
    """
    merged: list[Gene] = []
    for incoming in genes:
        sig_incoming = f"{incoming.title} {incoming.trigger}"
        matched_idx: int | None = None
        for idx, existing in enumerate(merged):
            if existing.id == incoming.id:
                matched_idx = idx
                break
            sig_existing = f"{existing.title} {existing.trigger}"
            if jaccard_similarity(sig_incoming, sig_existing) >= similarity_threshold:
                matched_idx = idx
                break
        if matched_idx is not None:
            merged[matched_idx] = _merge_two_genes(merged[matched_idx], incoming)
        else:
            merged.append(incoming)

    for g in merged:
        g.fitness = compute_fitness(g, config, now=now)
        if g.fitness < config.prune_threshold or g.failure_count > g.success_count + 2:
            g.status = "archived"
        elif (
            g.verified_gate
            and g.success_count >= 1
            and g.fitness >= config.promote_threshold
        ):
            g.status = "promoted"
        else:
            g.status = "candidate"

    merged.sort(key=lambda item: (item.status == "promoted", item.fitness, item.success_count), reverse=True)
    return merged
