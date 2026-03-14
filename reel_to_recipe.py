import json
import logging
import os
import shutil
import subprocess
import sys
from datetime import datetime

sys.stdout.reconfigure(line_buffering=True)  # type: ignore
sys.stderr.reconfigure(line_buffering=True)  # type: ignore

from compiler import compile_document, generate_recipe_name
from downloader import download_video
from model_manager import running
from transcriber import transcribe_audio
from video_processor import extract_frames_and_audio
from vision_model import analyze_frames

from CONFIG import VAULT_ROOT, VAULT_PATH, VISION_CONTAINER, TEXT_CONTAINER, WHISPER_CONTAINER

_log_fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
_file_handler = logging.FileHandler(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "reel_to_recipe.log")
)
_file_handler.setFormatter(_log_fmt)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logging.getLogger().addHandler(_file_handler)

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        logger.error("Usage: python main.py <video_url> [base_output_dir]")
        sys.exit(1)

    url = sys.argv[1]
    base_dir = sys.argv[2] if len(sys.argv) > 2 else "."
    parsed_dir = os.path.join(base_dir, "parsed_recipes")
    os.makedirs(parsed_dir, exist_ok=True)

    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = os.path.join(parsed_dir, f"run_{run_id}")
    os.makedirs(run_dir, exist_ok=True)

    logger.info("Run folder: %s", run_dir)

    logger.info("Step 1: Downloading video...")
    metadata = download_video(url, run_dir)
    video_path = metadata["filepath"]

    logger.info("Step 2: Extracting frames and audio...")
    frames, audio_path = extract_frames_and_audio(
        video_path, run_dir, frames_per_second=0.2
    )

    logger.info("Step 3: Analyzing frames with vision model...")
    with running(VISION_CONTAINER):
        frame_descriptions = analyze_frames(frames)

    logger.info("Step 4: Transcribing audio...")
    with running(WHISPER_CONTAINER):
        transcript = transcribe_audio(audio_path)

    logger.info("Step 5: Compiling recipe document...")
    with running(TEXT_CONTAINER):
        recipe_document = compile_document(metadata, frame_descriptions, transcript)
        logger.info("Generating recipe name...")
        recipe_name = generate_recipe_name(recipe_document)

    full_document = f"[Source Reel]({url})\n\n{recipe_document}"

    final_dir = os.path.join(parsed_dir, recipe_name)
    if os.path.exists(final_dir):
        final_dir = f"{final_dir}_{run_id}"
    os.rename(run_dir, final_dir)
    video_path = os.path.join(final_dir, os.path.basename(video_path))
    logger.info("Renamed run folder → %s/", final_dir)

    with open(os.path.join(final_dir, f"{recipe_name}.md"), "w") as f:
        f.write(full_document)

    with open(os.path.join(final_dir, "frames.json"), "w") as f:
        json.dump(frame_descriptions, f, indent=2)

    with open(os.path.join(final_dir, "transcript.txt"), "w") as f:
        f.write(transcript)

    logger.info("Outputs saved to: %s/", final_dir)
    logger.info("Done!")

    logger.info("Step 6: Adding generated MD file to the Obsidian vault...")
    if not os.path.exists(VAULT_PATH):
        logger.warning("Vault directory %s does not exist. Skipping vault integration.", VAULT_PATH)
    else:
        md_file_path = os.path.join(final_dir, f"{recipe_name}.md")
        vault_md_file_path = os.path.join(VAULT_PATH, f"{recipe_name}.md")
        shutil.copy(md_file_path, vault_md_file_path)
        logger.info("Copied %s to %s", md_file_path, vault_md_file_path)

        logger.info("Step 7: Performing Git operations in the vault directory...")
        git_file = os.path.relpath(vault_md_file_path, VAULT_ROOT)
        try:
            subprocess.run(["git", "-C", VAULT_ROOT, "stash"], check=True)
            subprocess.run(["git", "-C", VAULT_ROOT, "fetch", "origin"], check=True)
            subprocess.run(["git", "-C", VAULT_ROOT, "reset", "--hard", "origin/main"], check=True)
            subprocess.run(["git", "-C", VAULT_ROOT, "stash", "pop"], check=True)
            subprocess.run(["git", "-C", VAULT_ROOT, "add", git_file], check=True)
            subprocess.run(
                ["git", "-C", VAULT_ROOT, "commit", "-m", f"Add {recipe_name}.md"],
                check=True,
            )
            subprocess.run(["git", "-C", VAULT_ROOT, "push"], check=True)
            logger.info("Git operations completed successfully.")
        except subprocess.CalledProcessError as e:
            logger.error("Git operation failed: %s", e)
