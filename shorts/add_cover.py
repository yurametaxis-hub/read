#!/usr/bin/env python3
"""Put the cover image in front of a short for 0.1 s, so it is the first frame the cover picker offers
in TikTok and in the YouTube app. In the feed it flashes for a few frames and is hardly noticed.

    python3 shorts/add_cover.py VIDEO.mp4 COVER.png OUT.mp4 [--dur 0.1]
"""
import argparse
import json
import subprocess


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("cover")
    ap.add_argument("out")
    ap.add_argument("--dur", type=float, default=0.1)
    a = ap.parse_args()
    info = json.loads(subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,r_frame_rate,sample_rate,channels",
         "-of", "json", a.video], capture_output=True, text=True, check=True).stdout)["streams"]
    v = next(s for s in info if s["codec_type"] == "video")
    au = next(s for s in info if s["codec_type"] == "audio")
    fps, sr = v["r_frame_rate"], au["sample_rate"]
    layout = "stereo" if int(au.get("channels", 2)) == 2 else "mono"
    subprocess.run([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-loop", "1", "-framerate", fps, "-t", str(a.dur), "-i", a.cover,
        "-f", "lavfi", "-t", str(a.dur), "-i", f"anullsrc=r={sr}:cl={layout}",
        "-i", a.video,
        "-filter_complex", "[0:v]scale=1080:1920,format=yuv420p,setsar=1[c];[2:v]setsar=1[m];"
                           "[c][1:a][m][2:a]concat=n=2:v=1:a=1[v][au]",
        "-map", "[v]", "-map", "[au]", "-r", fps, "-c:v", "libx264", "-preset", "slow", "-crf", "18",
        "-profile:v", "high", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
        a.out], check=True)
    print(a.out)


if __name__ == "__main__":
    main()
