#!/usr/bin/env python3
"""
    File: SplitThread.py
"""
import os
import subprocess
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
                 callback: Callable
                 ) -> None:
        """
        Initialize the split thread.
        :param ffmpeg_path: str: The full path to ffmpeg.
        :param input_path: str: The full path to the input file, including filename.
        :param output_path: str: The full path ot the output directory, excluding filename.
        :param chunk_size: int: The number of seconds to split by.
        :param callback: Callable: The callback to use when new files are created.
        """
        super().__init__(daemon=True)
        self._ffmpeg_path: str = ffmpeg_path
        self._input_path: str = input_path
        input_filename = os.path.split(input_path)[-1]
        file_format: str = 'Part.%d.' + input_filename
        self._output_path: str = os.path.join(output_path, file_format)
        self._chunk_size: int = chunk_size
        self._callback: Optional[Callable] = callback
        self._output_files: list[str] = []
        return

    def run(self):
        """
        Start the split operation, calling the call back every file.
        :return: None
        """
        # ffmpeg -i movie.mp4 -c copy -map 0 -segment_time 120 -f segment job-id_%d.mp4

        command_ine = [self._ffmpeg_path, '-y', '-hide_banner', '-nostdin', '-i', self._input_path, '-c', 'copy',
                       '-map', '0', '-segment_time', str(self._chunk_size), '-f', 'segment', self._output_path]
        process = subprocess.Popen(command_ine, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        while process.poll() is None:
            line = process.stdout.readline()
            if line.startswith('[segment'):
                file_path = line.split("'")[1]
                self._output_files.append(file_path)
                self._callback(file_path, len(self._output_files))
        return

    @property
    def output_files(self) -> tuple[str, ...]:
        return tuple(self._output_files)


if __name__ == '__main__':
    exit(0)
