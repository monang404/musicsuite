from engines.timestamp.parsers.timestamp_parser import parse_timestamps_from_text

def extract_description_timestamps(info: dict) -> list[dict] | None:
    description = info.get("description") or ""
    if not description.strip():
        return None

    entries = parse_timestamps_from_text(description)
    return entries if len(entries) >= 2 else None
