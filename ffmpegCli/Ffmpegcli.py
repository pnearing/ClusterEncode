#!/usr/bin/env python3
"""
    File: ffmpegCli.py
"""
import os.path
import shutil
import subprocess
from typing import Optional

try:
    from SplitThread import SplitThread
except ModuleNotFoundError:
    from .SplitThread import SplitThread


class Ffmpegcli(object):
    """
    class to store ffmpeg functions / threads / actions etc.
    """

    def __init__(self, ffmpeg_path: str) -> None:
        self._ffmpeg_path = ffmpeg_path
        """The full path to ffmpeg."""
        self.current_threads: Optional[list[SplitThread]] = []
        """The current threads running."""
        self.status: str = 'idle'
        """The current status of ffmpeg operations."""
        return

    def get_version(self) -> Optional[str]:
        """
        Get the version of ffmpeg.
        :return: Optional[str]
        """
        command_line: list[str] = [self._ffmpeg_path, '-version']
        try:
            cmd_output = subprocess.check_output(command_line, text=True)
        except subprocess.CalledProcessError:
            return None
        version_line = cmd_output.splitlines()[0]
        version = version_line.split()[2]
        if version.find('-') > -1:
            version = version.split('-')[0]
        return version

    def get_audio_encoders(self) -> Optional[list[tuple[str, str]]]:
        """
        Get all the supported audio encoders supported by this ffmpeg.
        :return: Optional[list[tuple[str, str]]]: None on error running ffmpeg, otherwise it's a list of tuples; the
        first element of the tuple is the encoder name, and the second element is the encoder description.
        """
        command_line: list[str] = [self._ffmpeg_path, '-hide_banner', '-encoders']
        try:
            all_encoders: list[str] = subprocess.check_output(command_line, text=True).splitlines()
        except subprocess.CalledProcessError:
            return None
        audio_encoders: list[tuple[str, str]] = []
        start_looking: bool = False
        for line in all_encoders:
            if line.startswith(' -'):
                start_looking = True
            if start_looking:
                if line.startswith(' A'):
                    encoder: str = line.split()[1]
                    description: str = ' '.join(line.split()[2:])
                    audio_encoders.append((encoder, description))
        return audio_encoders

    def get_video_encoders(self) -> Optional[list[tuple[str, str]]]:
        """
        Get a list of the video encoders supported by ffmpeg.
        :return: Optional[list[tuple[str, str]]]: None on error running ffmpeg, otherwise a list of tuples. The first
        element of the tuple is the encoder name, the second element is the encoder description.
        """
        command_line: list[str] = [self._ffmpeg_path, '-hide_banner', '-encoders']
        try:
            all_encoders: list[str] = subprocess.check_output(command_line, text=True).splitlines()
        except subprocess.CalledProcessError:
            return None
        video_encoders: list[tuple[str, str]] = []
        start_looking: bool = False
        for line in all_encoders:
            if line.startswith(' -'):
                start_looking = True
            if start_looking:
                if line.startswith(' V'):
                    encoder: str = line.split()[1]
                    description: str = ' '.join(line.split()[2:])
                    video_encoders.append((encoder, description))
        return video_encoders


    def split(self, input_path: str, output_path: str, chunk_size: int, callback: callable) -> bool:
        """
        Start the split thread running.
        :param input_path: str: The full path to the video to split.
        :param output_path: str: The full path to the output directory.
        :param chunk_size: int: The number of seconds per file.
        :param callback: Callback: The callback to run every time a new file is created.
        :return: bool: True the thread started, False, the thread didn't start.
        """
        if self.current_threads is not None:
            return False
        self.current_threads = SplitThread(self._ffmpeg_path, input_path, output_path, chunk_size, callback)
        self.current_threads.start()
        return True

    def split_finish(self) -> tuple[bool, tuple[str, ...]]:
        """
        Blocks until split is finished, returning the results.
        :return: tuple[bool, tuple[str, ...]]: Returns a tuple where the first element is a bool, which is True on
        split success, and False if the split wasn't started; The second element of the tuple is a tuple of strings,
        each element being the full path to a created file, or an empty tuple if the split wasn't started.
        """
        if not isinstance(self.current_threads, SplitThread):
            return False, ()
        self.current_threads.join()
        output_file_list = self.current_threads.output_files
        self.current_threads = None
        return True, output_file_list



if __name__ == '__main__':
    _input = "/home/orangepi/convert/Input/serenity.mkv"
    _output = "/home/orangepi/convert/Working/Input/"
    _ffmpeg_path = shutil.which('ffmpeg')
    if _ffmpeg_path is None:
        print("ffmpeg not found.")
        exit(1)

    _ffmpeg_cli = Ffmpegcli(_ffmpeg_path)
    print(_ffmpeg_cli.get_version())

    # Test split:
    # def _callback(file_path: str, file_count: int) -> None:
    #     print(file_path, file_count)
    #     return
    # print("Starting split.")
    # _ffmpeg_cli.split(_input, _output, 300, _callback)
    #
    # print("Calling split_finish")
    # _ffmpeg_cli.split_finish()
    # print("Split Finished.")

    _ffmpeg_cli.get_audio_encoders()

    exit(0)
