from collections.abc import Iterable


def coalesce_items(ids_or_uris: Iterable[str]) -> list[str]:
    return [str(v).strip() for v in ids_or_uris if str(v).strip()]


def coalesce_csv(ids_or_uris: Iterable[str]) -> str:
    return ",".join(coalesce_items(ids_or_uris))
