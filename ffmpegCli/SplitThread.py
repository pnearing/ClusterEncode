#!/usr/bin/env python3
"""
    File: SplitThread.py
"""
import os
import subprocess
from datetime import timedelta, datetime
from threading import Thread
from typing import Callable, Optional


class SplitThread(Thread):
    """
    Thread to run the ffmpeg split operation.
    """
    def __init__(self,
                 ffmpeg_path: str,
                 input_path: str,
                 output_path: str,
                 chunk_size: int,
                 callback: Callable,
                 report_delay: float,
                 total_time: Optional[timedelta] = None
                 ) -> None:
        """
        Initialize the split thread.
        :param ffmpeg_path: str: The full path to ffmpeg.
        :param input_path: str: The full path to the input file, including filename.
        :param output_path: str: The full path ot the output directory, excluding filename.
        :param chunk_size: int: The number of seconds to split by.
        :param callback: Callable: The callback to use when new files are created.
        :param report_delay: float: Number of seconds to wait before reporting stats as a float.
        :param total_time: Optional[timedelta]: The total time of the input file. Optional. If not provided, then
        percent complete won't be calculated.
        """
        super().__init__(daemon=True)
        self._ffmpeg_path: str = ffmpeg_path
        """The full path to ffmpeg."""
        self._input_path: str = input_path
        """The full path to the input file."""
        # Calculate the output file name:
        input_filename = os.path.split(input_path)[-1]
        file_format: str = 'Part.%d.' + input_filename
        self._output_path: str = os.path.join(output_path, file_format)
        """The output path with the calculated file name."""
        self._chunk_size: int = chunk_size
        """The number of seconds to split by as an int."""
        self._segment_length: timedelta = timedelta(seconds=chunk_size)
        """The number of seconds per segment as a timedelta."""
        self._segment_start: timedelta = timedelta(seconds=0)
        """The start time of the current segment."""
        self._segment_end: timedelta = self._segment_length
        """The time that the current segment stops."""
        self._callback: Optional[Callable] = callback
        """The callback to call on report / new_file events."""
        self._report_delay: float = report_delay
        """The number of seconds to wait between reports as a float."""
        self._total_time: Optional[timedelta] = total_time
        """The length of the input video as a timedelta"""
        self._start_time: Optional[datetime] = None
        """The time the split was started used to calculate elapsed time."""

        # Properties:
        self._output_files: list[str] = []
        """A list of the files created."""
        self._current_time: timedelta = timedelta(seconds=0)
        """The current time of the input video."""
        self._current_speed: Optional[str] = None
        """The current speed of processing."""
        self._percent_complete: Optional[float] = None
        """The total percentage completed."""
        self._percent_segment_complete: float = 0.0
        """The approx percent complete of the current segment."""
        return

    def run(self):
        """
        Start the split operation, calling the call back every file, and report period.
        :return: None
        """
        # ffmpeg -i movie.mp4 -c copy -map 0 -segment_time 120 -f segment job-id_%d.mp4
        command_line = [self._ffmpeg_path, '-y', '-hide_banner', '-progress', '-', '-nostdin', '-i', self._input_path,
                        '-c', 'copy', '-map', '0', '-segment_time', str(self._chunk_size), '-f', 'segment',
                        self._output_path]
        process = subprocess.Popen(command_line, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if process.returncode is not None:
            raise RuntimeError("Failed to start ffmpeg")
        self._start_time = datetime.now()
        delta_delay = timedelta(seconds=self._report_delay)
        report_time = self._start_time + delta_delay
        self._segment_start = timedelta(seconds=0)
        while process.poll() is None:
            line = process.stdout.readline()
            if line.startswith('out_time_us'):  # Current time:
                # Get and set the current position of the file:
                micros: int = int(line.split('=')[-1])
                self._current_time = timedelta(microseconds=micros)
                # Calculate the approx segment percent complete:
                if self._segment_start is not None:
                    segment_time: timedelta = self._current_time - self._segment_start
                    self._percent_segment_complete = (segment_time / self._segment_length) * 100.0
                    self._percent_segment_complete = min(self._percent_segment_complete, 100.0)
                # Calculate total percent complete if we have the info:
                if self._total_time is not None:
                    self._percent_complete = (self._current_time / self._total_time) * 100.0
            elif line.startswith('speed'):  # Speed:
                self._current_speed = line.split('=')[-1].strip()
            elif line.startswith('[segment') and line.find("Opening") > -1:
                # Collect and store the new file path:
                file_path = line.split("'")[1]
                self._output_files.append(file_path)
                # Set the segment times:
                self._segment_start = self._current_time
                self._percent_segment_complete = 0.0
                # Call the callback with the new file info:
                self._callback('new_file', file_path, len(self._output_files))
            if datetime.now() > report_time:
                report_time = datetime.now() + delta_delay
                self._callback('report', self._current_time, self._current_speed, self._percent_segment_complete,
                               self._percent_complete)
        return

    @property
    def output_files(self) -> tuple[str, ...]:
        return tuple(self._output_files)

    @property
    def current_time(self) -> Optional[timedelta]:
        return self._current_time

    @property
    def current_speed(self) -> Optional[str]:
        return self._current_speed

    @property
    def percent_complete(self) -> Optional[float]:
        return self._percent_complete

    @property
    def percent_segment_complete(self) -> float:
        return self._percent_segment_complete


if __name__ == '__main__':
    exit(0)
