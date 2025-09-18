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


def mm_ss_to_seconds(time_float,specific=False):
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

def create_highlight_clip(path,highlights,non_bibs_team, bibs_team, extend_clips=0,game=1,fix_scores=[]):

    # === Configure your match video ===
    video = VideoFileClip(path)

    team_intro = create_team_intro(non_bibs_team, bibs_team,game)

    # === Create clips with score overlay ===
    highlight_clips = []
    # Create the generator
    team_dict = {
        "n": non_bibs_team['name'], "b": bibs_team['name']
    }
    tracker = match_tracker(team_dict["n"], team_dict["b"])
    next(tracker)
    for score in fix_scores:
        tracker.send((team_dict[score["team"]], score["scored"], score["assist"] if "assist" in score else "", mm_ss_to_seconds(score["time"]) // 60
        ))

    for i, h in enumerate(highlights):
        if "start" in h:
            start = mm_ss_to_seconds(h["start"]) - extend_clips
        else:
            start = mm_ss_to_seconds(h["time"]) - 10 - extend_clips
        
        if "end" in h:
            end = mm_ss_to_seconds(h["end"]) + extend_clips
        else:
            end = mm_ss_to_seconds(h["time"]) + 5 + extend_clips

        extra_time = max(0,(end - start - 15) if ("end" in h) and ("time" in h) else 0)
        clip = video.subclip(start, end)

        text_duration = h["text_duration"] if "text_duration" in h else 5
        
        # Create score text overlay

        if "text" not in h:
            text = tracker.send((team_dict[h["team"]], h["scored"], h["assist"] if "assist" in h else "", mm_ss_to_seconds(h["time"]) // 60
    ))
            final_scoreboard = text

        else:
            text = h["text"]
            if "Kick-off" in text:
                text_duration = clip.duration


        if "zoom" in h:
            focal_x, focal_y = h["zoom"]
            clip = create_replay_pause_zoom(video, mm_ss_to_seconds(h["time"],True), pause_duration=5, x=focal_x, y=focal_y)
            txt = TextClip(
                text, fontsize=36, color='white', font="Arial-Bold", bg_color='black'
                ).set_position(("center", "bottom")).set_duration(2).set_start(clip.duration - 5)
            
            if "Decision: Goal" in text:
                text = tracker.send((team_dict[h["team"]], h["scored"], h["assist"] if "assist" in h else "", mm_ss_to_seconds(h["time"]) // 60
                                     ))
                final_scoreboard = text

                txt2 = TextClip(
                text, fontsize=36, color='white', font="Arial-Bold"
                ).set_position(("center", "bottom")).set_duration(3).set_start(clip.duration - 3 - extra_time)
                composite = CompositeVideoClip([clip, txt, txt2])

            else:
                composite = CompositeVideoClip([clip, txt])
        elif "slow" in h:
            if len(h["slow"]) == 2:
                focal_x, focal_y = h["slow"]
                slowmo = 0.5
            else:
             focal_x, focal_y, slowmo = h["slow"]
            clip = zoom_and_slowmo(clip, focal_x, focal_y, zoom_factor=2.0, slowmo_factor=slowmo)
            txt = TextClip(
                text, fontsize=36, color='white', font="Arial-Bold"
                ).set_position(("center", "bottom")).set_duration(3).set_start(clip.duration - 3)
            
            composite = CompositeVideoClip([clip, txt])
        else:
            txt = TextClip(
                text, fontsize=36, color='white', font="Arial-Bold"
                ).set_position(("center", "bottom")).set_duration(text_duration).set_start(clip.duration - text_duration - extra_time)
            # Function to generate timer frame
            def make_timer(t, start_time=start):
                current_time = start_time + int(t)
                minutes = current_time // 60
                seconds = current_time % 60
                txt_clip = TextClip(
                    f"{minutes}:{seconds:02d}",
                    fontsize=36, color='white', font="Arial-Bold", bg_color='black'
                ).set_position(("left", "top")).set_duration(clip.duration)
                
                return txt_clip.get_frame(t)  # Return actual frame as NumPy array

            # Create dynamic timer clip
            timer_txt = VideoClip(make_timer, duration=clip.duration)
            composite = CompositeVideoClip([clip, txt, timer_txt])
        highlight_clips.append(composite)

    scoreboard_clip = TextClip(
        final_scoreboard.replace(">>>", ""), fontsize=36, color='white', font="Arial", bg_color='black', size=video.size
    ).set_duration(10).set_position("center").without_audio()

    summary_clip = create_summary_clip(highlights + fix_scores).without_audio()

        
    # === Concatenate all highlight clips ===

    final_highlights = concatenate_videoclips([team_intro] + highlight_clips + [scoreboard_clip, summary_clip],method="compose")
    save_to = path.replace("..","").replace("\\","").replace(".mp4",f" Highlights - {str(dt.datetime.now())[:10]}.mp4")
    save_to = get_unique_filepath(save_to)
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


def merge_highlight_dicts(highlights, extend_clips=0):
    overlaps = {}
    for i, h in enumerate(highlights):
        start = mm_ss_to_seconds(h["start"] if "start" in h else h["time"]) - 10 - extend_clips
        end = mm_ss_to_seconds(h["end"] if "end" in h else (h["time"] )) + 5 + extend_clips
        overlaps[i] = [start,end]
    
    return overlaps


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