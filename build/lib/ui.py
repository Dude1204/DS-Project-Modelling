import os
import tempfile
from pathlib import Path
import streamlit as st
import json
from highlight_utils import create_highlight_clip, compose_highlight_clip

APP_DIR = Path(__file__).resolve().parent

# Default logos
DEFAULT_NON_BIBS_LOGO = APP_DIR / "logos" / "Non-Bibs Logo.png"
DEFAULT_BIBS_LOGO = APP_DIR / "logos" / "Bibs Logo.png"

st.title("Football Highlight Maker")

st.sidebar.header("Team Setup")

# Non-Bibs Team
st.sidebar.subheader("Non-Bibs Team")
non_bibs_name = st.sidebar.text_input("Team Name", "Non-bibs FC")
non_bibs_players = st.sidebar.text_area("Players (comma-separated)", "George, Gerald, Alex, Ben, Yaw, JC, Sam")
non_bibs_captain = st.sidebar.selectbox("Captain", non_bibs_players.split(", ") if non_bibs_players else [])
non_bibs_logo_text = st.sidebar.text_input("Logo Path", value="logos/Non-Bibs Logo.png", key="non_bibs_logo_text")
non_bibs_logo = st.sidebar.file_uploader("Upload Logo", type=["png", "jpg"], key="non_bibs_logo")

# Bibs Team
st.sidebar.subheader("Bibs Team")
bibs_name = st.sidebar.text_input("Team Name", "Bibs FC")
bibs_players = st.sidebar.text_area("Players (comma-separated)", "Manzan, Jason, Pavlos, Kevin, Aaron, Yi, Ringer")
bibs_captain = st.sidebar.selectbox("Captain", bibs_players.split(", ") if bibs_players else [])
bibs_logo_text = st.sidebar.text_input("Logo Path", value="logos/Bibs Logo.png", key="bibs_logo_text")
bibs_logo = st.sidebar.file_uploader("Upload Logo", type=["png", "jpg"], key="bibs_logo")

# Video and Settings
st.header("Video Settings")
video_path_text = st.text_input("Main Video Path", value="Game 1.mp4")
video_path = st.file_uploader("Upload Main Video", type=["mp4", "avi", "mov", "mkv"])
game_number = st.number_input("Game Number", 1, 10, 1)
extend_clips = st.number_input("Extend Clips (seconds)", 0, 10, 0)

# Highlights
st.header("Highlights")
highlights_input = st.text_area(
    "Highlights (JSON format)",
    '[\n    {"time": 2.11, "text": "Pre-Kick-off Game"},\n    {"time": 22.33, "team": "b", "scored": "Pavlos", "assist": "Manzan", "replay": "h"}\n]',
    height=200
)

# Optional: Cam2 and Replays
st.header("Optional Settings")
use_cam2 = st.checkbox("Use Cam2")
cam2_time = 0.0
cam2_path = ""
cam2_overlap = 100
if use_cam2:
    cam2_time = st.number_input("Cam2 Time", 0.0, step=0.01)
    cam2_path = st.text_input("Cam2 Path", value="Game 1 Cam2.mp4")
    cam2_overlap = st.number_input("Cam2 Overlap PX", 100)

replays_h_time = st.number_input("Replays Home Time", 0.0, step=0.01)
replays_h_path = st.text_input("Replays Home Path", value="Game 1 Home.mp4")
replays_a_time = st.number_input("Replays Away Time", 0.0, step=0.01)
replays_a_path = st.text_input("Replays Away Path", value="Game 1 Away.mp4")

# Fix Scores
fix_scores_input = st.text_area("Fix Scores (JSON)", "[]")

# Final Score
final_score_n = st.number_input("Final Score Non-Bibs", 0)
final_score_b = st.number_input("Final Score Bibs", 0)

status_container = st.empty()
progress_bar = st.progress(0)


def resolve_input_path(path_input):
    if not path_input:
        return None

    path = Path(path_input)
    if path.is_absolute():
        return path

    # Try the app directory first, then current working directory.
    app_path = APP_DIR / path_input
    if app_path.exists():
        return app_path

    cwd_path = Path.cwd() / path_input
    if cwd_path.exists():
        return cwd_path

    # fallback to the raw path so the original function can raise a meaningful error
    return path


def update_progress(log_container, progress_bar, logs, message, progress=None):
    logs.append(message)
    log_container.markdown(f"```\n" + "\n".join(logs) + "\n```")
    if progress is not None:
        progress_bar.progress(progress)

if st.button("Generate and Preview Highlight Video"):
    progress_bar = st.progress(0)
    status_container = st.empty()
    logs = []
    try:
        non_bibs_logo_path = non_bibs_logo.name if non_bibs_logo else (non_bibs_logo_text or "logos/Non-Bibs Logo.png")
        bibs_logo_path = bibs_logo.name if bibs_logo else (bibs_logo_text or "logos/Bibs Logo.png")
        non_bibs_team = {
            "name": non_bibs_name,
            "players": [p.strip() for p in non_bibs_players.split(",")],
            "captain": non_bibs_captain,
            "logo": non_bibs_logo_path
        }
        bibs_team = {
            "name": bibs_name,
            "players": [p.strip() for p in bibs_players.split(",")],
            "captain": bibs_captain,
            "logo": bibs_logo_path
        }

        if non_bibs_logo:
            with open(non_bibs_logo.name, "wb") as f:
                f.write(non_bibs_logo.getbuffer())
        if bibs_logo:
            with open(bibs_logo.name, "wb") as f:
                f.write(bibs_logo.getbuffer())

        highlights = json.loads(highlights_input)

        if video_path:
            video_file_path = video_path.name
            with open(video_file_path, "wb") as f:
                f.write(video_path.getbuffer())
            resolved_video_path = video_file_path
        elif video_path_text:
            resolved_video_path = resolve_input_path(video_path_text)
            if not resolved_video_path or not resolved_video_path.exists():
                raise FileNotFoundError(f"Main video not found: {video_path_text}")
        else:
            raise FileNotFoundError("Please provide main video file or path.")

        cam2 = None
        if use_cam2 and cam2_path:
            resolved_cam2_path = resolve_input_path(cam2_path)
            if not resolved_cam2_path or not resolved_cam2_path.exists():
                raise FileNotFoundError(f"Cam2 video not found: {cam2_path}")
            cam2 = {"time": cam2_time, "path": str(resolved_cam2_path), "overlap_px": cam2_overlap}

        replays = None
        if replays_h_path and replays_a_path:
            resolved_replays_h = resolve_input_path(replays_h_path)
            resolved_replays_a = resolve_input_path(replays_a_path)
            if not resolved_replays_h.exists() or not resolved_replays_a.exists():
                raise FileNotFoundError("Replay files not found; check the replay paths")
            replays = {
                "time_h": replays_h_time, "path_h": str(resolved_replays_h),
                "time_a": replays_a_time, "path_a": str(resolved_replays_a)
            }

        fix_scores = json.loads(fix_scores_input)

        update_progress(status_container, progress_bar, logs, "Building highlight clip", 50)
        clip = compose_highlight_clip(
            str(resolved_video_path), highlights, non_bibs_team, bibs_team,
            extend_clips=extend_clips, game=game_number,
            fix_scores=fix_scores, final_score={"n": final_score_n, "b": final_score_b} if final_score_n or final_score_b else None,
            cam2=cam2, replays=replays
        )

        st.session_state['preview_clip'] = clip

        with tempfile.TemporaryDirectory() as tmpdir:
            preview_path = os.path.join(tmpdir, "preview.mp4")
            update_progress(status_container, progress_bar, logs, "Rendering preview video", 70)
            clip.write_videofile(
                preview_path,
                codec="libx264",
                fps=15,
                preset="ultrafast",
                bitrate="500k",
                audio=False,
                verbose=False,
                logger=None
            )
            update_progress(status_container, progress_bar, logs, "Preview ready", 100)
            st.video(preview_path)

    except Exception as e:
        st.error(f"Error: {str(e)}")

if 'preview_clip' in st.session_state:
    if st.button("Save Highlight Video"):
        try:
            output_path = f"highlight_game_{game_number}.mp4"
            st.session_state['preview_clip'].write_videofile(
                output_path,
                codec="libx264",
                fps=30,
                preset="medium",
                bitrate="2000k",
                audio=True,
                verbose=False,
                logger=None
            )
            st.success(f"Highlight video saved as: {output_path}")
        except Exception as e:
            st.error(f"Save error: {str(e)}")

    # Live preview with frame scrubbing
    clip = st.session_state['preview_clip']
    duration = clip.duration
    time_slider = st.slider("Scrub through the video", 0.0, duration, 0.0, 0.1, key="time_slider")
    frame = clip.get_frame(time_slider)
    st.image(frame, caption=f"Frame at {time_slider:.1f} seconds")

st.header("Create Thumbnail")
thumbnail_time = st.number_input("Thumbnail Time (seconds)", 0.0, step=0.1)
if st.button("Create Thumbnail"):
    if 'preview_clip' in st.session_state:
        frame = st.session_state['preview_clip'].get_frame(thumbnail_time)
        from PIL import Image
        img = Image.fromarray(frame)
        img.save("thumbnail.png")
        st.image("thumbnail.png", caption=f"Thumbnail at {thumbnail_time:.1f} seconds")
    else:
        st.error("Generate video first")