import logging
import os
import random
from dataclasses import dataclass
from typing import List, Optional, Tuple

import ffmpeg

logger = logging.getLogger(__name__)


@dataclass
class TimelineSegment:
    start_time: float
    end_time: float
    visual_path: str
    audio_path: str
    transition_type: str


class Timeline:
    def __init__(self):
        self.segments: List[TimelineSegment] = []
        self.scene_transitions: List[str] = []

    def add_segment(self, segment: TimelineSegment):
        self.segments.append(segment)


class Composer:
    def __init__(
        self,
        width: int = 1080,
        height: int = 1920,
        fps: int = 30,
        transition_duration: float = 0.5,
        subtitle_y_ratio: float = 0.72,
        subtitle_font_size: int = 52,
    ):
        self.width = width
        self.height = height
        self.fps = fps
        self.transition_duration = transition_duration
        self.subtitle_y_ratio = subtitle_y_ratio
        self.subtitle_font_size = subtitle_font_size
        self.temp_dir = os.path.join(os.getcwd(), "assets", "temp")
        self.final_dir = os.path.join(os.getcwd(), "assets", "final")
        os.makedirs(self.temp_dir, exist_ok=True)
        os.makedirs(self.final_dir, exist_ok=True)
        self.transitions = ["fade", "diagbr", "diagtl", "wipeleft", "fadeblack"]

    def choose_transition(self, mood: str) -> str:
        mood_value = (mood or "").lower()
        if mood_value in {"intriguing", "mystery"}:
            return "fade"
        if mood_value == "educational":
            return random.choice(["diagbr", "wipeleft"])
        if mood_value in {"ominous", "dramatic"}:
            return "fadeblack"
        return random.choice(self.transitions)

    def create_timeline(self, script_data, visual_pairs) -> Timeline:
        timeline = Timeline()
        current_time = 0.0

        for index, scene in enumerate(script_data):
            if index >= len(visual_pairs) or visual_pairs[index] is None:
                continue

            path_a, path_b = visual_pairs[index]
            total_duration = max(float(scene.get("duration", 1.0)), 1.0)
            half_duration = total_duration / 2
            transition_type = self.choose_transition(scene.get("mood", ""))
            scene_audio = scene["audio_path"]

            timeline.scene_transitions.append(transition_type)
            timeline.add_segment(
                TimelineSegment(
                    start_time=current_time,
                    end_time=current_time + half_duration,
                    visual_path=path_a,
                    audio_path=scene_audio,
                    transition_type=transition_type,
                )
            )
            timeline.add_segment(
                TimelineSegment(
                    start_time=current_time + half_duration,
                    end_time=current_time + total_duration,
                    visual_path=path_b,
                    audio_path=scene_audio,
                    transition_type=transition_type,
                )
            )
            current_time += total_duration
            if index < len(script_data) - 1:
                current_time = max(0.0, current_time - self.transition_duration)

        return timeline

    def get_duration(self, filepath: str) -> float:
        try:
            probe = ffmpeg.probe(filepath)
            return float(probe["format"]["duration"])
        except Exception:  # noqa: BLE001
            return 0.0

    @staticmethod
    def _is_image(path: str) -> bool:
        return os.path.splitext(path.lower())[1] in {".jpg", ".jpeg", ".png", ".webp"}

    @staticmethod
    def _escape_drawtext(text: str) -> str:
        return (
            text.replace("\\", "\\\\")
            .replace(":", "\\:")
            .replace("'", "\\'")
            .replace("%", "\\%")
            .replace("\n", " ")
        )

    def _build_visual_stream(self, path: str, duration: float):
        if self._is_image(path):
            frames = max(int(duration * self.fps), 1)
            stream = (
                ffmpeg.input(path, loop=1, framerate=self.fps)
                .filter("scale", self.width, self.height, force_original_aspect_ratio="increase")
                .filter("crop", self.width, self.height)
                .filter(
                    "zoompan",
                    z="min(zoom+0.0008,1.15)",
                    x="iw/2-(iw/zoom/2)",
                    y="ih/2-(ih/zoom/2)",
                    d=frames,
                    s=f"{self.width}x{self.height}",
                    fps=self.fps,
                )
                .trim(duration=duration)
                .setpts("PTS-STARTPTS")
            )
            return stream

        return (
            ffmpeg.input(path, stream_loop=-1)
            .trim(duration=duration)
            .setpts("PTS-STARTPTS")
            .filter("scale", self.width, self.height, force_original_aspect_ratio="increase")
            .filter("crop", self.width, self.height)
            .filter("fps", fps=self.fps, round="up")
        )

    def render_scene(self, scene, visual_pair: Tuple[str, str]) -> Optional[str]:
        scene_id = scene["id"]
        audio_path = scene["audio_path"]
        total_duration = max(float(scene.get("duration", 1.0)), 1.0)
        output_path = os.path.join(self.temp_dir, f"scene_{scene_id}.mp4")

        try:
            input_audio = ffmpeg.input(audio_path)
            duration_a = total_duration / 2
            duration_b = total_duration - duration_a
            stream_a = self._build_visual_stream(visual_pair[0], duration_a)
            stream_b = self._build_visual_stream(visual_pair[1], duration_b)
            video_stream = ffmpeg.concat(stream_a, stream_b, v=1, a=0)
            subtitle_text = self._escape_drawtext(scene.get("text", ""))
            subtitled_stream = video_stream.filter(
                "drawtext",
                text=subtitle_text,
                fontcolor="white",
                fontsize=self.subtitle_font_size,
                x="(w-text_w)/2",
                y=f"h*{self.subtitle_y_ratio}",
                borderw=3,
                bordercolor="black",
                shadowcolor="black",
                shadowx=2,
                shadowy=2,
            )

            ffmpeg.output(
                subtitled_stream,
                input_audio,
                output_path,
                vcodec="libx264",
                acodec="aac",
                pix_fmt="yuv420p",
                shortest=None,
            ).run(overwrite_output=True, quiet=True)
            return output_path
        except ffmpeg.Error as error:
            logger.error(
                "Render failed for scene %s: %s",
                scene_id,
                error.stderr.decode("utf8") if error.stderr else str(error),
            )
            return None

    def render_all_scenes(self, script_data, visual_pairs):
        timeline = self.create_timeline(script_data, visual_pairs)
        logger.info("Timeline created with %s segments", len(timeline.segments))

        rendered_paths = []
        transitions = []
        for index, scene in enumerate(script_data):
            if index >= len(visual_pairs) or visual_pairs[index] is None:
                continue
            output_path = self.render_scene(scene, visual_pairs[index])
            if output_path:
                rendered_paths.append(output_path)
                transitions.append(self.choose_transition(scene.get("mood", "")))

        return rendered_paths, transitions

    def concatenate_with_transitions(self, video_paths, transitions, output_filename="final_short.mp4"):
        output_path = os.path.join(self.final_dir, output_filename)

        if os.path.exists(output_path):
            os.remove(output_path)

        if not video_paths:
            return None

        base = ffmpeg.input(video_paths[0])
        v_stream = base.video
        a_stream = base.audio
        current_duration = self.get_duration(video_paths[0])

        for index in range(1, len(video_paths)):
            next_clip = ffmpeg.input(video_paths[index])
            next_duration = self.get_duration(video_paths[index])
            transition = transitions[index - 1] if index - 1 < len(transitions) else random.choice(self.transitions)
            offset = max(current_duration - self.transition_duration, 0.0)

            v_stream = ffmpeg.filter(
                [v_stream, next_clip.video],
                "xfade",
                transition=transition,
                duration=self.transition_duration,
                offset=offset,
            )
            a_stream = ffmpeg.filter(
                [a_stream, next_clip.audio],
                "acrossfade",
                d=self.transition_duration,
            )
            current_duration = (current_duration + next_duration) - self.transition_duration

        try:
            ffmpeg.output(
                v_stream,
                a_stream,
                output_path,
                vcodec="libx264",
                acodec="aac",
                pix_fmt="yuv420p",
                movflags="faststart",
                preset="medium",
            ).run(overwrite_output=True, quiet=False)
            logger.info("Final video saved at %s", output_path)
            return output_path
        except ffmpeg.Error as error:
            logger.error("Final stitching failed: %s", error.stderr.decode("utf8") if error.stderr else str(error))
            return None
