def extract_thumbnail_ocr_timestamps(thumbnail_url: str) -> str | None:
    """
    Fetch OCR text from the YouTube video's thumbnail.
    Uses the free OCR.space API with a demo key or user-configured key.
    """
    print(f"[OCR] URL Thumbnail: {thumbnail_url}")
    try:
        from config.settings import load_config
        config = load_config()
        api_key = config.get("ocr_space_api_key", "helloworld")
    except Exception:
        api_key = "helloworld"

    print("[OCR] Menggunakan API Key: *****")
    try:
        import urllib.request
        import urllib.parse
        import json

        if not thumbnail_url:
            print("[OCR] URL kosong.")
            return None

        # Build url for OCR.space
        params = {
            "apikey": api_key,
            "url": thumbnail_url,
            "language": "eng",
            "isOverlayRequired": "false"
        }
        query_string = urllib.parse.urlencode(params)
        url = f"https://api.ocr.space/parse/imageurl?{query_string}"

        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as response:
            res_data = json.loads(response.read().decode("utf-8"))

        print(f"[OCR] Response JSON: {json.dumps(res_data)}")

        if not res_data:
            print("[OCR] Response kosong.")
            return None

        if res_data.get("IsErroredOnProcessing"):
            print(f"[OCR] Error processing: {res_data.get('ErrorMessage')}")
            return None

        results = res_data.get("ParsedResults")
        if results and len(results) > 0:
            parsed_text = results[0].get("ParsedText")
            print(f"[OCR] Parsed Text:\n{parsed_text}")
            return parsed_text
            
        print("[OCR] Tidak ada ParsedResults.")
    except Exception as e:
        print(f"[OCR] Exception: {str(e)}")
    return None
