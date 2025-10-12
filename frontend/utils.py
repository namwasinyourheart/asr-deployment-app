import tempfile
import httpx
import shutil
import re

def download_audio_from_url(url: str):
    """Tải file audio từ URL (hỗ trợ Google Drive)"""
    try:
        output_path = tempfile.mktemp(suffix=".wav")
        with httpx.Client(follow_redirects=True, timeout=60) as client:
            r = client.get(url)
            if "drive.google.com" in r.url.host and "export=download" in r.url.query:
                m = re.search(r"confirm=([0-9A-Za-z_]+)", r.text)
                if m:
                    token = m.group(1)
                    download_url = url + "&confirm=" + token
                    r = client.get(download_url)
            r.raise_for_status()
            with open(output_path, "wb") as f:
                f.write(r.content)
        return output_path, None
    except Exception as e:
        return None, f"Failed to download audio: {e}"



import csv
import os
from datetime import datetime

CSV_PATH = "/home/nampv1/projects/asr/asr-demo-app/db/corrections.csv"

def save_corrections(user_name: str, corrections_text: str):
    """
    Lưu nhiều cặp corrections vào CSV.
    - user_name: tên user nhập
    - corrections_text: nhiều dòng, mỗi dòng dạng "error -> correct"
    """
    if not user_name or not corrections_text.strip():
        return "⚠️ Missing input fields!"

    user_id = user_name.strip().lower().replace(" ", "_")
    now = datetime.now()
    date_str = now.strftime("%d/%m/%y")
    time_str = now.strftime("%H:%M:%S")

    rows_to_save = []
    for line in corrections_text.strip().splitlines():
        line = line.strip()
        if "->" not in line:
            continue
        rows_to_save.append([user_name, user_id, line, date_str, time_str])

    if not rows_to_save:
        return "⚠️ No valid corrections found! Use format: error -> correct"

    file_exists = os.path.isfile(CSV_PATH)
    with open(CSV_PATH, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["user_name", "user_id", "error_correct_pair", "date", "time"])
        writer.writerows(rows_to_save)

    return f"✅ Saved {len(rows_to_save)} correction(s)."

