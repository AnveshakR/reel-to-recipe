import logging
import os
import subprocess

import cv2

logger = logging.getLogger(__name__)


def extract_frames_and_audio(
    video_path: str, output_dir: str = ".", frames_per_second: float = 0.2
) -> tuple:
    """Extract frames and audio from a video file.

    Args:
        video_path: Path to the input video file.
        output_dir: Directory to write extracted frames and audio.
        frames_per_second: Number of frames to capture per second of video.

    Returns:
        Tuple of (frames, audio_path) where frames is a list of dicts with
        'index', 'timestamp', and 'path' keys, and audio_path is the path to the extracted MP3.
    """
    audio_path = os.path.join(output_dir, "audio.mp3")
    subprocess.run(
        ["ffmpeg", "-i", video_path, "-vn", "-acodec", "mp3", "-y", audio_path],
        check=True,
    )

    frames_dir = os.path.join(output_dir, "frames")
    os.makedirs(frames_dir, exist_ok=True)

    video = cv2.VideoCapture(video_path)
    fps = video.get(cv2.CAP_PROP_FPS)
    frame_interval = int(fps / frames_per_second)

    frames = []
    frame_idx = 0

    while video.isOpened():
        ret, frame = video.read()
        if not ret:
            break
        if frame_idx % frame_interval == 0:
            timestamp = frame_idx / fps
            frame_path = os.path.join(frames_dir, f"frame_{frame_idx}.jpg")
            cv2.imwrite(frame_path, frame)
            frames.append(
                {"index": frame_idx, "timestamp": timestamp, "path": frame_path}
            )
        frame_idx += 1

    video.release()
    logger.info("Extracted %d frames and audio.", len(frames))
    return frames, audio_path
