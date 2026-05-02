from moviepy.editor import TextClip, CompositeVideoClip, ColorClip, concatenate_videoclips,VideoFileClip, VideoClip
from collections import defaultdict
import datetime as dt
from moviepy.config import change_settings

from moviepy.editor import VideoFileClip, concatenate_videoclips, vfx

from PIL import Image
import numpy as np
import math

from PIL import Image
import numpy as np
import math
from moviepy.editor import ImageClip, VideoClip, AudioClip


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

from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, ColorClip, ImageClip
from PIL import Image
import random

# --- 1. Format player list (bullet points + captain highlight) ---
def format_team(team):
    lines = []
    for p in team["players"]:
        cap = " (C)" if p == team["captain"] else ""
        lines.append(f"{p}{cap}")
    return "\n".join(lines)


# --- 2. Premier League–style team header bar ---
def team_header(name, logo_path, width):
    bar_height = 110

    # Background bar
    bar = ColorClip(size=(width, bar_height), color=(0, 0, 0))

    # Logo
    # logo = ImageClip(logo_path).resize(height=90).set_position((20, 10))
    logo = ImageClip(logo_path).resize((100, 100)).set_position((0, 0))

    # Team name
    text = TextClip(
        name,
        fontsize=60,
        color='white',
        font="Arial-Bold",
        method="label"
    ).set_position((130, 20))

    return CompositeVideoClip([bar, logo, text], size=(width, bar_height))


# --- 3. Main intro generator ---
def create_team_intro(non_bibs_team, bibs_team, game=1):
    width, height = 1280, 720
    duration = 5

    # Background
    bg = ColorClip(size=(width, height), color=(0, 0, 0)).set_duration(duration)

    # --- Left header (Non‑Bibs) ---
    left_header = team_header(
        non_bibs_team["name"],
        non_bibs_team["logo"],
        width // 2
    ).set_position((0, 120)).set_duration(duration)

    # --- Right header (Bibs) ---
    right_header = team_header(
        bibs_team["name"],
        bibs_team["logo"],
        width // 2
    ).set_position(((width +150 )// 2, 120)).set_duration(duration)

    # --- Player lists ---
    left_text = format_team(non_bibs_team)
    right_text = format_team(bibs_team)

    left_clip = TextClip(
        left_text,
        fontsize=48,
        color='white',
        font="Arial",
        method="caption",
        size=(width // 2 - 80, None)
    ).set_position((40, 260)).set_duration(duration)

    right_clip = TextClip(
        right_text,
        fontsize=48,
        color='white',
        font="Arial",
        method="caption",
        size=(width // 2 - 80, None)
    ).set_position((width // 2 + 40, 260)).set_duration(duration)

    # --- Game heading ---
    heading = TextClip(
        f"Game {game}",
        fontsize=70,
        color='white',
        font="Arial-Bold",
        method="label"
    ).set_position(("center", 20)).set_duration(duration)

    # --- Final composite ---
    team_intro = CompositeVideoClip([
        bg,
        heading,
        left_header,
        right_header,
        left_clip,
        right_clip
    ]).without_audio()

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
    ).set_duration(10).set_position("center").without_audio()


    return summary_clip

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

    # Dimensions
    BAR_HEIGHT = height + padding * 2

    # Segment widths
    SEG_LOGO = 120
    SEG_SCORE = 200
    SEG_LOGO2 = 120

    # --- BACKGROUND SEGMENTS (NO BORDERS, TRANSPARENT) ---
    x = 0

    # --- LOGO 1 (Bibs FC) ---
    if logo1 and os.path.exists(logo1):
        logo_clip1 = ImageClip(logo1).resize((75, 75)).set_duration(duration)
        logo_clip1 = logo_clip1.set_position(
            (25 + (SEG_LOGO - logo_clip1.w) // 2, padding - 10)
        )
        elements.append(logo_clip1)

    # --- SCORE TEXT ---
    score_text = TextClip(
        f"{score1}  -  {score2}",
        fontsize=40,
        color='green',
        font="Arial-Bold"
    ).set_duration(duration).set_position(
        (SEG_LOGO + (SEG_SCORE - 140) // 2, padding)
    )
    elements.append(score_text)

    # --- LOGO 2 (Non‑Bibs FC) ---
    if logo2 and os.path.exists(logo2):
        logo_clip2 = ImageClip(logo2).resize((75, 75)).set_duration(duration)
        logo_clip2 = logo_clip2.set_position(
            (-70 + SEG_LOGO + SEG_SCORE + (SEG_LOGO2 - logo_clip2.w) // 2, padding - 10)
        )
        elements.append(logo_clip2)

    return elements



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


def create_highlight_clip(path, highlights, non_bibs_team, bibs_team, extend_clips=0, game=1, fix_scores=[],final_score=None, cam2=None, replays=None, insta=True):
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
    if replays:
        ko = mm_ss_to_seconds(highlights[0].get("time", highlights[0].get("start")))
        time_diff_h = ko- mm_ss_to_seconds(replays["time_h"])
        time_diff_a = ko - mm_ss_to_seconds(replays["time_a"])
        video_h = VideoFileClip(replays["path_h"])
        video_a = VideoFileClip(replays["path_a"])

    team_intro = create_team_intro(non_bibs_team, bibs_team, game)
    team_dict = {"n": non_bibs_team['name'], "b": bibs_team['name']}
    tracker = match_tracker(team_dict["n"], team_dict["b"])
    next(tracker)

    for score in fix_scores:
        tracker.send((team_dict[score["team"]], score["scored"], score.get("assist", ""), mm_ss_to_seconds(score["time"]) // 60))

    highlight_clips = []
    update_score = False

    scoreboard_elements = create_scoreboard(team_dict["n"], "0", team_dict["b"], "0", logo1, logo2,duration=15)
    scored = False
    once = False
    for i, h in enumerate(highlights):
        angle = h.get("angle", 0)
        video = video2 if angle == 1 and video2 else video0
        vid2 = video is video2

        adj=0
        
        if insta and (h["time"] > 28.57) and not once:
            adj = 15
            once = True
        time_diff -= h.get("time_adjustment", adj)
        time_diff_h -= h.get("time_adjustment", adj)
        time_diff_a -= h.get("time_adjustment", adj)

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

        # def make_timer(t, base=start + time_diff if vid2 else start):
        #     current_time = base + int(t)
        #     minutes, seconds = divmod(int(current_time), 60)
        #     return TextClip(
        #         f"{minutes}:{seconds:02d}",
        #         fontsize=36,
        #         color='white',
        #         font="Arial-Bold",
        #         bg_color='black'
        #     ).get_frame(t)

        # timer_txt = VideoClip(make_timer, duration=clip.duration)
        # timer_txt = timer_txt.set_position(("right", "top"))

        def make_timer(t, base=start + time_diff if vid2 else start):
            current_time = base + int(t)
            minutes, seconds = divmod(int(current_time), 60)
            return TextClip(
                f"{minutes}:{seconds:02d}",
                fontsize=36,
                color='green',          # GREEN TEXT
                font="Arial-Bold",
                bg_color='white'        # WHITE BACKGROUND
            ).get_frame(t)

        timer_txt = VideoClip(make_timer, duration=clip.duration)
        timer_txt = timer_txt.set_position(("right", "top"))


        def overlay_text(txt, duration, start_offset):
            return TextClip(txt, fontsize=36, color='white', font="Arial-Bold")\
                .set_position(("center", "bottom")).set_duration(duration).set_start(start_offset)
        
        if update_score:
            update_score = False
            scored = True

            score1, score2 = extract_scores_from_block(final_scoreboard, team_dict["n"], team_dict["b"])

            # PRE-GOAL SCOREBOARD (subtract 1 from scoring team)
            score1_pre = str(int(score1) - 1) if h["team"] == "n" else score1
            score2_pre = str(int(score2) - 1) if h["team"] == "b" else score2

            scoreboard_elements_pre = create_scoreboard(
                team_dict["n"], score1_pre,
                team_dict["b"], score2_pre,
                logo1, logo2,
                duration=clip.duration
            )
            # FIX: scoreboard switches exactly 10 seconds into the clip
            delay = mm_ss_to_seconds(h["time"]) - start

            scoreboard_elements_post = create_scoreboard(
                team_dict["n"], score1,
                team_dict["b"], score2,
                logo1, logo2,
                duration=clip.duration - delay
            )



            scoreboard_elements_pre = [sb.set_start(0) for sb in scoreboard_elements_pre]
            scoreboard_elements_pre = [sb.set_end(delay) for sb in scoreboard_elements_pre]
            scoreboard_elements_post = [sb.set_start(delay) for sb in scoreboard_elements_post]

            # Combine both
            scoreboard_elements = scoreboard_elements_pre + scoreboard_elements_post
        else:
            if scored:
                scoreboard_elements = create_scoreboard(
                    team_dict["n"], score1,
                    team_dict["b"], score2,
                    logo1, logo2,
                    duration=clip.duration
                )
            else:
                scoreboard_elements = create_scoreboard(
                    team_dict["n"], 0,
                    team_dict["b"], 0,
                    logo1, logo2,
                    duration=clip.duration
                )

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
        
        elif "patch" in h:
            txt = overlay_text(text, text_duration, clip.duration - text_duration - extra_time)
            time_diff_ha = time_diff_h if h["patch"] == "h" else time_diff_a
            video_ha = video_h if h["patch"] == "h" else video_a

            start -= time_diff_ha 
            end -= time_diff_ha

            clip = video_ha.subclip(start, end)  # Replay is shorter and starts a bit later

            composite = CompositeVideoClip([clip, txt] + scoreboard_elements + [timer_txt])

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

            composite = CompositeVideoClip([clip, txt] + scoreboard_elements + [timer_txt])

        composite = composite.resize(newsize=TARGET_SIZE)
        highlight_clips.append(composite)

        if ("replay" in h) and replays:
            time_diff_ha = time_diff_h if h["replay"] == "h" else time_diff_a
            video_ha = video_h if h["replay"] == "h" else video_a

            time = mm_ss_to_seconds(h["time"]) - time_diff_ha

            clip = video_ha.subclip(time - 5, time + 2)  # Replay is shorter and starts a bit later

            silent_audio = AudioClip(lambda t: 0, duration=clip.duration, fps=44100)
            clip = clip.set_audio(silent_audio)
            txt = overlay_text("Replay", clip.duration,0)
            composite = CompositeVideoClip([clip, txt])
            composite = composite.resize(newsize=TARGET_SIZE)
            highlight_clips.append(composite)


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

from moviepy.editor import VideoFileClip
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import random

def create_custom_thumbnail(
    video_path,
    forest_logo_path,
    bib_logo,
    nonbib_logo,
    bib_score,
    nonbib_score,
    output_path="thumbnail.jpg",
    frame_time=None,
):
    WIDTH, HEIGHT = 1280, 720
    LEFT_W = 500
    RIGHT_W = WIDTH - LEFT_W

    # --- 1. Extract frame from video for right side ---
    clip = VideoFileClip(video_path)
    if frame_time is None:
        frame_time = clip.duration * random.uniform(0.3, 0.7)
    frame = clip.get_frame(frame_time)
    right_img = Image.fromarray(frame).resize((RIGHT_W, HEIGHT))

    # --- 2. Create left panel background ---
    left_panel = Image.new("RGBA", (LEFT_W, HEIGHT), (34, 85, 34, 255))  # Forest green
    overlay = Image.new("RGBA", left_panel.size, (0, 0, 0, 120))
    left_panel = Image.alpha_composite(left_panel, overlay)

    # --- 3. Create base canvas ---
    canvas = Image.new("RGBA", (WIDTH, HEIGHT))
    canvas.paste(left_panel, (0, 0))
    canvas.paste(right_img, (LEFT_W, 0))

    draw = ImageDraw.Draw(canvas)

    # Fonts
    font_big = ImageFont.truetype("arialbd.ttf", 150)
    font_mid = ImageFont.truetype("arialbd.ttf", 60)
    font_small = ImageFont.truetype("arialbd.ttf", 30)

    # --- 4. Left side content ---
    # Random + logo + Forrest FC
    draw.text((85, 30), "Random", fill="white", font=font_small)

    forest_logo = Image.open(forest_logo_path).convert("RGBA").resize((150, 150))
    canvas.paste(forest_logo, (175, -10), forest_logo)

    draw.text((295, 30), "Forest FC", fill="white", font=font_small)

    # Highlights text
    draw.text((100, 100), "Highlights", fill="white", font=font_mid)

    # --- 5. Bibs FC logo + score ---
    bib = Image.open(bib_logo).convert("RGBA").resize((250, 250))
    canvas.paste(bib, (30, 200), bib)
    draw.text((320, 250), str(bib_score), fill="white", font=font_big)

    # --- 6. Non‑Bibs FC logo + score ---
    nb = Image.open(nonbib_logo).convert("RGBA").resize((250, 250))
    canvas.paste(nb, (30, 450), nb)
    draw.text((320, 500), str(nonbib_score), fill="white", font=font_big)

    # --- 7. Save ---
    canvas.convert("RGB").save(output_path, quality=95)
    return output_path