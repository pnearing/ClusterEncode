#!/usr/bin/env python3
"""
    File: EncodeThread.py
"""
import os.path
from datetime import timedelta
from threading import Thread
import subprocess
from enum import Enum
from typing import Optional, Callable


class AudioEncoders(Enum):
    """
    Enum to store audio encoder values.
    """
    COPY = 'copy'
    """Copy the audio."""
    MP3 = 'mp3'
    """Encode audio to MP3."""
    AAC = 'aac'
    """Encode audio to AAC."""


class VideoEncoders(Enum):
    """
    Enum to store video encoder values.
    """
    COPY = 'copy'
    """Copy the video."""
    X264 = 'libx264'
    """Encode video with X264."""
    X265 = 'libx265'
    """Encode video with X265."""


class EncodeThread(Thread):
    """
    Thread to watch a single ffmpeg encode process.
    """
    def __init__(self,
                 ffmpeg_path: str,
                 input_path: str,
                 output_path: str,
                 audio_encoder: AudioEncoders,
                 down_mix_audio: bool,
                 boost_volume: int,
                 video_encoder: VideoEncoders,
                 scale_video: Optional[dict[str, int]],
                 callback: Callable,
                 ) -> None:
        """
        Initialize the encoder thread.
        :param ffmpeg_path: str: The full path to ffmpeg.
        :param input_path: str: The full path to the video to encode.
        :param output_path: str: The full path to the directory to output in.
        :param audio_encoder: AudioEncoders: One of the enum of the audio encoders. NOTE: If this is COPY, then the
        down_mix_audio parameter is ignored.
        :param down_mix_audio: bool: True down mix the audio to stereo, False keep the original channels.
        :param boost_volume: int: The amount in percentage to boost the audio.
        :param video_encoder: VideoEncoders: One of the enu of the video encoders. NOTE: If this is COPY, then the
        scale_video parameter is ignored.
        :param scale_video: Optional[dict[str, int]]: If None, no scaling is preformed, otherwise it is a dict with
        the keys 'width', 'height', and 'direction'; Width and height values an int for the number of pixels; And
        'direction' is either 'UP' or 'DOWN'.
        IE: {'width': 640, 'width': 480}
        :param callback: Callable: The callback to call with the status.
        """
        super().__init__(daemon=True)
        self._ffmpeg_path: str = ffmpeg_path
        self._input_path: str = input_path
        self._output_path: str = output_path
        self._audio_encoder: AudioEncoders = audio_encoder
        self._down_mix_audio: bool = down_mix_audio
        self._boost_volume: int = boost_volume
        self._video_encoder: VideoEncoders = video_encoder
        self._scale_video: Optional[dict[str, int]] = scale_video
        # Properties:
        self._current_frame: Optional[int] = None  # Will be None if video_encoder = copy
        self._fps: Optional[float] = None  # Will be None if video_encoder = copy
        self._bit_rate: Optional[str] = None  # Will be None until encoding starts.
        self._current_time: Optional[timedelta] = None  # Will be None until encoding starts.
        self._speed: Optional[str] = None  # Will be None until encoding starts.
        return

    def run(self) -> None:
        """
        Start the encoding process.
        :return: None
        """
        # ffmpeg -i job-id_1.mp4 -c:v copy -c:a copy job-id_1_done.mkv
        command_line = [self._ffmpeg_path, '-y', '-hide_banner', '-progress', '-', '-i', self._input_path,]
        # Add video encoding options:
        command_line.extend(['-c:v', self._video_encoder.value,])
        if self._video_encoder != VideoEncoders.COPY:
            if self._scale_video is not None:
                scale_filter: str
                if self._scale_video['direction'] == 'UP':
                    scale_filter = ':flags=lanczos'
                elif self._scale_video['direction'] == 'DOWN':
                    scale_filter = ':flags=bicubic'
                else:
                    raise RuntimeError("Invalid scale direction.")
                scale_size = "scale=%ix%i" % (self._scale_video['width'], self._scale_video['height'])
                video_filter = scale_size + scale_filter
                command_line.extend(['-vf', video_filter])

        # Add audio encoding options.
        # "pan=stereo|c0=c2+0.30*c0+0.30*c4|c1=c2+0.30*c1+0.30*c5"
        command_line.extend(['-c:a', self._audio_encoder.value])
        if self._audio_encoder != AudioEncoders.COPY:
            if self._boost_volume:
                volume = 256 + int(256 * (self._boost_volume / 100))
                command_line.extend(['-vol', str(volume)])
            if self._down_mix_audio:
                command_line.extend(['-af', "pan=stereo|c0=c2+0.30*c0+0.30*c4|c1=c2+0.30*c1+0.30*c5"])

        # Add the output file path:
        command_line.append(self._output_path)

        process = subprocess.Popen(command_line, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        while process.poll() is None:
            line = process.stdout.readline()


    @property
    def current_frame(self) -> Optional[int]:
        """
        The current frame.
        :return: Optional[int]: The current frame, as an int, or None if video encoding is not started. This will
        remain None if the video encoder is 'copy'.
        """
        return self._current_frame

    @property
    def fps(self) -> Optional[float]:
        """
        Current frames per second.
        :return: Optional[float]: The current fps if a float, or None if video encoding is not started. This will
        remain None if the video encoder is 'copy'.
        """
        return self._fps

    @property
    def bit_rate(self) -> Optional[str]:
        """
        Current bit rate.
        :return: Optional[str]: The current bit rate with units if a string, or None if encoding has not started.
        """
        return self._bit_rate

    @property
    def current_time(self) -> Optional[timedelta]:
        """
        The current time.
        :return: Optional[timedelta]: The current timestamp as a timedelta object.
        """
        return self._current_time
        # self._current_time: Optional[timedelta] = None  # Will be None until encoding starts.
        # self._speed: Optional[str] = None  # Will be None until encoding starts.

if __name__ == '__main__':
    exit(0)
