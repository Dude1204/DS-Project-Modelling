from moviepy.editor import TextClip, CompositeVideoClip, ColorClip, concatenate_videoclips,VideoFileClip, VideoClip
from collections import defaultdict
import datetime as dt
from moviepy.config import change_settings

change_settings({
    "IMAGEMAGICK_BINARY": r"C:\\Program Files\\ImageMagick-7.1.2-Q16-HDRI\\magick.exe"
})


def mm_ss_to_seconds(time_float):
    """
    Converts time from MM.SS format to total seconds.
    Example: 1.51 → 111 seconds (1 min + 51 sec)
    """
    minutes = int(time_float)
    seconds = int(round((time_float - minutes) * 100))
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

def create_team_intro(non_bibs_team, bibs_team):
    # Video settings
    width, height = 1280, 720
    bg_color = 'black'
    duration = 5

    # Create team clips
    text = format_team(non_bibs_team) + "\n\n" + format_team(bibs_team)

    txt_clip = TextClip(
        text,
        fontsize=36,
        color='white',
        font="Arial",
        method="caption",
        size=(width - 100, None),
        bg_color=bg_color
    ).set_position("center").set_duration(duration)

    # Optional: solid background clip
    bg = ColorClip(size=(width, height), color=(0, 0, 0)).set_duration(duration)

    # Combine
    team_intro = CompositeVideoClip([bg, txt_clip])

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
    ).set_duration(15).set_position("center")

    return summary_clip

def create_highlight_clip(path,highlights,non_bibs_team, bibs_team, extend_clips=0):

    # === Configure your match video ===
    video = VideoFileClip(path)

    team_intro = create_team_intro(non_bibs_team, bibs_team)

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
        end = mm_ss_to_seconds(h["end"] if "end" in h else (h["time"] )) + 5 + extend_clips
        clip = video.subclip(start, end)
        
        # Create score text overlay

        if "text" not in h:
            text = tracker.send((team_dict[h["team"]], h["scored"], h["assist"] if "assist" in h else "", mm_ss_to_seconds(h["time"]) // 60
    ))
            final_scoreboard = text
            text_duration = h["text_duration"] if "text_duration" in h else 5
        else:
            text = h["text"]
            text_duration = h["text_duration"] if "text_duration" in h else clip.duration

        
        txt = TextClip(
            text, fontsize=36, color='white', font="Arial-Bold", bg_color='black'
        ).set_position(("center", "bottom")).set_duration(text_duration).set_start(clip.duration - text_duration)

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
    ).set_duration(10).set_position("center")

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
    summary_clip = create_summary_clip(highlight1 + highlight2)
    final_highlights = concatenate_videoclips([video1,video2, summary_clip])
    save_to = f"Combined Highlights - {str(dt.datetime.now())[:10]}.mp4"
    final_highlights.write_videofile(save_to, codec="libx264", fps=25)