import yt_dlp


def download_video(url: str, output_dir: str = ".") -> dict:
    """Download a video and return its metadata.

    Args:
        url: URL of the video to download.
        output_dir: Directory to save the downloaded video.

    Returns:
        Dict with 'url', 'title', 'description', 'uploader', 'upload_date', 'duration', and 'filepath' keys.
    """
    opts = {
        "outtmpl": f"{output_dir}/%(title)s.%(ext)s",
        "format": "bestvideo+bestaudio/best",
        "merge_output_format": "mp4",
        "writedescription": True,
        "quiet": False,
    }
    with yt_dlp.YoutubeDL(opts) as ydl:  # type: ignore
        info = ydl.extract_info(url, download=True)
        return {
            "url": url,
            "title": info.get("title"),
            "description": info.get("description"),
            "uploader": info.get("uploader"),
            "upload_date": info.get("upload_date"),
            "duration": info.get("duration"),
            "filepath": ydl.prepare_filename(info),
        }
