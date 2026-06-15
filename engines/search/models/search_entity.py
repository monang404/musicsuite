from dataclasses import dataclass

@dataclass
class SearchEntity:
    id: str
    url: str
    title: str
    channel: str
    thumbnail_url: str = ""
    upload_date: str = ""
    entity_type: str = ""
