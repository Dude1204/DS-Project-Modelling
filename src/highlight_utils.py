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

def create_highlight_clip(path,highlights,non_bibs_team, bibs_team, extend_clips=0,game=1):

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
    for i, h in enumerate(highlights):
        start = mm_ss_to_seconds(h["start"] if "start" in h else h["time"]) - 10 - extend_clips
        if "end" in h:
            end = mm_ss_to_seconds(h["end"]) + extend_clips
        else:
            end = mm_ss_to_seconds(h["time"]) + 5 + extend_clips

        extra_time = (end - start - 15) if ("end" in h) and ("time" in h) else 0
        clip = video.subclip(start, end)

        text_duration = h["text_duration"] if "text_duration" in h else 5

        if "start" in h:
            text_duration = clip.duration
        
        # Create score text overlay

        if "text" not in h:
            text = tracker.send((team_dict[h["team"]], h["scored"], h["assist"] if "assist" in h else "", mm_ss_to_seconds(h["time"]) // 60
    ))
            final_scoreboard = text

        else:
            text = h["text"]


        if "zoom" in h:
            focal_x, focal_y = h["zoom"]
            clip = create_replay_pause_zoom(video, mm_ss_to_seconds(h["time"],True), pause_duration=3, x=focal_x, y=focal_y)
            txt = TextClip(
                text, fontsize=36, color='white', font="Arial-Bold", bg_color='black'
                ).set_position(("center", "bottom")).set_duration(3).set_start(clip.duration - 3)
            
            composite = CompositeVideoClip([clip, txt])
        else:
            txt = TextClip(
                text, fontsize=36, color='white', font="Arial-Bold", bg_color='black'
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

    summary_clip = create_summary_clip(highlights)

        
    # === Concatenate all highlight clips ===

    final_highlights = concatenate_videoclips([team_intro] + highlight_clips + [scoreboard_clip, summary_clip])
    save_to = path.replace("..","").replace("\\","").replace(".mp4",f" Highlights - {str(dt.datetime.now())[:10]}.mp4")
    final_highlights.write_videofile(save_to, codec="libx264", fps=25)


def combine_highlights(path1,path2,highlight1,highlight2):
    """
    Combines highlights from a list of dictionaries into a single video.
    """
    # === Configure your match video ===
    video1 = VideoFileClip(path1)
    video2 = VideoFileClip(path2)
    summary_clip = create_summary_clip(highlight1 + highlight2, True)
    final_highlights = concatenate_videoclips([video1,video2, summary_clip])
    save_to = f"Combined Highlights - {str(dt.datetime.now())[:10]}.mp4"
    final_highlights.write_videofile(save_to, codec="libx264", fps=25)


def merge_highlight_dicts(highlights, extend_clips=0):
    overlaps = {}
    for i, h in enumerate(highlights):
        start = mm_ss_to_seconds(h["start"] if "start" in h else h["time"]) - 10 - extend_clips
        end = mm_ss_to_seconds(h["end"] if "end" in h else (h["time"] )) + 5 + extend_clips
        overlaps[i] = [start,end]
    
    return overlaps


def zoom_in_to_point(image_clip, focal_x, focal_y, zoom_ratio=0.8, fps=25):
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
                              pause_duration=3, x=0.5, y=0.5):

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