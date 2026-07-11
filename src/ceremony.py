"""
Puskas Award Ceremony Generator
Interactive Streamlit app for creating dramatic Puskas Award ceremony videos
"""

import streamlit as st
import json
import os
import tempfile
from pathlib import Path
from datetime import datetime
import json

from highlight_utils import create_puskas_ceremony, get_unique_filepath

APP_DIR = Path(__file__).resolve().parent

st.set_page_config(page_title="Puskas Award Ceremony", layout="wide")
st.title("🏆 Puskas Award Ceremony Generator")

# Initialize session state
if "contenders" not in st.session_state:
    st.session_state.contenders = []

if "winner_index" not in st.session_state:
    st.session_state.winner_index = 0


def add_contender(player_name, team_name, video_path, start_time, duration):
    """Add a new contender to the ceremony"""
    contender = {
        "player_name": player_name,
        "team_name": team_name,
        "video_path": video_path,
        "start_time": start_time,
        "duration": duration,
    }
    st.session_state.contenders.append(contender)
    st.success(f"✅ Added {player_name} to contenders!")


def remove_contender(index):
    """Remove a contender from the list"""
    removed = st.session_state.contenders.pop(index)
    st.info(f"Removed {removed['player_name']}")


# ============================================================================
# SIDEBAR - CONTENDER MANAGEMENT
# ============================================================================
with st.sidebar:
    st.header("📋 Manage Contenders")
    
    with st.expander("➕ Add New Contender", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            player_name = st.text_input("Player Name", key="player_name_input")
            team_name = st.text_input("Team Name", key="team_name_input")
        
        with col2:
            video_path = st.text_input("Video File Path", key="video_path_input", 
                                      help="Full path to video file (e.g., 'Game 1.mp4')")
        
        col3, col4 = st.columns(2)
        with col3:
            start_time = st.number_input("Start Time (seconds)", min_value=0.0, step=0.1, 
                                        key="start_time_input")
        
        with col4:
            duration = st.number_input("Duration (seconds)", min_value=1.0, max_value=30.0, 
                                      value=5.0, step=0.1, key="duration_input")
        
        if st.button("✅ Add Contender", use_container_width=True):
            if player_name and team_name and video_path:
                if os.path.exists(video_path):
                    add_contender(player_name, team_name, video_path, start_time, duration)
                else:
                    st.error(f"❌ Video file not found: {video_path}")
            else:
                st.error("Please fill in all fields")
    
    st.divider()
    
    # Display current contenders
    if st.session_state.contenders:
        st.subheader(f"Current Contenders ({len(st.session_state.contenders)})")
        
        for idx, contender in enumerate(st.session_state.contenders):
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.write(f"**#{idx + 1}** {contender['player_name']} ({contender['team_name']})")
                    st.caption(f"⏱️ {contender['start_time']}s → {contender['duration']}s")
                
                with col2:
                    if st.button("🏆 Winner", key=f"winner_{idx}", use_container_width=True):
                        st.session_state.winner_index = idx
                        st.success(f"✨ {contender['player_name']} selected as winner!")
                
                with col3:
                    if st.button("🗑️", key=f"delete_{idx}"):
                        remove_contender(idx)
                        st.rerun()
                
                st.divider()
    else:
        st.info("No contenders added yet. Add some goals to get started!")


# ============================================================================
# MAIN CONTENT - CEREMONY SETTINGS & GENERATION
# ============================================================================

if len(st.session_state.contenders) >= 2:
    st.success(f"✅ Ready! {len(st.session_state.contenders)} contenders registered")
    
    # Current winner info
    winner = st.session_state.contenders[st.session_state.winner_index]
    st.info(
        f"🏆 **Current Winner:** {winner['player_name']} ({winner['team_name']})",
        icon="🎯"
    )
    
    st.divider()
    
    # Ceremony Settings
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("⚙️ Ceremony Settings")
        
        # Ceremony name
        ceremony_name = st.text_input(
            "Ceremony Name",
            value=f"Puskas_Award_{datetime.now().strftime('%Y%m%d')}",
            help="Name for the output video"
        )
    
    with col2:
        st.subheader("👁️ Preview")
        st.write("**Contender Order:**")
        for idx, c in enumerate(st.session_state.contenders, 1):
            marker = "🏆" if idx - 1 == st.session_state.winner_index else "⚽"
            st.write(f"{marker} #{idx} - {c['player_name']} ({c['team_name']})")
    
    st.divider()
    
    # Generation settings
    st.subheader("🎬 Video Generation")
    
    gen_col1, gen_col2, gen_col3 = st.columns(3)
    
    with gen_col1:
        randomize_order = st.checkbox(
            "🔀 Randomize Contender Order",
            value=False,
            help="Show contenders in random order (winner will still be revealed last)"
        )
    
    with gen_col2:
        include_countdown = st.checkbox(
            "⏱️ Include Countdown",
            value=True,
            help="Show dramatic countdown before winner reveal"
        )
    
    with gen_col3:
        auto_open = st.checkbox(
            "📁 Open Output Folder",
            value=False,
            help="Open folder after video is generated"
        )
    
    st.divider()
    
    # Generate ceremony button
    if st.button("🚀 Generate Ceremony Video", use_container_width=True, type="primary"):
        
        # Prepare contenders list
        contenders_to_use = st.session_state.contenders.copy()
        winner_idx_to_use = st.session_state.winner_index
        print(f"Generating ceremony with {contenders_to_use} contenders, winner index: {winner_idx_to_use}")
        # Randomize if requested
        if randomize_order:
            import random
            non_winner_contenders = [c for i, c in enumerate(contenders_to_use) if i != winner_idx_to_use]
            winner_contender = contenders_to_use[winner_idx_to_use]
            random.shuffle(non_winner_contenders)
            contenders_to_use = non_winner_contenders + [winner_contender]
            winner_idx_to_use = len(non_winner_contenders)
        
        # Generate output path
        output_path = get_unique_filepath(f"{ceremony_name}.mp4")
        
        # Progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # Create the ceremony
            status_text.text("🎬 Generating ceremony video...")
            
            create_puskas_ceremony(
                contenders_list=contenders_to_use,
                winner_index=winner_idx_to_use,
                output_path=output_path
            )
            
            st.success(f"✨ Ceremony video created successfully!")
            st.info(f"📁 Saved to: `{output_path}`")
            
            # Display file info
            file_size = os.path.getsize(output_path) / (1024 * 1024)  # MB
            st.write(f"📊 File size: {file_size:.2f} MB")
            
            # Option to download
            with open(output_path, "rb") as f:
                st.download_button(
                    label="⬇️ Download Video",
                    data=f,
                    file_name=os.path.basename(output_path),
                    mime="video/mp4",
                    use_container_width=True
                )
            
            progress_bar.progress(100)
            
        except Exception as e:
            st.error(f"❌ Error generating ceremony: {str(e)}")
            import traceback
            st.code(traceback.format_exc())

else:
    st.warning(f"⚠️ Add at least 2 contenders to create a ceremony (current: {len(st.session_state.contenders)})")
    st.info("👈 Use the sidebar to add goal contenders")


# ============================================================================
# FOOTER - SAVED CEREMONIES
# ============================================================================
st.divider()

st.subheader("📹 Recent Ceremonies")

# Find recent ceremony videos
ceremony_videos = sorted(
    Path(".").glob("Puskas_Award_*.mp4"),
    key=os.path.getctime,
    reverse=True
)[:5]

if ceremony_videos:
    for video_path in ceremony_videos:
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            stat = os.stat(video_path)
            size_mb = stat.st_size / (1024 * 1024)
            created = datetime.fromtimestamp(stat.st_ctime).strftime("%Y-%m-%d %H:%M")
            st.write(f"📹 **{video_path.name}**")
            st.caption(f"Created: {created} | Size: {size_mb:.2f} MB")
        
        with col2:
            if st.button("▶️ Play", key=f"play_{video_path}"):
                st.video(str(video_path))
        
        with col3:
            if st.button("🗑️ Delete", key=f"del_{video_path}"):
                os.remove(video_path)
                st.success("Deleted!")
                st.rerun()
else:
    st.info("No ceremony videos created yet.")
