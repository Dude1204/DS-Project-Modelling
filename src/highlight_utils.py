# highlight_utils.py
# Utility functions for creating football match highlight videos

import os
from pathlib import Path
import random
import datetime as dt
from collections import defaultdict

import numpy as np
import math
from PIL import Image, ImageDraw, ImageFont

from moviepy.editor import (
    VideoFileClip, TextClip, CompositeVideoClip, ColorClip,
    ImageClip, concatenate_videoclips, VideoClip, AudioClip, vfx
)
from moviepy.config import change_settings

# Configure ImageMagick path
change_settings({
    "IMAGEMAGICK_BINARY": r"C:\\Program Files\\ImageMagick-7.1.2-Q16-HDRI\\magick.exe"
})

# Constants
DEFAULT_FONT = "Arial"
DEFAULT_FONT_BOLD = "Arial-Bold"
DEFAULT_FPS = 25
DEFAULT_WIDTH, DEFAULT_HEIGHT = 1280, 720
BAR_HEIGHT = 110
SCOREBOARD_HEIGHT = 60
SCOREBOARD_PADDING = 10
SEG_LOGO = 120
SEG_SCORE = 200
SEG_LOGO2 = 120
THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT = 1280, 720
LEFT_PANEL_WIDTH = 500
RIGHT_PANEL_WIDTH = THUMBNAIL_WIDTH - LEFT_PANEL_WIDTH

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
FOREST_GREEN = (34, 85, 34)

# Font sizes
FONT_SIZE_LARGE = 70
FONT_SIZE_MEDIUM = 48
FONT_SIZE_SMALL = 36
FONT_SIZE_TINY = 30
FONT_SIZE_TIMER = 36
FONT_SIZE_THUMBNAIL_BIG = 150
FONT_SIZE_THUMBNAIL_MID = 60
FONT_SIZE_THUMBNAIL_SMALL = 30

# Durations
INTRO_DURATION = 5
SUMMARY_DURATION = 10
TEXT_FADE_DURATION = 0.3
PAUSE_DURATION = 5

# Other defaults
ZOOM_RATIO = 0.5
SLOWMO_FACTOR_DEFAULT = 0.5
ZOOM_FACTOR_DEFAULT = 2.0
OVERLAP_PX_DEFAULT = 100


def mm_ss_to_seconds(time_float, specific=True):
    """
    Converts time from MM.SS format to total seconds.
    Example: 1.51 → 111 seconds (1 min + 51 sec)
    """
    minutes = int(time_float)
    seconds = ((time_float - minutes) * 100) if specific else int((time_float - minutes) * 100)
    return minutes * 60 + seconds


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


class MatchTracker:
    """
    Generator to track match scores, goals, and assists.
    """

    def __init__(self, non_bibs_team_name, bibs_team_name):
        self.score = {non_bibs_team_name: 0, bibs_team_name: 0}
        self.player_goals = {non_bibs_team_name: {}, bibs_team_name: {}}
        self.player_assists = {non_bibs_team_name: {}, bibs_team_name: {}}
        self.last_scorer = None
        self.last_team = None
        self.non_bibs_team_name = non_bibs_team_name
        self.bibs_team_name = bibs_team_name

    def __iter__(self):
        return self

    def __next__(self):
        # Prime the generator
        self.team, self.scorer, self.assist, self.time = yield
        return self._process_event()

    def send(self, event):
        self.team, self.scorer, self.assist, self.time = event
        return self._process_event()

    def _process_event(self):
        if self.team not in self.score:
            raise ValueError(f"Team must be '{self.non_bibs_team_name}' or '{self.bibs_team_name}'")

        self.score[self.team] += 1
        minute = int(self.time)

        # Track goals
        if self.scorer not in self.player_goals[self.team]:
            self.player_goals[self.team][self.scorer] = []
        self.player_goals[self.team][self.scorer].append(f"{minute}'")

        # Track assists
        if self.assist:
            if self.scorer not in self.player_assists[self.team]:
                self.player_assists[self.team][self.scorer] = []
            self.player_assists[self.team][self.scorer].append(self.assist)

        # Mark the most recent scorer
        self.last_scorer = self.scorer
        self.last_team = self.team

        # Build output string
        output_lines = []
        for t in [self.non_bibs_team_name, self.bibs_team_name]:
            output_lines.append(f"{t}: {self.score[t]}")
            for player in self.player_goals[t]:
                times = ",".join(self.player_goals[t][player])
                assists = "".join(f"({a})" for a in self.player_assists[t].get(player, []))
                line = f"{player} {times} {assists}".strip()
                if player == self.last_scorer and t == self.last_team:
                    line = f">>> {line}"  # Highlight most recent
                output_lines.append(line)
            output_lines.append("")  # Blank line between teams

        return "\n".join(output_lines).strip()


def format_team(team):
    """
    Format player list with captain highlight.
    """
    lines = []
    for p in team["players"]:
        cap = " (C)" if p == team["captain"] else ""
        lines.append(f"{p}{cap}")
    return "\n".join(lines)


def team_header(name, logo_path, width):
    """
    Create a Premier League-style team header bar.
    """
    # Background bar
    bar = ColorClip(size=(width, BAR_HEIGHT), color=BLACK)

    # Logo
    logo = ImageClip(logo_path).resize((100, 100)).set_position((0, 0))

    # Team name
    text = TextClip(
        name,
        fontsize=FONT_SIZE_LARGE,
        color='white',
        font=DEFAULT_FONT_BOLD,
        method="label"
    ).set_position((130, 20))

    return CompositeVideoClip([bar, logo, text], size=(width, BAR_HEIGHT))


def create_team_intro(non_bibs_team, bibs_team, game=1):
    """
    Create the team introduction clip.
    """
    width, height = DEFAULT_WIDTH, DEFAULT_HEIGHT

    # Background
    bg = ColorClip(size=(width, height), color=BLACK).set_duration(INTRO_DURATION)

    # Left header (Non-Bibs)
    left_header = team_header(
        non_bibs_team["name"],
        non_bibs_team["logo"],
        width // 2
    ).set_position((0, 120)).set_duration(INTRO_DURATION)

    # Right header (Bibs)
    right_header = team_header(
        bibs_team["name"],
        bibs_team["logo"],
        width // 2
    ).set_position(((width + 150) // 2, 120)).set_duration(INTRO_DURATION)

    # Player lists
    left_text = format_team(non_bibs_team)
    right_text = format_team(bibs_team)

    left_clip = TextClip(
        left_text,
        fontsize=FONT_SIZE_MEDIUM,
        color='white',
        font=DEFAULT_FONT,
        method="caption",
        size=(width // 2 - 80, None)
    ).set_position((40, 260)).set_duration(INTRO_DURATION)

    right_clip = TextClip(
        right_text,
        fontsize=FONT_SIZE_MEDIUM,
        color='white',
        font=DEFAULT_FONT,
        method="caption",
        size=(width // 2 - 80, None)
    ).set_position((width // 2 + 40, 260)).set_duration(INTRO_DURATION)

    # Game heading
    heading = TextClip(
        f"Game {game}",
        fontsize=FONT_SIZE_LARGE,
        color='white',
        font=DEFAULT_FONT_BOLD,
        method="label"
    ).set_position(("center", 20)).set_duration(INTRO_DURATION)

    # Final composite
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
    """
    Create a summary clip of goals and assists.
    """
    goals = defaultdict(int)
    assists = defaultdict(int)

    for h in highlights:
        if "scored" in h and "OG" not in h["scored"]:
            goals[h["scored"]] += 1
        if "assist" in h:
            assists[h["assist"]] += 1

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

    # Create summary clip
    summary_clip = TextClip(
        summary_text, fontsize=FONT_SIZE_SMALL, color='white', font=DEFAULT_FONT,
        bg_color='black', size=[DEFAULT_WIDTH, DEFAULT_HEIGHT]
    ).set_duration(SUMMARY_DURATION).set_position("center").without_audio()

    return summary_clip


def zoom_in_to_point(image_clip, focal_x, focal_y, zoom_ratio=ZOOM_RATIO, fps=DEFAULT_FPS):
    """
    Create a zoom-in effect to a focal point.
    """
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


def create_replay_pause_zoom(video, start_time, end_time=0, pause_duration=PAUSE_DURATION, x=0.5, y=0.5):
    """
    Create a replay with pause and zoom effect.
    """
    # Extract replay segment
    if end_time == 0:
        end_time = start_time + 1
    replay_clip = video.subclip(start_time, end_time)

    # Freeze last frame
    pause_frame = replay_clip.to_ImageClip().set_duration(pause_duration)

    width, height = pause_frame.size
    focal_x = width * x
    focal_y = height * y

    zoomed = zoom_in_to_point(pause_frame.set_duration(pause_duration), focal_x, focal_y, fps=DEFAULT_FPS)

    # Avoid requesting a frame at the exact clip duration, which may be out of range.
    final_frame_time = max(0, pause_duration - 1.0 / DEFAULT_FPS)
    frozen_zoom = ImageClip(zoomed.get_frame(final_frame_time)).set_duration(pause_duration)

    # Stitch replay, pause, zoomed frame
    final_clip = concatenate_videoclips([pause_frame, zoomed, frozen_zoom])

    return final_clip


def zoom_and_slowmo(clip, focal_x, focal_y, zoom_factor=ZOOM_FACTOR_DEFAULT, slowmo_factor=SLOWMO_FACTOR_DEFAULT):
    """
    Apply zoom and slow-motion effect.
    """
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


def overlay_text(txt, duration, start_offset, stitched_height=DEFAULT_HEIGHT):
    """
    Create overlay text clip.
    """
    return (
        TextClip(txt, fontsize=FONT_SIZE_SMALL, color='white', font=DEFAULT_FONT_BOLD)
        .set_position(("center", "bottom"))
        .set_duration(duration)
        .set_start(start_offset)
        .fadein(TEXT_FADE_DURATION)
        .fadeout(TEXT_FADE_DURATION)
    )


def create_stitched_clip(video0, video2, overlap_px=OVERLAP_PX_DEFAULT):
    """
    Create a stitched clip from two videos with overlap.
    """
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


def create_scoreboard(team1, score1, team2, score2, logo1=None, logo2=None, height=SCOREBOARD_HEIGHT, duration=15, padding=SCOREBOARD_PADDING):
    """
    Create scoreboard elements.
    """
    elements = []

    # Dimensions
    BAR_HEIGHT = height + padding * 2

    # Segment widths
    SEG_LOGO = 120
    SEG_SCORE = 200
    SEG_LOGO2 = 120

    # Logo 1 (Bibs FC)
    if logo1 and os.path.exists(logo1):
        logo_clip1 = ImageClip(logo1).resize((75, 75)).set_duration(duration)
        logo_clip1 = logo_clip1.set_position(
            (25 + (SEG_LOGO - logo_clip1.w) // 2, padding - 10)
        )
        elements.append(logo_clip1)

    # Score text
    score_text = TextClip(
        f"{score1}  -  {score2}",
        fontsize=40,
        color='green',
        font=DEFAULT_FONT_BOLD
    ).set_duration(duration).set_position(
        (SEG_LOGO + (SEG_SCORE - 140) // 2, padding)
    )
    elements.append(score_text)

    # Logo 2 (Non-Bibs FC)
    if logo2 and os.path.exists(logo2):
        logo_clip2 = ImageClip(logo2).resize((75, 75)).set_duration(duration)
        logo_clip2 = logo_clip2.set_position(
            (-70 + SEG_LOGO + SEG_SCORE + (SEG_LOGO2 - logo_clip2.w) // 2, padding - 10)
        )
        elements.append(logo_clip2)

    return elements


def extract_scores_from_block(score_text, team1, team2):
    """
    Extract scores from scoreboard text block.
    """
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


def create_timer_clip(duration, base_time):
    """
    Create a timer clip that shows elapsed time.
    """
    def make_timer(t):
        current_time = base_time + int(t)
        minutes, seconds = divmod(int(current_time), 60)
        return TextClip(
            f"{minutes}:{seconds:02d}",
            fontsize=FONT_SIZE_TIMER,
            color='green',
            font=DEFAULT_FONT_BOLD,
            bg_color='white'
        ).get_frame(t)

    timer_txt = VideoClip(make_timer, duration=duration)
    timer_txt = timer_txt.set_position(("right", "top"))
    return timer_txt


def compose_highlight_clip(path, highlights, non_bibs_team, bibs_team, extend_clips=0, game=1, fix_scores=None, final_score=None, cam2=None, replays=None, insta=True):
    """
    Compose the highlight clip without writing it to disk.
    """
    if fix_scores is None or fix_scores == []:
        fix_scores = []
        final_score = None

    video0 = VideoFileClip(path)
    TARGET_SIZE = video0.size
    video2 = None
    time_diff = 0

    # Optional logos
    logo1 = non_bibs_team.get("logo")
    logo2 = bibs_team.get("logo")

    if cam2:
        time_diff = mm_ss_to_seconds(highlights[0].get("time", highlights[0].get("start"))) - mm_ss_to_seconds(cam2["time"])
        video2 = VideoFileClip(cam2["path"])

    if replays:
        ko = mm_ss_to_seconds(highlights[0].get("time", highlights[0].get("start")))
        time_diff_h = ko - mm_ss_to_seconds(replays["time_h"])
        time_diff_a = ko - mm_ss_to_seconds(replays["time_a"])
        video_h = VideoFileClip(replays["path_h"])
        video_a = VideoFileClip(replays["path_a"])

    team_intro = create_team_intro(non_bibs_team, bibs_team, game)
    team_dict = {"n": non_bibs_team['name'], "b": bibs_team['name']}
    tracker = MatchTracker(team_dict["n"], team_dict["b"])
    next(tracker)

    for score in fix_scores:
        tracker.send((team_dict[score["team"]], score["scored"], score.get("assist", ""), mm_ss_to_seconds(score["time"]) // 60))

    highlight_clips = []
    update_score = False
    scoreboard_elements = create_scoreboard(team_dict["n"], "0", team_dict["b"], "0", logo1, logo2, duration=15)
    scored = False
    once = False

    for i, h in enumerate(highlights):
        angle = h.get("angle", 0)
        video = video2 if angle == 1 and video2 else video0
        vid2 = video is video2

        adj = 0
        if insta and (h["time"] > 29) and not once and ("patch" not in h):
            adj = 15
            once = True
        time_diff -= h.get("time_adjustment", adj)
        if replays:
            time_diff_h -= h.get("time_adjustment", adj)
            time_diff_a -= h.get("time_adjustment", adj)

        start = mm_ss_to_seconds(h.get("start", h["time"])) - (h.get("start_offset", 10) if "start" not in h else 0) - extend_clips
        end = mm_ss_to_seconds(h.get("end", h["time"])) + (h.get("end_offset", 5) if "end" not in h else 0) + extend_clips
        start -= time_diff if vid2 else 0
        end -= time_diff if vid2 else 0
        extra_time = max(0, (end - start - 15) if "end" in h and "time" in h else 0)

        clip = video.subclip(start, end)
        text_duration = h.get("text_duration", 5)

        if "text" not in h:
            text = tracker.send((team_dict[h["team"]], h["scored"], h.get("assist", ""), mm_ss_to_seconds(h["time"]) // 60))
            final_scoreboard = text
            update_score = True
        else:
            text = h["text"]
            if any(tag in text for tag in ["Kick-off", "2nd Angle", "Replay", "Penalty"]):
                text_duration = clip.duration

        timer_txt = create_timer_clip(clip.duration, start + time_diff if vid2 else start)

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
            delay = mm_ss_to_seconds(h["time"]) - start

            scoreboard_elements_post = create_scoreboard(
                team_dict["n"], score1,
                team_dict["b"], score2,
                logo1, logo2,
                duration=clip.duration - delay
            )

            scoreboard_elements_pre = [sb.set_start(0).set_end(delay) for sb in scoreboard_elements_pre]
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
                    team_dict["n"], "0",
                    team_dict["b"], "0",
                    logo1, logo2,
                    duration=clip.duration
                )

        if "zoom" in h:
            focal_x, focal_y = h["zoom"]
            clip = create_replay_pause_zoom(video, mm_ss_to_seconds(h["time"], True), pause_duration=PAUSE_DURATION, x=focal_x, y=focal_y)
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
            if "patch" in h:
                time_diff_ha = time_diff_h if h["patch"] == "h" else time_diff_a
                video_ha = video_h if h["patch"] == "h" else video_a
                start -= time_diff_ha
                end -= time_diff_ha
                clip = video_ha.subclip(start, end)  # Replay is shorter and starts a bit later
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
                overlap_px = cam2.get("overlap_px", OVERLAP_PX_DEFAULT) if cam2 else OVERLAP_PX_DEFAULT

                clip = create_stitched_clip(clip2, clip1, overlap_px=overlap_px)
                clip = clip.resize(newsize=TARGET_SIZE)

            composite = CompositeVideoClip([clip, txt] + scoreboard_elements + [timer_txt])

        composite = composite.resize(newsize=TARGET_SIZE)
        highlight_clips.append(composite)

        if ("replay" in h) and replays:
            time_diff_ha = time_diff_h if h["replay"] == "h" else time_diff_a
            video_ha = video_h if h["replay"] == "h" else video_a

            time = mm_ss_to_seconds(h["time"]) - time_diff_ha

            clip = video_ha.subclip(time - 5, time + 3)  # Replay is shorter and starts a bit later

            silent_audio = AudioClip(lambda t: 0, duration=clip.duration, fps=44100)
            clip = clip.set_audio(silent_audio)
            txt = overlay_text("Replay", clip.duration, 0)
            composite = CompositeVideoClip([clip, txt])
            composite = composite.resize(newsize=TARGET_SIZE)
            highlight_clips.append(composite)

    if final_score:
        final_scoreboard = f"""{team_dict["n"]}: {final_score["n"]}, {team_dict["b"]}: {final_score["b"]}"""
        scoreboard_clip = TextClip(final_scoreboard, fontsize=FONT_SIZE_SMALL, color='white', font=DEFAULT_FONT, bg_color='black', size=video0.size)\
            .set_duration(SUMMARY_DURATION).set_position("center").without_audio()
        final_highlights = concatenate_videoclips([team_intro] + highlight_clips + [scoreboard_clip], method="compose")
    else:
        scoreboard_clip = TextClip(final_scoreboard.replace(">>>", ""), fontsize=FONT_SIZE_SMALL, color='white', font=DEFAULT_FONT, bg_color='black', size=video0.size)\
            .set_duration(SUMMARY_DURATION).set_position("center").without_audio()

        summary_clip = create_summary_clip(highlights + fix_scores).without_audio()

        final_highlights = concatenate_videoclips([team_intro] + highlight_clips + [scoreboard_clip, summary_clip], method="compose")

    return final_highlights


def create_highlight_clip(path, highlights, non_bibs_team, bibs_team, extend_clips=0, game=1, fix_scores=None, final_score=None, cam2=None, replays=None, insta=True):
    """
    Create and save the highlight video to disk.
    """
    final_highlights = compose_highlight_clip(
        path, highlights, non_bibs_team, bibs_team,
        extend_clips=extend_clips, game=game,
        fix_scores=fix_scores, final_score=final_score,
        cam2=cam2, replays=replays, insta=insta
    )
    save_to = get_unique_filepath(path.replace("..", "").replace("\\", "").replace(".mp4", f" Highlights - {str(dt.datetime.now())[:10]}.mp4"))
    final_highlights.write_videofile(save_to, codec="libx264", fps=DEFAULT_FPS)
    return save_to


def create_custom_thumbnail(video_path, forest_logo_path, bib_logo, nonbib_logo, bib_score, nonbib_score, output_path="thumbnail.jpg", frame_time=None):
    """
    Create a custom thumbnail for the video.
    """
    # Normalize and fallback for forest logo
    try:
        forest_logo_path = str(forest_logo_path) if forest_logo_path else ""
    except Exception:
        forest_logo_path = ""

    if not forest_logo_path or not os.path.exists(forest_logo_path):
        forest_logo_path = str(Path(__file__).resolve().parent / "logos" / "Random Forest Logo.png")

    # Extract frame from video for right side
    clip = VideoFileClip(video_path)
    if frame_time is None:
        frame_time = clip.duration * random.uniform(0.3, 0.7)
    frame = clip.get_frame(frame_time)
    right_img = Image.fromarray(frame).resize((RIGHT_PANEL_WIDTH, THUMBNAIL_HEIGHT))

    # Create left panel background
    left_panel = Image.new("RGBA", (LEFT_PANEL_WIDTH, THUMBNAIL_HEIGHT), FOREST_GREEN)
    overlay = Image.new("RGBA", left_panel.size, (0, 0, 0, 120))
    left_panel = Image.alpha_composite(left_panel, overlay)

    # Create base canvas
    canvas = Image.new("RGBA", (THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT))
    canvas.paste(left_panel, (0, 0))
    canvas.paste(right_img, (LEFT_PANEL_WIDTH, 0))

    draw = ImageDraw.Draw(canvas)

    # Fonts
    font_big = ImageFont.truetype("arialbd.ttf", FONT_SIZE_THUMBNAIL_BIG)
    font_mid = ImageFont.truetype("arialbd.ttf", FONT_SIZE_THUMBNAIL_MID)
    font_small = ImageFont.truetype("arialbd.ttf", FONT_SIZE_THUMBNAIL_SMALL)

    # Left side content
    # Random + logo + Forrest FC
    draw.text((85, 30), "Random", fill="white", font=font_small)

    forest_logo = Image.open(forest_logo_path).convert("RGBA").resize((150, 150))
    canvas.paste(forest_logo, (175, -10), forest_logo)

    draw.text((295, 30), "Forest FC", fill="white", font=font_small)

    # Highlights text
    draw.text((100, 100), "Highlights", fill="white", font=font_mid)

    # Bibs FC logo + score
    bib = Image.open(bib_logo).convert("RGBA").resize((250, 250))
    canvas.paste(bib, (30, 200), bib)
    draw.text((320, 250), str(bib_score), fill="white", font=font_big)

    # Non-Bibs FC logo + score
    nb = Image.open(nonbib_logo).convert("RGBA").resize((250, 250))
    canvas.paste(nb, (30, 450), nb)
    draw.text((320, 500), str(nonbib_score), fill="white", font=font_big)

    # Save
    canvas.convert("RGB").save(output_path, quality=95)
    return output_path


# ============================================================================
# PUSKAS AWARD CEREMONY FUNCTIONS
# ============================================================================

def create_ceremony_title_slide(duration=3):
    """
    Create a dramatic title slide for the Puskas Award Ceremony.
    """
    width, height = DEFAULT_WIDTH, DEFAULT_HEIGHT
    
    # Black background with gradient effect
    bg = ColorClip(size=(width, height), color=BLACK).set_duration(duration)
    
    # Main title
    title = TextClip(
        "PUSKAS AWARD",
        fontsize=100,
        color='gold',
        font=DEFAULT_FONT_BOLD,
        method="label"
    ).set_duration(duration).set_position(("center", height//3))
    
    # Subtitle
    subtitle = TextClip(
        "Best Goal of the Season",
        fontsize=50,
        color='white',
        font=DEFAULT_FONT,
        method="label"
    ).set_duration(duration).set_position(("center", height//2 + 50))
    
    # Add fade in/out effects
    title = title.crossfadeout(0.5).crossfadein(0.5)
    subtitle = subtitle.crossfadeout(0.5).crossfadein(0.5)
    
    return CompositeVideoClip([bg, title, subtitle], size=(width, height))


def create_contender_slide(player_name, team_name, goal_clip, rank, duration=4):
    """
    Create a contender presentation slide with goal video.
    
    Args:
        player_name: Name of the goal scorer
        team_name: Team name
        goal_clip: VideoFileClip of the goal
        rank: Contender number (1, 2, 3, etc)
        duration: Slide duration in seconds
    """
    width, height = DEFAULT_WIDTH, DEFAULT_HEIGHT
    
    # Resize goal clip to fit top portion
    video_height = int(height * 0.65)
    goal_video = goal_clip.resize(width=width).crop(
        x1=0, y1=0, x2=width, y2=video_height
    ).set_duration(duration)
    
    # Black bar for player info
    info_height = height - video_height
    info_bar = ColorClip(size=(width, info_height), color=BLACK).set_duration(duration)
    
    # Rank number (large)
    rank_text = TextClip(
        f"#{rank}",
        fontsize=80,
        color='gold',
        font=DEFAULT_FONT_BOLD,
        method="label"
    ).set_duration(duration).set_position((50, video_height + 20))
    
    # Player name
    player_text = TextClip(
        player_name,
        fontsize=60,
        color='white',
        font=DEFAULT_FONT_BOLD,
        method="label"
    ).set_duration(duration).set_position((250, video_height + 30))
    
    # Team name
    team_text = TextClip(
        team_name,
        fontsize=40,
        color='lightgray',
        font=DEFAULT_FONT,
        method="label"
    ).set_duration(duration).set_position((250, video_height + 100))
    
    # Combine all layers
    slide = CompositeVideoClip(
        [goal_video, info_bar, rank_text, player_text, team_text],
        size=(width, height)
    )
    
    return slide


def create_countdown_timer(start_num=5, duration=5.5):
    """
    Create a dramatic countdown timer (5, 4, 3, 2, 1, GO!).
    """
    width, height = DEFAULT_WIDTH, DEFAULT_HEIGHT
    
    # Black background
    bg = ColorClip(size=(width, height), color=BLACK).set_duration(duration)
    
    clips_to_combine = [bg]
    
    # Countdown numbers
    for i in range(start_num, 0, -1):
        time_in = (start_num - i) * 1.0
        time_out = time_in + 0.9
        
        number_text = TextClip(
            str(i),
            fontsize=200,
            color='gold',
            font=DEFAULT_FONT_BOLD,
            method="label"
        ).set_duration(duration).set_position(("center", "center")).set_start(time_in).set_end(time_out)
        
        clips_to_combine.append(number_text)
    
    # GO! text
    go_text = TextClip(
        "GO!",
        fontsize=150,
        color='white',
        font=DEFAULT_FONT_BOLD,
        method="label"
    ).set_duration(duration).set_position(("center", "center")).set_start(5.0).set_end(duration)
    
    clips_to_combine.append(go_text)
    
    return CompositeVideoClip(clips_to_combine, size=(width, height))


def create_winner_reveal(winner_name, team_name, winner_clip, duration=8):
    """
    Create a dramatic winner reveal with celebration effects.
    
    Args:
        winner_name: Name of the goal scorer
        team_name: Team name
        winner_clip: VideoFileClip of the winning goal
        duration: Total duration of reveal sequence
    """
    width, height = DEFAULT_WIDTH, DEFAULT_HEIGHT
    
    # Main video (full screen for first part)
    video_height = int(height * 0.7)
    winner_video = winner_clip.resize(width=width).crop(
        x1=0, y1=0, x2=width, y2=video_height
    ).set_duration(duration)
    
    # Black background for lower section
    lower_bg = ColorClip(size=(width, height - video_height), color=BLACK).set_duration(duration)
    lower_bg = lower_bg.set_position((0, video_height))
    
    # Trophy emoji/text
    trophy_text = TextClip(
        "🏆",
        fontsize=120,
        color='gold',
        font=DEFAULT_FONT_BOLD,
        method="label"
    ).set_duration(duration).set_position(("center", video_height + 20)).set_start(0.5)
    
    # Winner name with fade in
    winner_text = TextClip(
        f"{winner_name}",
        fontsize=80,
        color='gold',
        font=DEFAULT_FONT_BOLD,
        method="label"
    ).set_duration(duration).set_position(("center", video_height + 130)).crossfadein(0.5)
    
    # Team name
    team_text = TextClip(
        team_name,
        fontsize=50,
        color='white',
        font=DEFAULT_FONT,
        method="label"
    ).set_duration(duration).set_position(("center", video_height + 230)).crossfadein(0.5)
    
    # Congratulations text
    congrats_text = TextClip(
        "PUSKAS AWARD WINNER",
        fontsize=60,
        color='white',
        font=DEFAULT_FONT_BOLD,
        method="label"
    ).set_duration(duration).set_position(("center", height - 80)).set_start(3).crossfadein(0.5)
    
    return CompositeVideoClip(
        [winner_video, lower_bg, trophy_text, winner_text, team_text, congrats_text],
        size=(width, height)
    )


def create_puskas_ceremony(contenders_list, winner_index, output_path):
    """
    Create a complete Puskas Award Ceremony video.
    
    Args:
        contenders_list: List of dicts with structure:
            {
                "player_name": str,
                "team_name": str,
                "video_path": str,
                "start_time": float (in seconds),
                "duration": float (in seconds)
            }
        winner_index: Index of the winner in contenders_list (0-based)
        output_path: Output file path for the ceremony video
    """
    clips = []
    open_videos = []  # Keep track of open videos to close them later
    
    # Opening title slide
    print("Creating title slide...")
    title_slide = create_ceremony_title_slide(duration=3)
    clips.append(title_slide)
    
    # Add contender slides
    print("Creating contender slides...")
    for rank, contender in enumerate(contenders_list, 1):
        try:
            # Load goal clip
            goal_video = VideoFileClip(contender["video_path"])
            open_videos.append(goal_video)  # Track for cleanup
            
            video_duration = goal_video.duration
            
            # Get timing parameters
            start_time = contender.get("start_time", 0)
            clip_duration = contender.get("duration", 5)
            
            # Validate timing
            if start_time >= video_duration:
                print(f"⚠️  Warning: Start time {start_time}s is beyond video duration {video_duration:.1f}s for {contender['player_name']}")
                start_time = max(0, video_duration - clip_duration)
            
            # Ensure we don't go past the end
            end_time = min(start_time + clip_duration, video_duration)
            actual_duration = end_time - start_time
            
            if actual_duration < 0.5:
                print(f"⚠️  Warning: Adjusted duration to {actual_duration:.1f}s for {contender['player_name']}")
            
            # Extract the specific goal segment
            goal_segment = goal_video.subclip(start_time, end_time)
            
            # Create contender slide
            contender_slide = create_contender_slide(
                player_name=contender["player_name"],
                team_name=contender["team_name"],
                goal_clip=goal_segment,
                rank=rank,
                duration=4
            )
            clips.append(contender_slide)
            
            # Add pause between contenders
            pause = ColorClip(size=(DEFAULT_WIDTH, DEFAULT_HEIGHT), color=BLACK).set_duration(0.5)
            clips.append(pause)
            
        except Exception as e:
            print(f"❌ Error processing contender {rank} ({contender['player_name']}): {e}")
            print(f"   Video path: {contender['video_path']}")
            print(f"   Start time: {contender.get('start_time', 0)}s, Duration: {contender.get('duration', 5)}s")
            continue
    
    # Countdown to winner reveal
    print("Creating countdown...")
    countdown = create_countdown_timer(start_num=5, duration=5.5)
    clips.append(countdown)
    
    # Winner reveal
    print("Creating winner reveal...")
    winner_info = contenders_list[winner_index]
    try:
        winner_video = VideoFileClip(winner_info["video_path"])
        open_videos.append(winner_video)  # Track for cleanup
        
        video_duration = winner_video.duration
        
        # Get timing parameters
        start_time = winner_info.get("start_time", 0)
        clip_duration = winner_info.get("duration", 5)
        
        # Validate timing
        if start_time >= video_duration:
            print(f"⚠️  Warning: Start time {start_time}s is beyond video duration {video_duration:.1f}s for winner")
            start_time = max(0, video_duration - clip_duration)
        
        # Ensure we don't go past the end
        end_time = min(start_time + clip_duration, video_duration)
        winner_segment = winner_video.subclip(start_time, end_time)
        
        winner_reveal_clip = create_winner_reveal(
            winner_name=winner_info["player_name"],
            team_name=winner_info["team_name"],
            winner_clip=winner_segment,
            duration=8
        )
        clips.append(winner_reveal_clip)
        
    except Exception as e:
        print(f"❌ Error creating winner reveal: {e}")
        print(f"   Video path: {winner_info['video_path']}")
        print(f"   Start time: {winner_info.get('start_time', 0)}s, Duration: {winner_info.get('duration', 5)}s")
    
    # Concatenate all clips
    print("Concatenating all clips...")
    final_video = concatenate_videoclips(clips)
    
    # Write to file (video only, no audio)
    print(f"Writing ceremony video to {output_path}...")
    try:
        final_video.write_videofile(
            output_path,
            fps=DEFAULT_FPS,
            codec='libx264',
            audio=False,
            verbose=False,
            logger=None
        )
        print("✅ Ceremony video created successfully!")
    except Exception as e:
        print(f"❌ Error writing video: {e}")
        raise
    finally:
        # Clean up all open video files
        print("Cleaning up resources...")
        for vid in open_videos:
            try:
                vid.close()
            except:
                pass
    
    return output_path