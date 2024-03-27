#!/usr/bin/env python3
"""
    Name: LoadMediaInfoThread.py
    Description:
"""
import os
from threading import Thread, Event
from typing import Optional
from gi.repository import Gtk
from pymediainfo import MediaInfo

import common


class LoadMediaInfoThread(Thread):
    """
    Thread to load media info, for large files or slow file systems.
    """
    def __init__(self, file_path: str) -> None:
        super().__init__(daemon=True)
        self._file_path: str = file_path
        self._media_info: Optional[MediaInfo] = None
        return

    @staticmethod
    def _set_input_audio_properties(media_info: MediaInfo) -> None:
        """
        Set the input audio info labels.
        :param media_info: MediaInfo: The media info object for the input file.
        :return: None
        """
        # Get and set the number of audio tracks:
        num_audio_tracks = media_info.general_tracks[0].count_of_audio_streams
        lbl_audio_tracks: Gtk.Label = common.builder.get_object('lbl_input_audio_num_tracks')
        lbl_audio_tracks.set_label(str(num_audio_tracks))
        # Get and set the number of channels:
        num_channels = media_info.audio_tracks[0].channel_s
        lbl_num_channels: Gtk.Label = common.builder.get_object('lbl_input_audio_channels')
        lbl_num_channels.set_label(str(num_channels))
        # Get and set the bit rate:
        bit_rate = media_info.audio_tracks[0].bit_rate
        lbl_bit_rate: Gtk.Label = common.builder.get_object('lbl_input_audio_bit_rate')
        lbl_bit_rate.set_label(str(bit_rate))
        # Get and set the codec:
        codec = media_info.audio_tracks[0].commercial_name
        lbl_codec: Gtk.Label = common.builder.get_object('lbl_input_audio_codec')
        lbl_codec.set_label(codec)
        # Get and set the duration:
        duration = media_info.audio_tracks[0].other_duration[0]
        lbl_duration: Gtk.Label = common.builder.get_object('lbl_input_audio_duration')
        lbl_duration.set_label(duration)
        return

    @staticmethod
    def _set_input_video_properties(media_info: MediaInfo) -> None:
        """
        Set the video info properties.
        :param media_info: MediaInfo: The media info object for the input video.
        :return: None
        """
        # Get and set the codec:
        codec = media_info.video_tracks[0].commercial_name
        lbl_codec: Gtk.Label = common.builder.get_object('lbl_input_video_codec')
        lbl_codec.set_label(codec)
        # Get and set width:
        width = media_info.video_tracks[0].width
        lbl_width: Gtk.Label = common.builder.get_object('lbl_input_video_width')
        lbl_width.set_label(str(width))
        # Get and set the height:
        height = media_info.video_tracks[0].height
        lbl_height: Gtk.Label = common.builder.get_object('lbl_input_video_height')
        lbl_height.set_label(str(height))
        # Get and set the duration:
        duration = media_info.video_tracks[0].other_duration[0]
        lbl_duration: Gtk.Label = common.builder.get_object('lbl_input_video_duration')
        lbl_duration.set_label(duration)
        return

    def run(self) -> None:
        """
        Load the media info, and set the appropriate labels.
        :return: None
        """

        # Load the media info:
        media_info = MediaInfo.parse(self._file_path)

        # Set the input audio/video labels:
        self._set_input_audio_properties(media_info)
        self._set_input_video_properties(media_info)

        # Enable the 'encode' button:
        encode_button = common.builder.get_object('btn_start_encode')
        encode_button.set_sensitive(True)

        # Set the output directory and filename as sensitive:
        directory_label: Gtk.Label = common.builder.get_object('lbl_output_directory')
        fbtn_output_directory: Gtk.FileChooserButton = common.builder.get_object('fbtn_output_directory')
        filename_label: Gtk.Label = common.builder.get_object('lbl_output_filename')
        filename_entry: Gtk.Entry = common.builder.get_object('ent_output_filename')

        directory_label.set_sensitive(True)
        fbtn_output_directory.set_sensitive(True)
        filename_label.set_sensitive(True)
        filename_entry.set_sensitive(True)

        # Set the output file name.
        file_name: str = os.path.split(self._file_path)[-1]
        if file_name.endswith('.mkv'):
            file_name = file_name[:-4] + 're-encode.mkv'
        else:
            idx = file_name.rfind('.')
            file_name = file_name[:idx] + '.mkv'
        filename_entry.set_text(file_name)

        # Stop the spinner spinning:
        spinner: Gtk.Spinner = common.builder.get_object('input_file_loading_spinner')
        spinner.stop()
        # Set the input file chooser button as sensitive.
        file_chooser: Gtk.FileChooserButton = common.builder.get_object('fbtn_input_file')
        file_chooser.set_sensitive(True)
        return


if __name__ == '__main__':
    exit(0)
