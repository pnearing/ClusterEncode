#!/usr/bin/env python3
"""
    File: SignalHandlers.py
"""
from pymediainfo import MediaInfo

import gi
gi.require_version("Gtk", "3.0")

from gi.repository import Gtk


class SignalHandlers:
    def __init__(self, builder: Gtk.Builder) -> None:
        self._builder = builder
        return

    def _set_input_audio_properties(self, media_info: MediaInfo):
        # Get and set the number of audio tracks:
        num_audio_tracks = media_info.general_tracks[0].count_of_audio_streams
        lbl_audio_tracks = self._builder.get_object('lbl_input_audio_num_tracks')
        lbl_audio_tracks.set_label(str(num_audio_tracks))
        # Get and set the number of channels:
        num_channels = media_info.audio_tracks[0].channel_s
        lbl_num_channels = self._builder.get_object('lbl_input_audio_channels')
        lbl_num_channels.set_label(str(num_channels))
        # Get and set the bit rate:
        bit_rate = media_info.audio_tracks[0].bit_rate
        lbl_bit_rate = self._builder.get_object('lbl_input_audio_bit_rate')
        lbl_bit_rate.set_label(str(bit_rate))
        return

    ##############################
    # Signal Handlers:
    ##############################
    @staticmethod
    def on_destroy(*_args):
        Gtk.main_quit()
        return

    def fbtn_input_file_file_set_cb(self, widget, *_args):
        # Get the file path from the widget:
        file_path = widget.get_file().get_path()
        # Load the media info:
        media_info = MediaInfo.parse(file_path)
        # Set the input audio labels:
        self._set_input_audio_properties(media_info)
        return


if __name__ == '__main__':
    exit(0)
