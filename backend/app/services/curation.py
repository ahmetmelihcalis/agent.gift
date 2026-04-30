from ..schemas import ProductCandidate


def hydrate_curated_products(
    curated_payload: list[dict], candidates: list[ProductCandidate]
) -> list[dict]:
    hydrated: list[dict] = []
    used_indexes: set[int] = set()

    for item in curated_payload:
        candidate_index = item.get("candidate_index")
        if not isinstance(candidate_index, int):
            continue

        if candidate_index < 1 or candidate_index > len(candidates):
            continue

        if candidate_index in used_indexes:
            continue

        used_indexes.add(candidate_index)

        candidate = candidates[candidate_index - 1]
        hydrated.append(
            {
                "name": candidate.name,
                "why_it_matches": item.get("why_it_matches") or candidate.why_it_matches,
                "price_label": candidate.price_label,
                "url": str(candidate.url),
                "source": candidate.source,
                "editorial_note": item.get("editorial_note") or candidate.editorial_note,
                "matched_signals": item.get("matched_signals") or candidate.matched_signals,
                "caveats": item.get("caveats") or candidate.caveats,
                "comparison_note": item.get("comparison_note") or candidate.comparison_note,
            }
        )

    return hydrated


def _normalize_source(value: str) -> str:
    return value.strip().lower()


def diversify_curated_products(
    curated_products: list[dict], candidates: list[ProductCandidate], target_count: int = 3
) -> list[dict]:
    if len(curated_products) <= 1:
        return curated_products[:target_count]

    candidate_pool = list(curated_products)
    curated_names = {
        item.get("name", "").strip().lower() for item in curated_products if item.get("name")
    }
    for candidate in candidates:
        if candidate.name.strip().lower() not in curated_names:
            candidate_pool.append(
                {
                    "name": candidate.name,
                    "why_it_matches": candidate.why_it_matches,
                    "price_label": candidate.price_label,
                    "url": str(candidate.url),
                    "source": candidate.source,
                    "editorial_note": candidate.editorial_note,
                    "matched_signals": candidate.matched_signals,
                    "caveats": candidate.caveats,
                    "comparison_note": candidate.comparison_note,
                }
            )

    selected: list[dict] = []
    used_sources: set[str] = set()
    used_pairs: set[tuple[str, str]] = set()

    for item in candidate_pool:
        pair = (
            item.get("name", "").strip().lower(),
            _normalize_source(item.get("source", "")),
        )
        source = pair[1]
        if pair in used_pairs or source in used_sources:
            continue
        used_pairs.add(pair)
        used_sources.add(source)
        selected.append(item)
        if len(selected) >= target_count:
            return selected

    for item in candidate_pool:
        if len(selected) >= target_count:
            break
        pair = (
            item.get("name", "").strip().lower(),
            _normalize_source(item.get("source", "")),
        )
        if pair in used_pairs:
            continue
        used_pairs.add(pair)
        selected.append(item)

    return selected[:target_count]


def fill_missing_curated_products(
    curated_products: list[dict], candidates: list[ProductCandidate], target_count: int = 3
) -> list[dict]:
    filled = list(curated_products)
    used_pairs = {
        (item.get("name", "").strip().lower(), item.get("source", "").strip().lower())
        for item in filled
    }
    used_sources = {item.get("source", "").strip().lower() for item in filled}

    for candidate in candidates:
        if len(filled) >= target_count:
            break

        pair = (candidate.name.strip().lower(), candidate.source.strip().lower())
        if pair in used_pairs or pair[1] in used_sources:
            continue

        used_pairs.add(pair)
        used_sources.add(pair[1])
        filled.append(
            {
                "name": candidate.name,
                "why_it_matches": candidate.why_it_matches,
                "price_label": candidate.price_label,
                "url": str(candidate.url),
                "source": candidate.source,
                "editorial_note": candidate.editorial_note,
                "matched_signals": candidate.matched_signals,
                "caveats": candidate.caveats,
                "comparison_note": candidate.comparison_note,
            }
        )

    for candidate in candidates:
        if len(filled) >= target_count:
            break

        pair = (candidate.name.strip().lower(), candidate.source.strip().lower())
        if pair in used_pairs:
            continue

        used_pairs.add(pair)
        filled.append(
            {
                "name": candidate.name,
                "why_it_matches": candidate.why_it_matches,
                "price_label": candidate.price_label,
                "url": str(candidate.url),
                "source": candidate.source,
                "editorial_note": candidate.editorial_note,
                "matched_signals": candidate.matched_signals,
                "caveats": candidate.caveats,
                "comparison_note": candidate.comparison_note,
            }
        )

    return filled[:target_count]
