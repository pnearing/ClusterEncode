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
                 report_delay: int,
                 ) -> None:
        """
        Initialize the split thread.
        :param ffmpeg_path: str: The full path to ffmpeg.
        :param input_path: str: The full path to the input file, including filename.
        :param output_path: str: The full path ot the output directory, excluding filename.
        :param chunk_size: int: The number of seconds to split by.
        :param callback: Callable: The callback to use when new files are created.
        :param report_delay: int: Number of seconds to wait before reporting stats.
        """
        super().__init__(daemon=True)
        self._ffmpeg_path: str = ffmpeg_path
        self._input_path: str = input_path
        input_filename = os.path.split(input_path)[-1]
        file_format: str = 'Part.%d.' + input_filename
        self._output_path: str = os.path.join(output_path, file_format)
        self._chunk_size: int = chunk_size
        self._callback: Optional[Callable] = callback
        self._report_delay: int = report_delay
        # Properties:
        self._output_files: list[str] = []
        self._current_time: Optional[timedelta] = None
        self._current_speed: Optional[str] = None
        return

    def run(self):
        """
        Start the split operation, calling the call back every file.
        :return: None
        """
        # ffmpeg -i movie.mp4 -c copy -map 0 -segment_time 120 -f segment job-id_%d.mp4

        command_ine = [self._ffmpeg_path, '-y', '-hide_banner', '-progress', '-', '-nostdin', '-i', self._input_path,
                       '-c', 'copy', '-map', '0', '-segment_time', str(self._chunk_size), '-f', 'segment',
                       self._output_path]
        process = subprocess.Popen(command_ine, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        time_started = datetime.now()
        delta_delay = timedelta(seconds=self._report_delay)
        report_time = time_started + delta_delay
        while process.poll() is None:
            line = process.stdout.readline()
            if line.startswith('out_time_us'):
                micros: int = int(line.split('=')[-1])
                self._current_time = timedelta(microseconds=micros)
            elif line.startswith('speed'):
                self._current_speed = line.split('=')[-1].strip()
            elif line.startswith('[segment') and line.find("Opening") > -1:
                file_path = line.split("'")[1]
                self._output_files.append(file_path)
                self._callback(file_path, len(self._output_files))

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

if __name__ == '__main__':
    exit(0)
