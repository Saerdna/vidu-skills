# Video Compose Reference

Compose a multi-track timeline into a single exported video.

---

## CLI Commands

### Submit compose

```bash
vidu-cli task compose \
  --timeline <file_path_or_json_string> \
  [--width 1920] \
  [--height 1080]
```

All output flags are optional. If omitted, the server decides.

`--timeline` accepts either a JSON file path or an inline JSON string. The CLI auto-detects which.

Returns: `{"ok": true, "task_id": "...", "trace_id": "..."}`

### Query compose job

```bash
vidu-cli task get <task_id>
```

Uses the `task_id` returned by `task compose`. Same as querying any other task.

---

## media_url Rules

The CLI automatically normalizes `media_url` and `file_url` fields in the timeline before sending:

**media_url** (video/image clips):

| Input format | Behavior |
|---|---|
| `ssupload:?id=xxx` | Pass through |
| `http(s)://...` | Pass through (treated as valid remote URL) |
| Local file path | Upload → `ssupload:?id=...` |

**file_url** (subtitle files, e.g. .srt):

| Input format | Behavior |
|---|---|
| `ssupload:?id=xxx` | Pass through |
| `http(s)://...` | Pass through |
| Local file path | Upload → `ssupload:?id=...` |

For local files and http URLs (image/video), the CLI validates before upload:
- File size: image ≤ 50MB, video ≤ 500MB
- Dimensions: width and height must be 128–4096 px, short side ≤ 2160 px

---

## Limits

- Each track type (video, audio, subtitle, effect) is limited to 100 tracks maximum.

---

## Timeline JSON Schema

Top-level structure:

```json
{
  "video_tracks": [],
  "audio_tracks": [],
  "subtitle_tracks": [],
  "effect_tracks": []
}
```

### VideoTrack

| Field | Type | Description |
|-------|------|-------------|
| `type` | string | Track type |
| `main_track` | boolean | Whether this is the main track |
| `track_shorten_mode` | string | `AutoSpeed` — auto-accelerate when exceeding main track |
| `track_expand_mode` | string | `AutoSpeed` — auto-decelerate when shorter than main track |
| `video_track_clips` | VideoTrackClip[] | Clips on this track |

### VideoTrackClip

| Field | Type | Description |
|-------|------|-------------|
| `media_url` | string | Media reference (see media_url rules above) |
| `type` | string | `Video`, `Image`, `GlobalImage` |
| `x`, `y` | float | Position. [0-0.9999] = percentage, ≥2 = pixels |
| `width`, `height` | float | Size. Same format as x/y |
| `adapt_mode` | string | `Contain`, `Cover`, `Fill` (default) |
| `in` | float | Entry point in source material (seconds) |
| `out` | float | Exit point in source material (seconds) |
| `duration` | float | Clip duration (for images) |
| `timeline_in` | float | Start position on timeline |
| `timeline_out` | float | End position on timeline |
| `speed` | float | Playback speed (0.1-100) |
| `opacity` | float | 0 (transparent) to 1 (opaque) |
| `effects` | Effect[] | Effects applied to this clip |

### AudioTrack

| Field | Type | Description |
|-------|------|-------------|
| `main_track` | boolean | Whether this is the main track |
| `track_shorten_mode` | string | `AutoSpeed` |
| `track_expand_mode` | string | `AutoSpeed` |
| `audio_track_clips` | AudioTrackClip[] | Clips on this track |

### AudioTrackClip

| Field | Type | Description |
|-------|------|-------------|
| `media_url` | string | Media reference |
| `type` | string | Default audio; use `AI_TTS` for text-to-speech |
| `content` | string | Text content (for AI_TTS) |
| `voice` | string | Voice type (for AI_TTS) |
| `in`, `out` | float | Trim points (seconds) |
| `timeline_in`, `timeline_out` | float | Timeline positioning |
| `speed` | float | Playback speed (0.1-100) |
| `loop_mode` | boolean | Loop playback |
| `effects` | Effect[] | Effects applied to this clip |

### SubtitleTrack

| Field | Type | Description |
|-------|------|-------------|
| `subtitle_track_clips` | SubtitleTrackClip[] | Clips on this track |

### SubtitleTrackClip

| Field | Type | Description |
|-------|------|-------------|
| `type` | string | `Subtitle` (external file) or `Text` (inline text) |
| `sub_type` | string | `srt` or `ass` (for external subtitles) |
| `file_url` | string | External subtitle file URL (for Subtitle type) |
| `content` | string | Text content (for Text type) |
| `font` | string | Font name (default: SimSun) |
| `font_size` | int | 0-5000 |
| `font_color` | string | Hex `#RRGGBB` |
| `font_color_opacity` | float | 0-1 |
| `font_face` | object | `{ bold, italic, underline }` (booleans) |
| `x`, `y` | float | Position |
| `timeline_in`, `timeline_out` | float | Display duration |
| `alignment` | string | TopLeft, TopCenter, TopRight, CenterLeft, CenterCenter, CenterRight, BottomLeft, BottomCenter, BottomRight |
| `adapt_mode` | string | AutoWrap, AutoScale, AutoWrapAtSpaces |
| `spacing` | int | Character spacing (pixels) |
| `line_spacing` | int | Line spacing (pixels) |
| `angle` | float | Rotation degrees |

### EffectTrack

| Field | Type | Description |
|-------|------|-------------|
| `effect_track_items` | EffectTrackItem[] | Items on this track |

### EffectTrackItem

| Field | Type | Description |
|-------|------|-------------|
| `type` | string | `VFX` or `Filter` |
| `sub_type` | string | Specific effect subtype |
| `timeline_in` | float | Start position |
| `timeline_out` | float | End position |
| `duration` | float | Effect duration |
| `x`, `y`, `width`, `height` | float | Effect region (for mosaic/blur) |

### Effect (on clips)

| Field | Type | Description |
|-------|------|-------------|
| `type` | string | `Transition`, `VFX`, `Filter`, `Volume`, `AFade`, etc. |
| `sub_type` | string | Specific effect subtype |
| `timeline_in`, `timeline_out` | float | Effect time range |
| `duration` | float | Effect duration |
| `gain` | float | Volume/AEqualize gain |

---

## output_media_config

All fields are optional. Only provided fields are sent to the server.

| Field | Type | Description |
|-------|------|-------------|
| `width` | int | Output video width in pixels |
| `height` | int | Output video height in pixels |

---

## Examples

### Simple: two video clips concatenated

```json
{
  "video_tracks": [
    {
      "main_track": true,
      "video_track_clips": [
        {
          "media_url": "https://example.com/video1.mp4",
          "type": "Video",
          "timeline_in": 0,
          "timeline_out": 5
        },
        {
          "media_url": "https://example.com/video2.mp4",
          "type": "Video",
          "timeline_in": 5,
          "timeline_out": 10
        }
      ]
    }
  ]
}
```

```bash
vidu-cli task compose --timeline timeline.json
```

### With audio and subtitle

```json
{
  "video_tracks": [
    {
      "main_track": true,
      "video_track_clips": [
        {
          "media_url": "https://example.com/clip.mp4",
          "type": "Video",
          "timeline_in": 0,
          "timeline_out": 10,
          "speed": 1.0
        }
      ]
    }
  ],
  "audio_tracks": [
    {
      "audio_track_clips": [
        {
          "media_url": "/path/to/bgm.mp3",
          "timeline_in": 0,
          "timeline_out": 10,
          "loop_mode": true
        }
      ]
    }
  ],
  "subtitle_tracks": [
    {
      "subtitle_track_clips": [
        {
          "type": "Text",
          "content": "Hello World",
          "font_size": 48,
          "font_color": "#FFFFFF",
          "alignment": "BottomCenter",
          "timeline_in": 0,
          "timeline_out": 5
        }
      ]
    }
  ]
}
```

### Inline JSON

```bash
vidu-cli task compose --timeline '{"video_tracks":[{"main_track":true,"video_track_clips":[{"media_url":"https://example.com/video1.mp4","type":"Video","timeline_in":0,"timeline_out":5}]}]}'
```

