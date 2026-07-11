# Puskas Award Ceremony Generator

Create dramatic Puskas Award ceremony videos showcasing the best goals of the season!

## Quick Start

### Run the Ceremony App
```bash
streamlit run src/ceremony.py
```

The interactive UI will open at `http://localhost:8501`

## Features

### 🎬 Cinematic Video Generation
- **Title Slide**: Dramatic "PUSKAS AWARD" opening
- **Contender Showcase**: Each goal displayed with player info and ranking
- **Countdown**: 5-second dramatic countdown before the winner
- **Winner Reveal**: Triumphant winner announcement with celebration graphics

### 🎯 Interactive Management
- Add/remove contenders easily
- Set which player/goal wins the award
- Customize video timing and segments
- Preview contender order before generation

### ⚙️ Advanced Options
- **Randomize Order**: Show contenders in random sequence (winner always last)
- **Auto Countdown**: Include/exclude the dramatic countdown
- **Video Management**: View, play, and delete recent ceremonies

## How to Use

### 1. Add Contenders
In the sidebar, fill out the contender form:
- **Player Name**: Name of the goal scorer
- **Team Name**: Team they play for
- **Video File Path**: Full path to video file (e.g., `Game 1.mp4`)
- **Start Time**: Where the goal begins (in seconds)
- **Duration**: How long the goal clip is (typically 5 seconds)

Click **✅ Add Contender** to add it to the ceremony.

### 2. Select the Winner
Next to each contender, click the **🏆 Winner** button to select them as the award winner. Their goal will be revealed last with celebration effects.

### 3. Configure Settings
- **Ceremony Name**: Custom name for the output video
- **Randomize Order**: Optional - randomizes contender display order
- **Include Countdown**: Optional - adds dramatic 5-second countdown
- **Preview**: See the contender order before generation

### 4. Generate Video
Click **🚀 Generate Ceremony Video** to create your ceremony video.

The video will:
1. Open with a dramatic title slide
2. Show each contender in order with their goal
3. Include a countdown timer
4. Reveal the winner with celebration graphics
5. Save as `Puskas_Award_[name]-v[version].mp4`

## Video Timing Guide

### Finding Start Times and Durations

Use your video player to identify goal timestamps:

1. Open your video file in any player (VLC, Windows Media Player, etc.)
2. Pause at the moment before the ball is kicked
3. Note the timestamp as **Start Time**
4. Count forward ~5 seconds to include the celebration
5. Note the endpoint to calculate **Duration**

Example:
- Goal happens at 2:45 (2 minutes, 45 seconds)
- Start time: `165` seconds (2:45 in seconds)
- Duration: `5` seconds (includes goal + initial celebration)

### Tips
- **Start slightly before** the kick for better context
- **5-8 seconds** is typically a good goal duration
- Include the celebration reaction for drama
- Avoid overly long clips (keeps ceremony paced)

## Example Configuration

See `ceremony_example.json` for a sample ceremony setup with 3 contenders.

To load a saved ceremony:
1. Use the example as a template
2. Update video paths and timings
3. Add new contenders in the UI
4. Generate the video

## Output

Generated videos are saved in the workspace directory as:
```
Puskas_Award_[ceremony_name]-v[version].mp4
```

Each ceremony includes:
- High-quality video (1280x720 @ 25fps)
- Professional overlays and graphics
- Golden Puskas Award theming
- Dramatic music-ready format

## File Management

### View Recent Ceremonies
The app displays your 5 most recent ceremony videos with:
- Creation date
- File size
- Play button
- Delete option

### Download Videos
Click **⬇️ Download Video** after generation to download directly from the app.

## Troubleshooting

### "Video file not found" Error
- Ensure the video path is correct and absolute
- Check that the file exists in the specified location
- Use full paths: `C:\Users\YourName\Videos\Game1.mp4`

### Video Generation is Slow
- Processing time depends on video quality and duration
- Typical ceremony (3 contenders): 2-5 minutes
- Be patient - high quality takes time!

### Audio Issues
- Ceremony videos include all audio from source clips
- If you want silent videos, use video editing software

## Advanced: Batch Processing

For multiple ceremonies, you can modify the code to process a JSON config:

```python
import json
from highlight_utils import create_puskas_ceremony

with open("ceremony_example.json") as f:
    config = json.load(f)

create_puskas_ceremony(
    contenders_list=config["contenders"],
    winner_index=config["winner_index"],
    output_path=f"{config['ceremony_name']}.mp4"
)
```

## API Reference

### Direct Python Usage

```python
from highlight_utils import create_puskas_ceremony

contenders = [
    {
        "player_name": "Player Name",
        "team_name": "Team Name",
        "video_path": "path/to/video.mp4",
        "start_time": 45.5,  # seconds
        "duration": 5.0       # seconds
    },
    # ... more contenders
]

create_puskas_ceremony(
    contenders_list=contenders,
    winner_index=0,  # Index of winner in list
    output_path="ceremony_output.mp4"
)
```

### Available Functions

- `create_ceremony_title_slide(duration=3)` - Opening title
- `create_contender_slide(player_name, team_name, goal_clip, rank, duration=4)` - Contender presentation
- `create_countdown_timer(start_num=5, duration=5.5)` - Countdown sequence
- `create_winner_reveal(winner_name, team_name, winner_clip, duration=8)` - Winner announcement
- `create_puskas_ceremony(contenders_list, winner_index, output_path)` - Full ceremony

## Tips for Best Results

1. **Consistent Quality**: Use videos from the same source for cohesive look
2. **Good Angles**: Choose goals with clear camera angles and good lighting
3. **Clear Audio**: Ensure source videos have clear audio/commentary
4. **Diverse Goals**: Mix long-range, headers, free kicks, etc. for variety
5. **Test First**: Do a 3-contender ceremony before larger ones
6. **Timing**: Practice finding accurate start times for smooth playback

## Future Enhancements

Potential features to add:
- Custom music/soundtrack support
- Player portraits/stats overlays
- Vote counts/scores display
- Multiple languages for titles
- Custom color schemes (team colors)
- Social media export options

## Credits

Built with:
- **Streamlit**: Interactive UI
- **MoviePy**: Video processing
- **PIL**: Image manipulation

Enjoy creating dramatic Puskas Award ceremonies! 🏆⚽
