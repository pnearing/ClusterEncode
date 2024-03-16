#!/usr/bin/env python3
"""
    File: main.py
"""
from typing import Optional

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from gi.repository import GLib
from gi.repository import Gio
from pymediainfo import MediaInfo

builder: Gtk.Builder = Gtk.Builder()


class SignalHandlers:
    @staticmethod
    def on_destroy(*_args):
        Gtk.main_quit()
        return

    @staticmethod
    def fbtn_input_file_file_set_cb(widget, *_args):
        file_path = widget.get_file().get_path()
        media_info = MediaInfo.parse(file_path)
        num_audio_tracks = media_info.general_tracks[0].count_of_audio_streams
        lbl_audio_tracks = builder.get_object('lbl_input_audio_num_tracks')
        lbl_audio_tracks.set_label(str(num_audio_tracks))
        return


if __name__ == '__main__':

    builder.add_from_file("ClusterEncode.glade")
    builder.connect_signals(SignalHandlers())
    window = builder.get_object("app_window")
    window.show_all()

    Gtk.main()
