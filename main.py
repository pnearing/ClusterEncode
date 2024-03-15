#!/usr/bin/env python3
"""
    File: main.py
"""

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import GLib, Gio, Gtk


if __name__ == '__main__':
    builder = Gtk.Builder()
    builder.add_from_file("ClusterEncode.glade")
    window = builder.get_object("app_window")
    window.show_all()

    Gtk.main()