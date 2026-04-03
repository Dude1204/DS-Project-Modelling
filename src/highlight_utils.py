from moviepy.editor import TextClip, CompositeVideoClip, ColorClip, concatenate_videoclips,VideoFileClip, VideoClip
from collections import defaultdict
import datetime as dt
from moviepy.config import change_settings

from moviepy.editor import VideoFileClip, concatenate_videoclips, vfx

from PIL import Image
import numpy as np
import math

from moviepy.editor import VideoClip
from PIL import Image
import numpy as np
import math

from moviepy.editor import VideoClip
from PIL import Image
import numpy as np
import math

change_settings({
    "IMAGEMAGICK_BINARY": r"C:\\Program Files\\ImageMagick-7.1.2-Q16-HDRI\\magick.exe"
})


def mm_ss_to_seconds(time_float,specific=True):
    """
    Converts time from MM.SS format to total seconds.
    Example: 1.51 → 111 seconds (1 min + 51 sec)
    """
    minutes = int(time_float)
    seconds = ((time_float - minutes) * 100) if specific else int((time_float - minutes) * 100)
    return minutes * 60 + seconds


def match_tracker(non_bibs_team_name, bibs_team_name):
    score = {non_bibs_team_name: 0, bibs_team_name: 0}
    player_goals = {non_bibs_team_name: {}, bibs_team_name: {}}
    player_assists = {non_bibs_team_name: {}, bibs_team_name: {}}
    last_scorer = None
    last_team = None

    team, scorer, assist, time = yield  # Prime the generator

    while True:
        if team not in score:
            raise ValueError(f"Team must be '{non_bibs_team_name}' or '{bibs_team_name}'")

        score[team] += 1
        minute = int(time)

        # Track goals
        if scorer not in player_goals[team]:
            player_goals[team][scorer] = []
        player_goals[team][scorer].append(f"{minute}'")

        # Track assists
        if assist:
            if scorer not in player_assists[team]:
                player_assists[team][scorer] = []
            player_assists[team][scorer].append(assist)

        # Mark the most recent scorer
        last_scorer = scorer
        last_team = team

        # Build output string
        output_lines = []
        for t in [non_bibs_team_name, bibs_team_name]:
            output_lines.append(f"{t}: {score[t]}")
            for player in player_goals[t]:
                times = ",".join(player_goals[t][player])
                assists = "".join(f"({a})" for a in player_assists[t].get(player, []))
                line = f"{player} {times} {assists}".strip()
                if player == last_scorer and t == last_team:
                    line = f">>> {line}"  # Highlight most recent
                output_lines.append(line)
            output_lines.append("")  # Blank line between teams

        output_text = "\n".join(output_lines).strip()

        # Wait for next input and yield output
        team, scorer, assist, time = yield output_text

def format_team(team):
    lines = [f"{team['name']}"]
    for p in team["players"]:
        label = " (Captain)" if p == team["captain"] else ""
        lines.append(f"{p}{label}")
    return "\n".join(lines)

from moviepy.editor import TextClip, ColorClip, CompositeVideoClip

def create_team_intro(non_bibs_team, bibs_team, game=1):
    # Video settings
    width, height = 1280, 720
    bg_color = 'black'
    duration = 5

    # Create clips for each team
    left_text = format_team(non_bibs_team)
    right_text = format_team(bibs_team)

    left_clip = TextClip(
        left_text,
        fontsize=48,
        color='white',
        font="Arial",
        method="caption",
        size=(width // 2 - 50, None),
        bg_color=bg_color
    ).set_position((50, height // 2 - 100)).set_duration(duration)

    right_clip = TextClip(
        right_text,
        fontsize=48,
        color='white',
        font="Arial",
        method="caption",
        size=(width // 2 - 50, None),
        bg_color=bg_color
    ).set_position((width // 2 + 50, height // 2 - 100)).set_duration(duration)

    # Game heading
    heading = TextClip(
        f"Game {game}",
        fontsize=60,
        color='white',
        font="Arial-Bold",
        method="label"
    ).set_position(("center", 50)).set_duration(duration)

    # Background
    bg = ColorClip(size=(width, height), color=(0, 0, 0)).set_duration(duration)

    # Compose final clip
    team_intro = CompositeVideoClip([bg, heading, left_clip, right_clip]).without_audio()
    return team_intro

def create_summary_clip(highlights, combined=False):
        # === Step 1: Count goals and assists ===

    goals = defaultdict(int)
    assists = defaultdict(int)

    for h in highlights:
        if "scored" in h:
            if "OG" not in h["scored"]:
                goals[h["scored"]] += 1
        if "assist" in h:
            assists[h["assist"]] += 1

    # === Step 2: Build summary text ===

    summary_lines = ["  Player Summary", ""]
    if combined:
        summary_lines = ["  Combined Goals and Assists", ""]

    # Combine goals and assists into a sortable list
    player_stats = []
    for player in set(goals.keys()) | set(assists.keys()):
        g = goals[player]
        a = assists[player]
        player_stats.append((g, a, player))  # Sort by goals, then assists

    # Sort descending by goals, then assists
    player_stats.sort(reverse=True)

    # Format summary lines
    for g, a, player in player_stats:
        summary_lines.append(f"{player}: {g} goal{'s' if g != 1 else ''}, {a} assist{'s' if a != 1 else ''}")

    summary_text = "\n".join(summary_lines)

    # === Step 3: Create summary clip ===
    summary_clip = TextClip(
        summary_text, fontsize=36, color='white', font="Arial", bg_color='black', size=[1280, 720]
    ).set_duration(15).set_position("center").without_audio()


    return summary_clip

def create_highlight_clip(path, highlights, non_bibs_team, bibs_team, extend_clips=0, game=1, fix_scores=[],final_score=None, cam2=None):
    video0 = VideoFileClip(path)
    TARGET_SIZE = video0.size   # (width, height)
    video2 = None
    time_diff = 0

    # Optional logos (paths or None)
    logo1 = non_bibs_team.get("logo")
    logo2 = bibs_team.get("logo")
    if cam2:
        time_diff = mm_ss_to_seconds(highlights[0].get("time", highlights[0].get("start"))) - mm_ss_to_seconds(cam2["time"])
        video2 = VideoFileClip(cam2["path"])

    team_intro = create_team_intro(non_bibs_team, bibs_team, game)
    team_dict = {"n": non_bibs_team['name'], "b": bibs_team['name']}
    tracker = match_tracker(team_dict["n"], team_dict["b"])
    next(tracker)

    for score in fix_scores:
        tracker.send((team_dict[score["team"]], score["scored"], score.get("assist", ""), mm_ss_to_seconds(score["time"]) // 60))

    highlight_clips = []
    update_score = False

    logo1 = non_bibs_team.get("logo")
    logo2 = bibs_team.get("logo")
    scoreboard_elements = create_scoreboard(team_dict["n"], "0", team_dict["b"], "0", logo1, logo2,duration=15)

    for i, h in enumerate(highlights):
        angle = h.get("angle", 0)
        video = video2 if angle == 1 and video2 else video0
        vid2 = video is video2

        time_diff -= h.get("time_adjustment", 0)

        start = mm_ss_to_seconds(h.get("start", h["time"])) - (10 if "start" not in h else 0) - extend_clips
        end = mm_ss_to_seconds(h.get("end", h["time"])) + (5 if "end" not in h else 0) + extend_clips
        start -= time_diff if vid2 else 0
        end -= time_diff if vid2 else 0
        extra_time = max(0, (end - start - 15) if "end" in h and "time" in h else 0)

        clip = video.subclip(start, end)
        text_duration = h.get("text_duration", 5)

        
        if "text" not in h:
            text = tracker.send((team_dict[h["team"]], h["scored"], h.get("assist", ""), mm_ss_to_seconds(h["time"]) // 60))
            final_scoreboard = text
            
            update_score=True

        else:
            text = h["text"]
            if any(tag in text for tag in ["Kick-off", "2nd Angle", "Replay", "Penalty"]):
                text_duration = clip.duration

        def make_timer(t, base=start + time_diff if vid2 else start):
            current_time = base + int(t)
            minutes, seconds = divmod(int(current_time), 60)
            return TextClip(f"{minutes}:{seconds:02d}", fontsize=36, color='white', font="Arial-Bold", bg_color='black')\
                .set_position((TARGET_SIZE[0] - 150, 10)).set_duration(clip.duration).get_frame(t)

        timer_txt = VideoClip(make_timer, duration=clip.duration)

        def overlay_text(txt, duration, start_offset):
            return TextClip(txt, fontsize=36, color='white', font="Arial-Bold")\
                .set_position(("center", "bottom")).set_duration(duration).set_start(start_offset)
        
        if update_score:
            update_score=False
            # Extract current score from tracker output
            print(f"Tracker output for scoreboard: {final_scoreboard}")
            score1, score2 = extract_scores_from_block(final_scoreboard, team_dict["n"], team_dict["b"])
            print(f"Extracted scores - {team_dict['n']}: {score1}, {team_dict['b']}: {score2}")

            #scoreboard_elements_pre = create_scoreboard(team1_name, score1_pre, team2_name, score2_pre, logo1, logo2)
            scoreboard_elements = create_scoreboard(team_dict["n"], score1, team_dict["b"], score2, logo1, logo2,duration=clip.duration)

        if "zoom" in h:
            focal_x, focal_y = h["zoom"]
            clip = create_replay_pause_zoom(video, mm_ss_to_seconds(h["time"], True), pause_duration=5, x=focal_x, y=focal_y)
            txt = overlay_text(text, 2, clip.duration - 5)

            if "Decision: Goal" in text:
                text = tracker.send((team_dict[h["team"]], h["scored"], h.get("assist", ""), mm_ss_to_seconds(h["time"]) // 60))
                final_scoreboard = text
                txt2 = overlay_text(text, 3, clip.duration - 3 - extra_time)
                composite = CompositeVideoClip([clip, txt, txt2])
            else:
                composite = CompositeVideoClip([clip, txt])

        elif "slow" in h:
            focal_x, focal_y = h["slow"][0]
            slowmo = h["slow"][1]
            zoom = h["slow"][2]
            clip = zoom_and_slowmo(clip, focal_x, focal_y, zoom_factor=zoom, slowmo_factor=slowmo)
            silent_audio = AudioClip(lambda t: 0, duration=clip.duration, fps=44100)
            clip = clip.set_audio(silent_audio)
            txt = overlay_text(text, 3, clip.duration - 3)
            composite = CompositeVideoClip([clip, txt])

        else:
            txt = overlay_text(text, text_duration, clip.duration - text_duration - extra_time)
            if angle == 2 and video2:
                # Clip1 from video0 (primary)
                start1 = mm_ss_to_seconds(h.get("start", h["time"])) - (10 if "start" not in h else 0) - extend_clips
                end1 = mm_ss_to_seconds(h.get("end", h["time"])) + (5 if "end" not in h else 0) + extend_clips
                clip1 = video0.subclip(start1, end1)

                # Clip2 from video2 (secondary), adjusted for time_diff
                start2 = start1 - time_diff
                end2 = end1 - time_diff
                clip2 = video2.subclip(start2, end2)
                overlap_px = cam2.get("overlap_px", 100) if cam2 else 100

                clip = create_stitched_clip(clip2,clip1, overlap_px=overlap_px)
                clip = clip.resize(newsize=TARGET_SIZE)

            composite = CompositeVideoClip([clip, txt, timer_txt]+ scoreboard_elements)

        composite = composite.resize(newsize=TARGET_SIZE)
        highlight_clips.append(composite)

    # print("\n--- DEBUG CLIP DURATIONS ---")
    # print("team_intro:", getattr(team_intro, "duration", None))

    # for idx, c in enumerate(highlight_clips):
    #     print(f"highlight clip {idx}:", getattr(c, "duration", None))

    # print("scoreboard_clip:", getattr(scoreboard_clip, "duration", None))

    # if not final_score:
    #     print("summary_clip:", getattr(summary_clip, "duration", None))

    # print("--- END DEBUG ---\n")
    if final_score:
        final_scoreboard=f"""{team_dict["n"]}: {final_score["n"]}, {team_dict["b"]}: {final_score["b"]}"""
        scoreboard_clip = TextClip(final_scoreboard, fontsize=36, color='white', font="Arial", bg_color='black', size=video.size)\
            .set_duration(10).set_position("center").without_audio()
        final_highlights = concatenate_videoclips([team_intro] + highlight_clips + [scoreboard_clip], method="compose")
    else:
        scoreboard_clip = TextClip(final_scoreboard.replace(">>>", ""), fontsize=36, color='white', font="Arial", bg_color='black', size=video.size)\
            .set_duration(10).set_position("center").without_audio()

        summary_clip = create_summary_clip(highlights + fix_scores).without_audio()

        final_highlights = concatenate_videoclips([team_intro] + highlight_clips + [scoreboard_clip, summary_clip], method="compose")
    save_to = get_unique_filepath(path.replace("..", "").replace("\\", "").replace(".mp4", f" Highlights - {str(dt.datetime.now())[:10]}.mp4"))
    final_highlights.write_videofile(save_to, codec="libx264", fps=25)

from moviepy.audio.fx.all import audio_normalize
def combine_highlights(path1,path2,highlight1,highlight2):
    """
    Combines highlights from a list of dictionaries into a single video.
    """
    # === Configure your match video ===
    video1 = mute_last_25_seconds(VideoFileClip(path1))
    video2 = mute_last_25_seconds(VideoFileClip(path2).fx(audio_normalize))
    summary_clip = create_summary_clip(highlight1 + highlight2, True)
    final_highlights = concatenate_videoclips([video1,video2, summary_clip], method="compose")
    save_to = f"Combined Highlights - {str(dt.datetime.now())[:10]}.mp4"
    final_highlights.write_videofile(save_to, codec="libx264", fps=25)

from moviepy.editor import VideoFileClip, AudioClip, concatenate_videoclips

def mute_last_25_seconds(video):
    """
    Loads a video, mutes the last 25 seconds, and saves the result.

    Parameters:
    - video_path: str, path to input video
    - output_path: str, path to save output video
    """
    duration = video.duration

    # Clamp if video is shorter than 25 seconds
    mute_duration = min(25, duration)

    # Split into two parts
    main_part = video.subclip(0, duration - mute_duration)
    silent_part = video.subclip(duration - mute_duration, duration)

    # Create silent audio for the last segment
    silent_audio = AudioClip(lambda t: 0, duration=mute_duration, fps=44100)
    silent_part = silent_part.set_audio(silent_audio)

    # Combine and export
    final = concatenate_videoclips([main_part, silent_part], method="compose")
    return final

def mute_segment(video_path, start_time, end_time):
    """
    Mutes a specific segment of the video from start_time to end_time.

    Parameters:
    - video: VideoFileClip, the video to mute
    - start_time: float, start time in seconds
    - end_time: float, end time in seconds

    Returns:
    - VideoFileClip with the specified segment muted
    """
    video = VideoFileClip(video_path)
    duration = video.duration

    # Clamp if video is shorter than the segment
    start_time = max(0, min(start_time, duration))
    end_time = max(start_time, min(end_time, duration))

    # Split into two parts
    main_part = video.subclip(0, start_time)
    silent_part = video.subclip(start_time, end_time)
    tail_part = video.subclip(end_time, duration)

    # Create silent audio for the segment
    silent_audio = AudioClip(lambda t: 0, duration=end_time - start_time, fps=44100)
    silent_part = silent_part.set_audio(silent_audio)

    # Combine and return
    final = concatenate_videoclips([main_part, silent_part, tail_part], method="compose")
    final.write_videofile("muted_video.mp4", codec="libx264", fps=25)

def cut_video(video_path, start_time, end_time, output_path=None):
    """
    Cuts a video from start_time to end_time and saves it to output_path.
    
    Parameters:
    - video_path: str, path to the input video file
    - start_time: float, start time in seconds
    - end_time: float, end time in seconds
    - output_path: str, path to save the cut video
    """
    video = VideoFileClip(video_path)
    end_time = video.duration - end_time
    video = video.subclip(start_time, end_time)
    if output_path is None:
        output_path = video_path.replace(".mp4", f" - {start_time}-{end_time}.mp4")
    video.write_videofile(output_path, codec="libx264", fps=25)

def combine_videos(video_paths, output_path=None):
    """
    Combines multiple videos into one.

    Parameters:
    - video_paths: list of str, paths to input video files
    - output_path: str, path to save the combined video
    """
    clips = [VideoFileClip(path) for path in video_paths]
    final_clip = concatenate_videoclips(clips, method="compose")
    
    if output_path is None:
        output_path = "combined_video.mp4"
    
    final_clip.write_videofile(output_path, codec="libx264", fps=25)

def zoom_in_to_point(image_clip, focal_x, focal_y, zoom_ratio=0.5, fps=25):
    def make_frame(t):
        img = Image.fromarray(image_clip.get_frame(t))
        base_w, base_h = img.size

        # Zoom scaling
        scale = 1 + zoom_ratio * t
        new_w = math.ceil(base_w * scale)
        new_h = math.ceil(base_h * scale)
        new_w += new_w % 2
        new_h += new_h % 2

        # Resize
        img = img.resize((new_w, new_h), Image.LANCZOS)

        # Compute crop centered on (focal_x, focal_y)
        x = int(focal_x * scale - base_w // 2)
        y = int(focal_y * scale - base_h // 2)

        # Clamp to image edges
        x = max(0, min(x, new_w - base_w))
        y = max(0, min(y, new_h - base_h))

        img = img.crop((x, y, x + base_w, y + base_h))
        return np.array(img)

    return VideoClip(make_frame, duration=image_clip.duration).set_fps(fps)

from moviepy.editor import ImageClip
def create_replay_pause_zoom(video, start_time, end_time=0,
                              pause_duration=5, x=0.5, y=0.5):

    # Extract replay segment
    if end_time == 0:
        end_time = start_time + 1
    replay_clip = video.subclip(start_time, end_time)

    # Freeze last frame
    pause_frame = replay_clip.to_ImageClip().set_duration(pause_duration)

    width, height = pause_frame.size
    focal_x = width * x  # right side
    focal_y = height * y  # middle

    zoomed = zoom_in_to_point(pause_frame.set_duration(pause_duration), focal_x, focal_y, fps=25)
    # Zoom-in effect (animated or static — toggle as needed)

    frozen_zoom = ImageClip(zoomed.get_frame(pause_duration)).set_duration(pause_duration)
    
    #frozen_zoom = zoomed.to_ImageClip().set_duration(pause_duration)

    # Stitch replay, pause, zoomed frame
    final_clip = concatenate_videoclips([pause_frame, zoomed, frozen_zoom])

    return final_clip


def zoom_and_slowmo(clip, focal_x, focal_y, zoom_factor=2.0, slowmo_factor=0.5):
    w, h = clip.size
    crop_w = w / zoom_factor
    crop_h = h / zoom_factor

    center_x = int(focal_x * w)
    center_y = int(focal_y * h)

    x1 = max(0, int(center_x - crop_w / 2))
    y1 = max(0, int(center_y - crop_h / 2))

    # Ensure crop doesn't exceed frame bounds
    x1 = min(x1, w - int(crop_w))
    y1 = min(y1, h - int(crop_h))

    zoomed = (
        clip
        .crop(x1=x1, y1=y1, width=int(crop_w), height=int(crop_h))
        .resize((w, h))
        .fx(vfx.speedx, slowmo_factor)
    )

    return zoomed

import os

def get_unique_filepath(filepath):
    """
    Returns a unique file path by appending version suffixes (v1, v2, ...) if the file already exists.
    """
    if not os.path.exists(filepath):
        return filepath

    base, ext = os.path.splitext(filepath)
    version = 1

    while True:
        new_filepath = f"{base}_v{version}{ext}"
        if not os.path.exists(new_filepath):
            return new_filepath
        version += 1


import os
from pathlib import Path

def get_mp4_files_by_creation(folder_path):
    """
    Returns a list of .mp4 file paths in the folder, sorted by creation time (oldest first).
    """
    folder = Path(folder_path)
    if not folder.is_dir():
        raise ValueError(f"{folder_path} is not a valid directory.")

    mp4_files = [f for f in folder.glob("*.mp4") if f.is_file()]
    sorted_files = sorted(mp4_files, key=lambda f: f.stat().st_ctime)
    return [str(f) for f in sorted_files]

from moviepy.editor import VideoFileClip, concatenate_videoclips

def combine_videos(video_folder, output_path="GoProVid.mp4"):
    """
    Combines a list of video file paths into one video in the given order.
    
    Parameters:
    - video_paths: List of strings, each a path to an .mp4 file
    - output_path: Path to save the combined video
    """
    video_paths = get_mp4_files_by_creation(video_folder)
    
    clips = []
    for path in video_paths:
        try:
            clip = VideoFileClip(path)
            clips.append(clip)
        except Exception as e:
            print(f"Error loading {path}: {e}")

    if not clips:
        raise ValueError("No valid video clips to combine.")

    final_clip = concatenate_videoclips(clips, method="compose")
    output_path = get_unique_filepath(output_path)
    final_clip.write_videofile(output_path, codec="libx264", audio_codec="aac",preset="ultrafast",threads=4)


from moviepy.editor import VideoFileClip, CompositeVideoClip, TextClip

def overlay_text(txt, duration, start_offset, stitched_height):
    return (
        TextClip(txt, fontsize=36, color='white', font="Arial-Bold")
        .set_position(("center", stitched_height - 80))  # Keeps text inside frame
        .set_duration(duration)
        .set_start(start_offset)
        .fadein(0.3)
        .fadeout(0.3)
    )

def create_stitched_clip(
    video0,
    video2,
    overlap_px=100, #350
):
    # Crop overlap
    left_cropped = video0.crop(x2=video0.w - overlap_px)
    right_cropped = video2.crop(x1=overlap_px)

    # Position right clip
    right_positioned = right_cropped.set_position((left_cropped.w, 0))

    # Stitch dimensions
    stitched_width = left_cropped.w + right_cropped.w
    stitched_height = max(left_cropped.h, right_cropped.h)

    # Combine clips
    stitched_clip = CompositeVideoClip(
        [left_cropped, right_positioned],
        size=(stitched_width, stitched_height)
    )

    return stitched_clip

from moviepy.editor import ImageClip, TextClip, ColorClip
import os

def create_scoreboard(team1, score1, team2, score2,
                      logo1=None, logo2=None,
                      height=60, duration=5, padding=10):

    elements = []

    # Width of the scoreboard bar
    bg_width = 600
    bg_height = height + padding*2

    # LEFT HALF = Black
    left_bg = ColorClip(size=(bg_width // 2, bg_height), color=(0, 0, 0)) \
                .set_duration(duration) \
                .set_position((0, 0))

    # RIGHT HALF = Black
    right_bg = ColorClip(size=(bg_width // 2, bg_height), color=(0, 0, 0)) \
                .set_duration(duration) \
                .set_position((bg_width // 2, 0))

    elements += [left_bg, right_bg]

    x_offset = padding

    # Team 1 logo (Non-bibs)
    if logo1 and os.path.exists(logo1):
        logo_clip1 = ImageClip(logo1).resize(height=height).set_duration(duration)
        logo_clip1 = logo_clip1.set_position((x_offset, padding))
        elements.append(logo_clip1)
        x_offset += logo_clip1.w + padding

    # Team 1 name + score
    t1 = TextClip(f"{team1} {score1}", fontsize=36, color='white', font="Arial") \
            .set_duration(duration) \
            .set_position((x_offset, padding))
    elements.append(t1)
    x_offset += t1.w + padding

    # Dash
    dash = TextClip("-", fontsize=36, color='white', font="Arial") \
            .set_duration(duration) \
            .set_position((x_offset, padding))
    elements.append(dash)
    x_offset += dash.w + padding

    # Team 2 name + score
    t2 = TextClip(f"{score2} {team2}", fontsize=36, color='white', font="Arial") \
            .set_duration(duration) \
            .set_position((x_offset, padding))
    elements.append(t2)
    x_offset += t2.w + padding

    # Team 2 logo (Bibs)
    if logo2 and os.path.exists(logo2):
        logo_clip2 = ImageClip(logo2).resize(height=height).set_duration(duration)
        logo_clip2 = logo_clip2.set_position((x_offset, padding))
        elements.append(logo_clip2)

    return elements

import re

def extract_scores_from_block(score_text, team1, team2):
    score1 = "0"
    score2 = "0"

    # Normalize whitespace
    cleaned = score_text.replace("\r", "").replace("\t", "")
    lines = [line.strip() for line in cleaned.split("\n") if line.strip()]

    # Look for "Team Name: X" in each line
    for line in lines:
        if line.startswith(team1 + ":"):
            score1 = line.split(":")[1].strip()
        elif line.startswith(team2 + ":"):
            score2 = line.split(":")[1].strip()

    return score1, score2