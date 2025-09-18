import os
import pandas as pd
import subprocess
import os
import re
import cv2

def round_up(base_folder="unzipped"):
    all_trades = []
    all_filtered_trades = []

    for folder in sorted(os.listdir(base_folder)):
        if folder.startswith("collected_files_"):
            folder_path = os.path.join(base_folder, folder)
            files = os.listdir(folder_path)

            if "trades.csv" in files:
                df = pd.read_csv(os.path.join(folder_path, "trades.csv"))
                all_trades.append(df)

                df = pd.read_csv(os.path.join(folder_path, "trades_filtered.csv"))
                all_filtered_trades.append(df)

    trades_df = pd.concat(all_trades, ignore_index=True) if all_trades else pd.DataFrame()
    filtered_trades_df = pd.concat(all_filtered_trades, ignore_index=True) if all_filtered_trades else pd.DataFrame()

    if not trades_df.empty:
        trades_df.to_csv("trades.csv", index=False)
    if not filtered_trades_df.empty:
        filtered_trades_df.to_csv("trades_filtered.csv", index=False)
    
    return trades_df, filtered_trades_df


def map_pair(symbol):
    if symbol == "natural_gas":
        return "XNGUSD"
    else:
        return symbol
    


def get_frame(url, output_path="frame.jpg", cookies_file=None, clip_length=5):
    """
    Downloads one frame from a YouTube video at the given timestamp using yt-dlp + ffmpeg (subprocess only).
    
    Args:
        url (str): YouTube URL (with optional ?t=seconds).
        output_path (str): Path to save the extracted frame.
        cookies_file (str): Path to cookies.txt (optional).
        clip_length (int): Length of the clip to download (in seconds).
    """
    # Extract timestamp from URL (?t=110 or &t=110s)
    match = re.search(r"[?&]t=(\d+)", url)
    timestamp = int(match.group(1)) if match else 0

    # Temp file for the short clip
    temp_video = "temp_video"

    # Build yt-dlp command
    ytdlp_cmd = [
        "yt-dlp",
        "-f", "bestvideo[height=720]",
        "-o", temp_video+".mp4",
        "--download-sections", f"*{max(0, timestamp-1)}-{timestamp+clip_length}"
    ]
    if cookies_file:
        ytdlp_cmd += ["--cookies", cookies_file]
    ytdlp_cmd.append(url)
    


    # Run yt-dlp to download only the short section
    subprocess.run(ytdlp_cmd)
    for ext in [".mp4",".mkv","webm"]:
        if os.path.exists(temp_video+ext):
            # os.remove(temp_video+ext)
            video_path = temp_video+ext
            break
    # Extract one frame at the exact timestamp
    if os.path.exists(output_path):
        os.remove(output_path)
    ffmpeg_cmd = [
        "ffmpeg",
        "-ss", str(1),
        "-i", video_path,
        "-frames:v", "1",
        "-q:v", "2",
        output_path
    ]
    subprocess.run(ffmpeg_cmd)

    # Clean up
    if os.path.exists(video_path):
        os.remove(video_path)

    frame = cv2.imread(output_path)
    return frame

    


if __name__ == "__main__":
    round_up()
    