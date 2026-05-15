import os
import tempfile
import time
from datetime import datetime
from pathlib import Path
import streamlit as st
import json
from highlight_utils import create_highlight_clip, compose_highlight_clip, create_custom_thumbnail

APP_DIR = Path(__file__).resolve().parent

def parse_player_names(player_text):
    return [p.strip() for p in player_text.split(",") if p.strip()]


def build_player_options(team_name, non_bibs_names, bibs_names):
    if team_name == "Non-Bibs":
        return non_bibs_names + [f"{name} (OG)" for name in bibs_names]
    return bibs_names + [f"{name} (OG)" for name in non_bibs_names]


def get_output_filename(game_number, ext="mp4"):
    date_string = datetime.now().strftime("%Y%m%d")
    base = f"Game {game_number} highlights-{date_string}"
    version = 1
    while True:
        filename = f"{base}-v{version}.{ext}"
        if not os.path.exists(filename):
            return filename
        version += 1

# Default logos
DEFAULT_NON_BIBS_LOGO = APP_DIR / "logos" / "Non-Bibs Logo.png"
DEFAULT_BIBS_LOGO = APP_DIR / "logos" / "Bibs Logo.png"

st.title("Football Highlight Maker")

EVENT_TYPES = [
    "Kick-off",
    "Penalty",
    "Red Card",
    "Yellow Card",
    "2nd Half",
    "Full Time",
    "Nearly",
    "Save",
    "Custom Text",
    "Zoom and Slowmo",
]


def get_default_state(key, default):
    if key not in st.session_state:
        st.session_state[key] = default
    return st.session_state[key]


def get_versioned_filename(base, ext):
    version = 1
    while True:
        filename = f"{base}-v{version}.{ext}"
        if not os.path.exists(filename):
            return filename
        version += 1


def get_config_filename(game_number):
    date_string = datetime.now().strftime("%Y%m%d")
    base = f"Game {game_number} session-{date_string}"
    return get_versioned_filename(base, "json")


def build_config_data():
    return {
        "generated_at": datetime.now().isoformat(),
        "game_number": st.session_state.get("game_number", 1),
        "home_team": st.session_state.get("home_team", "Non-Bibs"),
        "teams": {
            "non_bibs": {
                "name": st.session_state.get("non_bibs_name", "Non-bibs FC"),
                "players": parse_player_names(st.session_state.get("non_bibs_players", "")),
                "captain": st.session_state.get("non_bibs_captain", ""),
                "logo": st.session_state.get("non_bibs_logo_text", "src/logos/Non-Bibs Logo.png"),
            },
            "bibs": {
                "name": st.session_state.get("bibs_name", "Bibs FC"),
                "players": parse_player_names(st.session_state.get("bibs_players", "")),
                "captain": st.session_state.get("bibs_captain", ""),
                "logo": st.session_state.get("bibs_logo_text", "src/logos/Bibs Logo.png"),
            },
        },
        "video": {
            "main": {
                "path": st.session_state.get("video_path_text", "Game 1.mp4"),
                "uploaded": bool(st.session_state.get("video_path")),
            },
            "extend_clips": st.session_state.get("extend_clips", 0),
            "cam2": {
                "enabled": st.session_state.get("use_cam2", False),
                "time": st.session_state.get("cam2_time", 0.0),
                "path": st.session_state.get("cam2_path_text", ""),
                "overlap_px": st.session_state.get("cam2_overlap", 100),
            },
            "replays": {
                "home": {
                    "time": st.session_state.get("replays_h_time", 0.0),
                    "path": st.session_state.get("replays_h_path_text", ""),
                },
                "away": {
                    "time": st.session_state.get("replays_a_time", 0.0),
                    "path": st.session_state.get("replays_a_path_text", ""),
                },
            },
        },
        "settings": {
            "use_fix_scores": st.session_state.get("use_fix_scores", False),
        },
        "highlights": st.session_state.get("highlights_list", []),
        "fix_scores": st.session_state.get("fix_scores_list", []),
        "final_score": {
            "n": st.session_state.get("final_score_n", 0),
            "b": st.session_state.get("final_score_b", 0),
        },
    }


def load_session_config(config):
    teams = config.get("teams", {})
    non_bibs = teams.get("non_bibs", {})
    bibs = teams.get("bibs", {})

    st.session_state.non_bibs_name = non_bibs.get("name", st.session_state.get("non_bibs_name", "Non-bibs FC"))
    st.session_state.non_bibs_players = ", ".join(non_bibs.get("players", st.session_state.get("non_bibs_players", "")))
    st.session_state.non_bibs_captain = non_bibs.get("captain", st.session_state.get("non_bibs_captain", ""))
    st.session_state.non_bibs_logo_text = non_bibs.get("logo", st.session_state.get("non_bibs_logo_text", "src/logos/Non-Bibs Logo.png"))

    st.session_state.bibs_name = bibs.get("name", st.session_state.get("bibs_name", "Bibs FC"))
    st.session_state.bibs_players = ", ".join(bibs.get("players", st.session_state.get("bibs_players", "")))
    st.session_state.bibs_captain = bibs.get("captain", st.session_state.get("bibs_captain", ""))
    st.session_state.bibs_logo_text = bibs.get("logo", st.session_state.get("bibs_logo_text", "src/logos/Bibs Logo.png"))

    video = config.get("video", {})
    main_video = video.get("main", {})
    st.session_state.video_path_text = main_video.get("path", st.session_state.get("video_path_text", "Game 1.mp4"))
    st.session_state.extend_clips = video.get("extend_clips", st.session_state.get("extend_clips", 0))

    cam2 = video.get("cam2", {})
    st.session_state.use_cam2 = cam2.get("enabled", st.session_state.get("use_cam2", False))
    st.session_state.cam2_time = cam2.get("time", st.session_state.get("cam2_time", 0.0))
    st.session_state.cam2_path_text = cam2.get("path", st.session_state.get("cam2_path_text", ""))
    st.session_state.cam2_overlap = cam2.get("overlap_px", st.session_state.get("cam2_overlap", 100))

    replays = video.get("replays", {})
    home_replay = replays.get("home", {})
    away_replay = replays.get("away", {})
    st.session_state.replays_h_time = home_replay.get("time", st.session_state.get("replays_h_time", 0.0))
    st.session_state.replays_h_path_text = home_replay.get("path", st.session_state.get("replays_h_path_text", ""))
    st.session_state.replays_a_time = away_replay.get("time", st.session_state.get("replays_a_time", 0.0))
    st.session_state.replays_a_path_text = away_replay.get("path", st.session_state.get("replays_a_path_text", ""))

    st.session_state.highlights_list = config.get("highlights", st.session_state.get("highlights_list", []))
    st.session_state.fix_scores_list = config.get("fix_scores", st.session_state.get("fix_scores_list", []))
    st.session_state.final_score_n = config.get("final_score", {}).get("n", st.session_state.get("final_score_n", 0))
    st.session_state.final_score_b = config.get("final_score", {}).get("b", st.session_state.get("final_score_b", 0))
    st.session_state.game_number = config.get("game_number", st.session_state.get("game_number", 1))
    st.session_state.use_fix_scores = config.get("settings", {}).get("use_fix_scores", bool(st.session_state.fix_scores_list))
    st.session_state.home_team = config.get("home_team", st.session_state.get("home_team", "Non-Bibs"))

    st.session_state.config_loaded_file = config.get("config_filename") or config.get("generated_at")


def save_session_config_file(filename=None):
    if filename is None or not filename.strip():
        filename = get_config_filename(st.session_state.get("game_number", 1))
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(build_config_data(), f, indent=2)
    st.session_state.last_config_path = filename
    return filename


st.sidebar.header("Session")
config_file = st.sidebar.file_uploader("Load session config JSON", type=["json"], key="config_file")
save_config_filename = st.sidebar.text_input("Session filename", value="", key="save_config_filename")
if st.sidebar.button("Save Session Config", key="save_config_btn"):
    try:
        saved_path = save_session_config_file(save_config_filename)
        st.sidebar.success(f"Config saved to {saved_path}")
    except Exception as e:
        st.sidebar.error(f"Unable to save config: {e}")

if config_file:
    if st.session_state.get("config_loaded_file") != getattr(config_file, "name", None):
        try:
            config = json.load(config_file)
            load_session_config(config)
            st.success("Config loaded from JSON")
        except Exception as e:
            st.error(f"Failed to load config: {e}")

# Initialize session state defaults
get_default_state("non_bibs_name", "Non-bibs FC")
get_default_state("non_bibs_players", "George, Gerald, Alex, Ben, Yaw, JC, Sam")
get_default_state("non_bibs_captain", "")
get_default_state("bibs_name", "Bibs FC")
get_default_state("bibs_players", "Manzan, Jason, Pavlos, Kevin, Aaron, Yi, Ringer")
get_default_state("bibs_captain", "")
get_default_state("non_bibs_logo_text", "src/logos/Non-Bibs Logo.png")
get_default_state("bibs_logo_text", "src/logos/Bibs Logo.png")
get_default_state("video_path_text", "Game 1.mp4")
get_default_state("game_number", 1)
get_default_state("extend_clips", 0)
get_default_state("highlights_list", [])
get_default_state("fix_scores_list", [])
get_default_state("final_score_n", 0)
get_default_state("final_score_b", 0)
get_default_state("use_cam2", False)
get_default_state("cam2_time", 0.0)
get_default_state("cam2_path_text", "")
get_default_state("cam2_overlap", 100)
get_default_state("replays_h_time", 0.0)
get_default_state("replays_h_path_text", "")
get_default_state("replays_a_time", 0.0)
get_default_state("replays_a_path_text", "")
get_default_state("use_fix_scores", False)
get_default_state("home_team", "Non-Bibs")
get_default_state("current_timestamp", 0.0)
get_default_state("edit_index", None)
get_default_state("edit_mode", None)
get_default_state("config_loaded_file", None)

st.sidebar.subheader("Team Setup")

# Non-Bibs Team
non_bibs_name = st.sidebar.text_input("Non-Bibs Team Name", value=st.session_state.non_bibs_name, key="non_bibs_name")
non_bibs_players = st.sidebar.text_area("Non-Bibs Players (comma-separated)", value=st.session_state.non_bibs_players, key="non_bibs_players")
non_bibs_captain = st.sidebar.selectbox("Non-Bibs Captain", parse_player_names(st.session_state.non_bibs_players), index=0 if st.session_state.non_bibs_captain in parse_player_names(st.session_state.non_bibs_players) else 0, key="non_bibs_captain")
non_bibs_logo_text = st.sidebar.text_input("Non-Bibs Logo Path", value=st.session_state.non_bibs_logo_text, key="non_bibs_logo_text")
non_bibs_logo = st.sidebar.file_uploader("Non-Bibs Logo Upload", type=["png", "jpg"], key="non_bibs_logo")

# Bibs Team
st.sidebar.subheader("Bibs Team")
bibs_name = st.sidebar.text_input("Bibs Team Name", value=st.session_state.bibs_name, key="bibs_name")
bibs_players = st.sidebar.text_area("Bibs Players (comma-separated)", value=st.session_state.bibs_players, key="bibs_players")
bibs_captain = st.sidebar.selectbox("Bibs Captain", parse_player_names(st.session_state.bibs_players), index=0 if st.session_state.bibs_captain in parse_player_names(st.session_state.bibs_players) else 0, key="bibs_captain")
bibs_logo_text = st.sidebar.text_input("Bibs Logo Path", value=st.session_state.bibs_logo_text, key="bibs_logo_text")
bibs_logo = st.sidebar.file_uploader("Bibs Logo Upload", type=["png", "jpg"], key="bibs_logo")

st.sidebar.subheader("Venue")
home_team = st.sidebar.selectbox("Home Team", ["Non-Bibs", "Bibs"], index=0 if st.session_state.home_team == "Non-Bibs" else 1, key="home_team")
away_team = "Bibs" if home_team == "Non-Bibs" else "Non-Bibs"
st.sidebar.write(f"Away Team: {away_team}")

# Video and Settings
st.header("Video Settings")
video_path_text = st.text_input("Main Video Path", value=st.session_state.video_path_text, key="video_path_text")
video_path = st.file_uploader("Upload Main Video", type=["mp4", "avi", "mov", "mkv"], key="video_path")
game_number = st.number_input("Game Number", 1, 10, value=st.session_state.game_number, key="game_number")
extend_clips = st.number_input("Extend Clips (seconds)", 0, 10, value=st.session_state.extend_clips, key="extend_clips")

def set_edit_state(idx):
    if idx >= len(st.session_state.highlights_list):
        return
    event = st.session_state.highlights_list[idx]
    st.session_state.edit_index = idx
    if "scored" in event:
        st.session_state.edit_mode = "goal"
        st.session_state.edit_time = event.get("time", 0.0)
        st.session_state.edit_goal_team = "Non-Bibs" if event.get("team") == "n" else "Bibs"
        st.session_state.edit_goal_scorer = event.get("scored", "")
        st.session_state.edit_goal_assist = event.get("assist", "None")
        st.session_state.edit_goal_replay = "Home" if event.get("replay") == "h" else "Away" if event.get("replay") == "a" else "None"
        st.session_state.edit_goal_start_offset = event.get("start_offset", 10.0)
        st.session_state.edit_goal_end_offset = event.get("end_offset", 5.0)
    else:
        st.session_state.edit_mode = "event"
        st.session_state.edit_time = event.get("time", 0.0)
        st.session_state.edit_event_type = event.get("text") if event.get("text") not in EVENT_TYPES else event.get("text")
        st.session_state.edit_custom_event_text = event.get("text", "") if event.get("text") not in EVENT_TYPES else ""
        st.session_state.edit_event_start_offset = event.get("start_offset", 10.0)
        st.session_state.edit_event_end_offset = event.get("end_offset", 5.0)
        if event.get("slow"):
            st.session_state.edit_event_type = "Zoom and Slowmo"
            st.session_state.edit_focal_x = event["slow"][0][0]
            st.session_state.edit_focal_y = event["slow"][0][1]
            st.session_state.edit_zoom_factor = event["slow"][2]
            st.session_state.edit_slowmo_factor = event["slow"][1]


def clear_edit_state():
    for key in [
        "edit_index", "edit_mode", "edit_time", "edit_goal_team", "edit_goal_scorer",
        "edit_goal_assist", "edit_goal_replay", "edit_goal_start_offset", "edit_goal_end_offset",
        "edit_event_type", "edit_custom_event_text", "edit_event_start_offset", "edit_event_end_offset",
        "edit_focal_x", "edit_focal_y", "edit_zoom_factor", "edit_slowmo_factor",
    ]:
        st.session_state.pop(key, None)
    st.session_state.edit_index = None
    st.session_state.edit_mode = None


# Display existing highlights
if st.session_state.highlights_list:
    st.subheader("Current Highlights")
    for idx, h in enumerate(st.session_state.highlights_list):
        col1, col2, col3 = st.columns([4, 1, 1])
        with col1:
            if "text" in h:
                st.write(f"**{h['time']}** - {h['text']}")
            else:
                scorer = h.get("scored", "Unknown")
                team = h.get("team", "?")
                team_name = "Non-Bibs" if team == "n" else "Bibs" if team == "b" else team
                assist = f" (assist: {h.get('assist', 'N/A')})" if h.get("assist") else ""
                replay = f" [Replay: {h.get('replay').upper()}]" if h.get("replay") else ""
                st.write(f"**{h['time']}** - {scorer} scores for {team_name}{assist}{replay}")
        with col2:
            if st.button("Edit", key=f"edit_{idx}", on_click=set_edit_state, args=(idx,)):
                pass
        with col3:
            if st.button("Delete", key=f"del_{idx}"):
                st.session_state.highlights_list.pop(idx)
                st.experimental_rerun()

if st.session_state.edit_index is not None:
    st.divider()
    st.subheader("Edit Highlight/Event")
    if st.session_state.edit_mode == "goal":
        edit_goal_time = st.number_input("Time (MM.SS format)", value=st.session_state.edit_time, step=0.01, key="edit_goal_time")
        edit_goal_team = st.selectbox("Scoring Team", ["Non-Bibs", "Bibs"], index=0 if st.session_state.edit_goal_team == "Non-Bibs" else 1, key="edit_goal_team")
        edit_goal_options = build_player_options(edit_goal_team, parse_player_names(st.session_state.non_bibs_players), parse_player_names(st.session_state.bibs_players)) or ["Select player"]
        edit_goal_scorer = st.selectbox("Player Who Scored", edit_goal_options, index=0 if st.session_state.edit_goal_scorer in edit_goal_options else 0, key="edit_goal_scorer")
        edit_assist_options = ["None"] + edit_goal_options
        edit_goal_assist = st.selectbox("Assisting Player (optional)", edit_assist_options, index=0 if st.session_state.edit_goal_assist in edit_assist_options else 0, key="edit_goal_assist")
        edit_goal_replay = st.selectbox("Include Replay", ["None", "Home", "Away"], index=["None", "Home", "Away"].index(st.session_state.edit_goal_replay if st.session_state.edit_goal_replay in ["None", "Home", "Away"] else "None"), key="edit_goal_replay")
        edit_goal_start_offset = st.number_input("Start Offset (seconds before)", value=st.session_state.edit_goal_start_offset, step=0.1, key="edit_goal_start_offset")
        edit_goal_end_offset = st.number_input("End Offset (seconds after)", value=st.session_state.edit_goal_end_offset, step=0.1, key="edit_goal_end_offset")
        if st.button("Save changes", key="save_edit_goal"):
            updated = {
                "time": edit_goal_time,
                "team": "n" if edit_goal_team == "Non-Bibs" else "b",
                "scored": edit_goal_scorer,
                "start_offset": edit_goal_start_offset,
                "end_offset": edit_goal_end_offset,
            }
            if edit_goal_assist and edit_goal_assist != "None":
                updated["assist"] = edit_goal_assist
            if edit_goal_replay != "None":
                updated["replay"] = "h" if edit_goal_replay == "Home" else "a"
            st.session_state.highlights_list[st.session_state.edit_index] = updated
            clear_edit_state()
            st.success("Highlight updated")
            st.experimental_rerun()
        if st.button("Cancel edit", key="cancel_edit_goal"):
            clear_edit_state()
            st.experimental_rerun()
    else:
        edit_event_time = st.number_input("Time (MM.SS format)", value=st.session_state.edit_time, step=0.01, key="edit_event_time")
        edit_event_type = st.selectbox("Event Type", EVENT_TYPES, index=EVENT_TYPES.index(st.session_state.edit_event_type) if st.session_state.edit_event_type in EVENT_TYPES else EVENT_TYPES.index("Custom Text"), key="edit_event_type")
        edit_custom_event_text = ""
        if edit_event_type == "Custom Text":
            edit_custom_event_text = st.text_input("Event Description", value=st.session_state.edit_custom_event_text, key="edit_custom_event_text")
        elif edit_event_type == "Zoom and Slowmo":
            edit_focal_x = st.slider("Focal X (0.0-1.0)", 0.0, 1.0, st.session_state.get("edit_focal_x", 0.5), key="edit_focal_x")
            edit_focal_y = st.slider("Focal Y (0.0-1.0)", 0.0, 1.0, st.session_state.get("edit_focal_y", 0.5), key="edit_focal_y")
            edit_zoom_factor = st.slider("Zoom Factor", 1.0, 5.0, st.session_state.get("edit_zoom_factor", 2.0), key="edit_zoom_factor")
            edit_slowmo_factor = st.slider("Slowmo Factor", 0.1, 1.0, st.session_state.get("edit_slowmo_factor", 0.5), key="edit_slowmo_factor")
        edit_event_start_offset = st.number_input("Start Offset (seconds before)", value=st.session_state.edit_event_start_offset, step=0.1, key="edit_event_start_offset")
        edit_event_end_offset = st.number_input("End Offset (seconds after)", value=st.session_state.edit_event_end_offset, step=0.1, key="edit_event_end_offset")
        if st.button("Save changes", key="save_edit_event"):
            text_value = edit_custom_event_text.strip() if edit_event_type == "Custom Text" else edit_event_type
            updated = {
                "time": edit_event_time,
                "text": text_value,
                "start_offset": edit_event_start_offset,
                "end_offset": edit_event_end_offset,
            }
            if edit_event_type == "Zoom and Slowmo":
                updated["slow"] = [[edit_focal_x, edit_focal_y], edit_slowmo_factor, edit_zoom_factor]
            st.session_state.highlights_list[st.session_state.edit_index] = updated
            clear_edit_state()
            st.success("Event updated")
            st.experimental_rerun()
        if st.button("Cancel edit", key="cancel_edit_event"):
            clear_edit_state()
            st.experimental_rerun()

st.divider()

# Add highlights with tabs
non_bibs_names = parse_player_names(non_bibs_players)
bibs_names = parse_player_names(bibs_players)

st.subheader("Timestamp helper")
st.write("Pause the main video and enter the paused timestamp below, then copy it into the goal or event form.")
current_timestamp = st.number_input("Paused timestamp (MM.SS)", value=st.session_state.current_timestamp, step=0.01, key="current_timestamp")
col1, col2 = st.columns(2)
if col1.button("Copy to Goal Time", key="copy_to_goal_time"):
    st.session_state.goal_time = current_timestamp
    st.experimental_rerun()
if col2.button("Copy to Event Time", key="copy_to_event_time"):
    st.session_state.event_time = current_timestamp
    st.experimental_rerun()

tab1, tab2 = st.tabs(["Add Goal", "Add Event/Text"])

with tab1:
    st.subheader("Add Goal Highlight")
    goal_time = st.number_input("Time (MM.SS format)", value=st.session_state.get("goal_time", 0.0), step=0.01, key="goal_time")
    goal_team = st.selectbox("Scoring Team", ["Non-Bibs", "Bibs"], index=0 if st.session_state.get("goal_team", "Non-Bibs") == "Non-Bibs" else 1, key="goal_team")
    goal_options = build_player_options(goal_team, non_bibs_names, bibs_names) or ["Select player"]
    goal_scorer = st.selectbox("Player Who Scored", goal_options, index=0 if st.session_state.get("goal_scorer") in goal_options else 0, key="goal_scorer")
    assist_options = ["None"] + goal_options
    goal_assist = st.selectbox("Assisting Player (optional)", assist_options, index=0 if st.session_state.get("goal_assist", "None") in assist_options else 0, key="goal_assist")
    goal_replay = st.selectbox("Include Replay", ["None", "Home", "Away"], index=["None", "Home", "Away"].index(st.session_state.get("goal_replay", "None")), key="goal_replay")
    goal_start_offset = st.number_input("Start Offset (seconds before)", value=st.session_state.get("goal_start_offset", 10.0), step=0.1, key="goal_start_offset")
    goal_end_offset = st.number_input("End Offset (seconds after)", value=st.session_state.get("goal_end_offset", 5.0), step=0.1, key="goal_end_offset")
    
    if st.button("Add Goal", key="add_goal_btn"):
        if goal_time >= 0 and goal_scorer and goal_scorer != "Select player":
            highlight = {
                "time": goal_time,
                "team": "n" if goal_team == "Non-Bibs" else "b",
                "scored": goal_scorer,
                "start_offset": goal_start_offset,
                "end_offset": goal_end_offset,
            }
            if goal_assist and goal_assist != "None":
                highlight["assist"] = goal_assist
            if goal_replay != "None":
                highlight["replay"] = "h" if goal_replay == "Home" else "a"
            
            st.session_state.highlights_list.append(highlight)
            st.success(f"✓ Added goal by {goal_scorer}")
            st.rerun()
        else:
            st.error("Please select a scorer and enter a valid time")

with tab2:
    st.subheader("Add Event/Text Annotation")
    event_time = st.number_input("Time (MM.SS format)", value=st.session_state.get("event_time", 0.0), step=0.01, key="event_time")
    event_type = st.selectbox("Event Type", EVENT_TYPES, index=EVENT_TYPES.index(st.session_state.get("event_type", "Kick-off")), key="event_type")
    
    event_text = ""
    if event_type == "Custom Text":
        event_text = st.text_input("Event Description", value=st.session_state.get("custom_event_text", ""), key="custom_event_text")
    elif event_type == "Zoom and Slowmo":
        event_text = "Zoom and Slowmo"
        focal_x = st.slider("Focal X (0.0-1.0)", 0.0, 1.0, st.session_state.get("focal_x", 0.5), key="focal_x")
        focal_y = st.slider("Focal Y (0.0-1.0)", 0.0, 1.0, st.session_state.get("focal_y", 0.5), key="focal_y")
        zoom_factor = st.slider("Zoom Factor", 1.0, 5.0, st.session_state.get("zoom_factor", 2.0), key="zoom_factor")
        slowmo_factor = st.slider("Slowmo Factor", 0.1, 1.0, st.session_state.get("slowmo_factor", 0.5), key="slowmo_factor")
    else:
        event_text = event_type
    
    event_start_offset = st.number_input("Start Offset (seconds before)", value=st.session_state.get("event_start_offset", 10.0), step=0.1, key="event_start_offset")
    event_end_offset = st.number_input("End Offset (seconds after)", value=st.session_state.get("event_end_offset", 5.0), step=0.1, key="event_end_offset")
    
    if st.button("Add Event", key="add_event_btn"):
        if event_time >= 0 and event_text.strip():
            highlight = {
                "time": event_time,
                "text": event_text.strip(),
                "start_offset": event_start_offset,
                "end_offset": event_end_offset,
            }
            if event_type == "Zoom and Slowmo":
                highlight["slow"] = [[focal_x, focal_y], slowmo_factor, zoom_factor]
            
            st.session_state.highlights_list.append(highlight)
            st.success(f"✓ Added event: {event_text}")
            st.rerun()
        else:
            st.error("Please fill in time and event description")

# Sort highlights by time
if st.session_state.highlights_list:
    st.session_state.highlights_list.sort(key=lambda x: x["time"])

# Optional: Cam2 and Replays
st.header("Optional Settings")
use_cam2 = st.checkbox("Use Cam2", value=st.session_state.get("use_cam2", False), key="use_cam2")
cam2_time = st.number_input("Cam2 Time", 0.0, step=0.01, value=st.session_state.get("cam2_time", 0.0), key="cam2_time") if use_cam2 else st.session_state.get("cam2_time", 0.0)
cam2_path_text = st.text_input("Cam2 Path", value=st.session_state.get("cam2_path_text", ""), key="cam2_path_text") if use_cam2 else st.session_state.get("cam2_path_text", "")
cam2_upload = st.file_uploader("Upload Cam2", type=["mp4", "avi", "mov", "mkv"], key="cam2_upload") if use_cam2 else None
cam2_overlap = st.number_input("Cam2 Overlap PX", 100, value=st.session_state.get("cam2_overlap", 100), key="cam2_overlap") if use_cam2 else st.session_state.get("cam2_overlap", 100)

replays_h_time = st.number_input("Replays Home Time", 0.0, step=0.01, value=st.session_state.get("replays_h_time", 0.0), key="replays_h_time")
replays_h_path_text = st.text_input("Replays Home Path", value=st.session_state.get("replays_h_path_text", ""), key="replays_h_path_text")
replays_h_upload = st.file_uploader("Upload Home Replay", type=["mp4", "avi", "mov", "mkv"], key="replays_h_upload")
replays_a_time = st.number_input("Replays Away Time", 0.0, step=0.01, value=st.session_state.get("replays_a_time", 0.0), key="replays_a_time")
replays_a_path_text = st.text_input("Replays Away Path", value=st.session_state.get("replays_a_path_text", ""), key="replays_a_path_text")
replays_a_upload = st.file_uploader("Upload Away Replay", type=["mp4", "avi", "mov", "mkv"], key="replays_a_upload")

if 'use_fix_scores' not in st.session_state:
    st.session_state.use_fix_scores = bool(st.session_state.get('fix_scores_list', []))

use_fix_scores = st.checkbox("Use Fix Scores", value=st.session_state.use_fix_scores, key="use_fix_scores")
if use_fix_scores:
    st.header("Fix Scores (Optional)")

    if st.session_state.fix_scores_list:
        st.subheader("Current Score Fixes")
        for idx, fs in enumerate(st.session_state.fix_scores_list):
            col1, col2 = st.columns([4, 1])
            with col1:
                team = "Non-Bibs" if fs["team"] == "n" else "Bibs"
                assist_str = f" (assist: {fs.get('assist', 'N/A')})" if fs.get("assist") else ""
                st.write(f"**{fs['time']}** - {fs['scored']} scores for {team}{assist_str}")
            with col2:
                if st.button("Delete", key=f"del_fix_{idx}"):
                    st.session_state.fix_scores_list.pop(idx)
                    st.experimental_rerun()

    st.divider()
    st.subheader("Add Score Fix")
    fix_time = st.number_input("Time (MM.SS format)", value=st.session_state.get("fix_time", 0.0), step=0.01, key="fix_time")
    fix_team = st.selectbox("Team", ["Non-Bibs", "Bibs"], index=0 if st.session_state.get("fix_team", "Non-Bibs") == "Non-Bibs" else 1, key="fix_team")
    fix_options = build_player_options(fix_team, non_bibs_names, bibs_names) or ["Select player"]
    fix_scorer = st.selectbox("Player Who Scored", fix_options, index=0 if st.session_state.get("fix_scorer") in fix_options else 0, key="fix_scorer")
    fix_assist_options = ["None"] + fix_options
    fix_assist = st.selectbox("Assisting Player (optional)", fix_assist_options, index=0 if st.session_state.get("fix_assist", "None") in fix_assist_options else 0, key="fix_assist")

    if st.button("Add Fix Score", key="add_fix_btn"):
        if fix_time >= 0 and fix_scorer and fix_scorer != "Select player":
            fix_score = {
                "time": fix_time,
                "team": "n" if fix_team == "Non-Bibs" else "b",
                "scored": fix_scorer,
            }
            if fix_assist and fix_assist != "None":
                fix_score["assist"] = fix_assist
            
            st.session_state.fix_scores_list.append(fix_score)
            st.success(f"✓ Added fix score for {fix_scorer}")
            st.rerun()
        else:
            st.error("Please select a scorer and enter a valid time")


# Final Score
final_score_n = st.number_input("Final Score Non-Bibs", 0, value=st.session_state.get("final_score_n", 0), key="final_score_n")
final_score_b = st.number_input("Final Score Bibs", 0, value=st.session_state.get("final_score_b", 0), key="final_score_b")

status_container = st.empty()
progress_bar = st.progress(0)


def resolve_input_path(path_input):
    if not path_input:
        return None

    path = Path(path_input)
    if path.is_absolute():
        return path

    # Accept both `src/logos/...` and `logos/...` when resolving in this app.
    normalized_path = path
    if normalized_path.parts and normalized_path.parts[0] == "src":
        normalized_path = Path(*normalized_path.parts[1:])

    # Try the app directory first, then current working directory.
    app_path = APP_DIR / normalized_path
    if app_path.exists():
        return app_path

    cwd_path = Path.cwd() / normalized_path
    if cwd_path.exists():
        return cwd_path

    # fallback to the raw path so the original function can raise a meaningful error
    return normalized_path


def update_progress(log_container, progress_bar, logs, message, progress=None):
    logs.append(message)
    log_container.markdown(f"```\n" + "\n".join(logs) + "\n```")
    if progress is not None:
        progress_bar.progress(progress)

if st.button("Generate and Preview Highlight Video"):
    if not st.session_state.highlights_list:
        st.error("Please add at least one highlight event")
    else:
        progress_bar = st.progress(0)
        status_container = st.empty()
        logs = []
        try:
            non_bibs_logo_path = non_bibs_logo.name if non_bibs_logo else (non_bibs_logo_text or str(DEFAULT_NON_BIBS_LOGO))
            bibs_logo_path = bibs_logo.name if bibs_logo else (bibs_logo_text or str(DEFAULT_BIBS_LOGO))
            non_bibs_team = {
                "name": non_bibs_name,
                "players": parse_player_names(non_bibs_players),
                "captain": non_bibs_captain,
                "logo": non_bibs_logo_path,
            }
            bibs_team = {
                "name": bibs_name,
                "players": parse_player_names(bibs_players),
                "captain": bibs_captain,
                "logo": bibs_logo_path,
            }

            if non_bibs_logo:
                with open(non_bibs_logo.name, "wb") as f:
                    f.write(non_bibs_logo.getbuffer())
            if bibs_logo:
                with open(bibs_logo.name, "wb") as f:
                    f.write(bibs_logo.getbuffer())

            highlights = st.session_state.highlights_list

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
            if use_cam2 and (cam2_upload or cam2_path_text):
                if cam2_upload:
                    cam2_file = cam2_upload.name
                    with open(cam2_file, "wb") as f:
                        f.write(cam2_upload.getbuffer())
                    resolved_cam2_path = cam2_file
                elif cam2_path_text:
                    resolved_cam2_path = resolve_input_path(cam2_path_text)
                    if not resolved_cam2_path or not resolved_cam2_path.exists():
                        raise FileNotFoundError(f"Cam2 video not found: {cam2_path_text}")

                cam2 = {"time": cam2_time, "path": str(resolved_cam2_path), "overlap_px": cam2_overlap}

            replays = None
            if replays_h_upload or replays_h_path_text or replays_a_upload or replays_a_path_text:
                if replays_h_upload:
                    replays_h_file = replays_h_upload.name
                    with open(replays_h_file, "wb") as f:
                        f.write(replays_h_upload.getbuffer())
                    resolved_replays_h = replays_h_file
                elif replays_h_path_text:
                    resolved_replays_h = resolve_input_path(replays_h_path_text)
                    if not resolved_replays_h or not resolved_replays_h.exists():
                        raise FileNotFoundError(f"Home replay not found: {replays_h_path_text}")
                else:
                    resolved_replays_h = None

                if replays_a_upload:
                    replays_a_file = replays_a_upload.name
                    with open(replays_a_file, "wb") as f:
                        f.write(replays_a_upload.getbuffer())
                    resolved_replays_a = replays_a_file
                elif replays_a_path_text:
                    resolved_replays_a = resolve_input_path(replays_a_path_text)
                    if not resolved_replays_a or not resolved_replays_a.exists():
                        raise FileNotFoundError(f"Away replay not found: {replays_a_path_text}")
                else:
                    resolved_replays_a = None

                if resolved_replays_h and resolved_replays_a:
                    replays = {
                        "time_h": replays_h_time,
                        "path_h": str(resolved_replays_h),
                        "time_a": replays_a_time,
                        "path_a": str(resolved_replays_a),
                    }

            fix_scores = st.session_state.fix_scores_list

            date_string = datetime.now().strftime("%Y%m%d")
            base_name = f"Game {game_number} highlights-{date_string}"
            version = 1
            while True:
                output_path = f"{base_name}-v{version}.mp4"
                config_path = f"{base_name}-v{version}.json"
                if not os.path.exists(output_path) and not os.path.exists(config_path):
                    break
                version += 1

            save_session_config_file(config_path)
            update_progress(status_container, progress_bar, logs, f"Saved current session config to {config_path}", 30)
            update_progress(status_container, progress_bar, logs, "Building highlight clip", 50)

            clip = compose_highlight_clip(
                str(resolved_video_path), highlights, non_bibs_team, bibs_team,
                extend_clips=extend_clips, game=game_number,
                fix_scores=fix_scores,
                final_score={"n": final_score_n, "b": final_score_b} if final_score_n or final_score_b else None,
                cam2=cam2, replays=replays,
            )

            update_progress(status_container, progress_bar, logs, "Rendering video at full quality", 70)
            start_time = time.time()
            clip.write_videofile(
                output_path,
                codec="libx264",
                fps=30,
                preset="medium",
                bitrate="2000k",
                audio=True,
                verbose=False,
            )
            elapsed_time = time.time() - start_time

            minutes = int(elapsed_time // 60)
            seconds = int(elapsed_time % 60)
            time_str = f"{minutes}m {seconds}s" if minutes > 0 else f"{seconds}s"

            update_progress(status_container, progress_bar, logs, f"Rendering complete - Time: {time_str}", 85)
            st.video(output_path)
            update_progress(status_container, progress_bar, logs, f"Saved to: {os.path.abspath(output_path)}", 100)
            update_progress(status_container, progress_bar, logs, f"Saved config to: {os.path.abspath(config_path)}", 100)
            st.success(f"✓ Video saved to: {os.path.abspath(output_path)} ({time_str})")
            st.session_state.last_video_path = output_path

        except Exception as e:
            st.error(f"Error: {str(e)}")

# Thumbnail Generation
st.header("Generate Thumbnail")
if st.button("Generate Thumbnail", key="generate_thumbnail"):
    try:
        # Use the last generated video or uploaded video
        video_for_thumb = st.session_state.get('last_video_path') or (video_path.name if video_path else video_path_text)
        if not video_for_thumb or not os.path.exists(video_for_thumb):
            st.error("No video available for thumbnail generation. Please generate a video first or provide a video path.")
        else:
            # Get logos
            non_bibs_logo_thumb = non_bibs_logo.name if non_bibs_logo else (non_bibs_logo_text or "logos/Non-Bibs Logo.png")
            bibs_logo_thumb = bibs_logo.name if bibs_logo else (bibs_logo_text or "logos/Bibs Logo.png")
            
            # Generate thumbnail
            thumbnail_path = f"thumbnail_game_{game_number}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            create_custom_thumbnail(
                video_for_thumb,
                bibs_logo_thumb,  # forest_logo_path (Bibs team)
                bibs_logo_thumb,
                non_bibs_logo_thumb,
                final_score_b,  # bib_score
                final_score_n,  # nonbib_score
                output_path=thumbnail_path
            )
            st.image(thumbnail_path, caption="Generated Thumbnail")
            st.success(f"✓ Thumbnail saved to: {os.path.abspath(thumbnail_path)}")
    except Exception as e:
        st.error(f"Error generating thumbnail: {str(e)}")
