#!/usr/bin/env python3
"""
    File: main.py
"""
from typing import Optional
from SignalHandlers import SignalHandlers

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from gi.repository import GLib
from gi.repository import Gio
from pymediainfo import MediaInfo



builder: Gtk.Builder = Gtk.Builder()




if __name__ == '__main__':

    builder.add_from_file("ClusterEncode.glade")

    builder.connect_signals(SignalHandlers(builder))

    window = builder.get_object("app_window")
    window.show_all()

    Gtk.main()
