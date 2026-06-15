from datetime import datetime

def recency_bonus(upload_date: str) -> int:
    if not upload_date:
        return 0
    try:
        upload = datetime.strptime(upload_date, "%Y%m%d")
        # Base the check on the current time
        delta = datetime.now() - upload
        if delta.days < 365 * 2:
            return 5
    except ValueError:
        pass
    return 0
