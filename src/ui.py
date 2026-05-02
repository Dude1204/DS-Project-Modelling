import streamlit as st
import json
from highlight_utils import create_highlight_clip

st.title("Football Highlight Maker")

st.sidebar.header("Team Setup")

# Non-Bibs Team
st.sidebar.subheader("Non-Bibs Team")
non_bibs_name = st.sidebar.text_input("Team Name", "Non-bibs FC")
non_bibs_players = st.sidebar.text_area("Players (comma-separated)", "George, Gerald, Alex, Ben, Yaw, JC, Sam")
non_bibs_captain = st.sidebar.selectbox("Captain", non_bibs_players.split(", ") if non_bibs_players else [])
non_bibs_logo = st.sidebar.file_uploader("Logo", type=["png", "jpg"], key="non_bibs_logo")

# Bibs Team
st.sidebar.subheader("Bibs Team")
bibs_name = st.sidebar.text_input("Team Name", "Bibs FC")
bibs_players = st.sidebar.text_area("Players (comma-separated)", "Manzan, Jason, Pavlos, Kevin, Aaron, Yi, Ringer")
bibs_captain = st.sidebar.selectbox("Captain", bibs_players.split(", ") if bibs_players else [])
bibs_logo = st.sidebar.file_uploader("Logo", type=["png", "jpg"], key="bibs_logo")

# Video and Settings
st.header("Video Settings")
video_path = st.text_input("Main Video Path", "Game 1.mp4")
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
cam2_time = st.number_input("Cam2 Time (if any)", 0.0, step=0.01)
cam2_path = st.text_input("Cam2 Path")
cam2_overlap = st.number_input("Cam2 Overlap PX", 100)

replays_h_time = st.number_input("Replays Home Time", 0.0, step=0.01)
replays_h_path = st.text_input("Replays Home Path")
replays_a_time = st.number_input("Replays Away Time", 0.0, step=0.01)
replays_a_path = st.text_input("Replays Away Path")

# Fix Scores
fix_scores_input = st.text_area("Fix Scores (JSON)", "[]")

# Final Score
final_score_n = st.number_input("Final Score Non-Bibs", 0)
final_score_b = st.number_input("Final Score Bibs", 0)

if st.button("Generate Highlight Video"):
    try:
        # Prepare teams
        non_bibs_team = {
            "name": non_bibs_name,
            "players": [p.strip() for p in non_bibs_players.split(",")],
            "captain": non_bibs_captain,
            "logo": non_bibs_logo.name if non_bibs_logo else None
        }
        bibs_team = {
            "name": bibs_name,
            "players": [p.strip() for p in bibs_players.split(",")],
            "captain": bibs_captain,
            "logo": bibs_logo.name if bibs_logo else None
        }

        # Save logos if uploaded
        if non_bibs_logo:
            with open(non_bibs_logo.name, "wb") as f:
                f.write(non_bibs_logo.getbuffer())
        if bibs_logo:
            with open(bibs_logo.name, "wb") as f:
                f.write(bibs_logo.getbuffer())

        # Parse highlights
        highlights = json.loads(highlights_input)

        # Optional cam2
        cam2 = None
        if cam2_path:
            cam2 = {"time": cam2_time, "path": cam2_path, "overlap_px": cam2_overlap}

        # Optional replays
        replays = None
        if replays_h_path and replays_a_path:
            replays = {
                "time_h": replays_h_time, "path_h": replays_h_path,
                "time_a": replays_a_time, "path_a": replays_a_path
            }

        # Fix scores
        fix_scores = json.loads(fix_scores_input)

        # Final score
        final_score = {"n": final_score_n, "b": final_score_b} if final_score_n or final_score_b else None

        # Call the function
        create_highlight_clip(
            video_path, highlights, non_bibs_team, bibs_team,
            extend_clips=extend_clips, game=game_number,
            fix_scores=fix_scores, final_score=final_score,
            cam2=cam2, replays=replays
        )

        st.success("Highlight video generated successfully!")

    except Exception as e:
        st.error(f"Error: {str(e)}")