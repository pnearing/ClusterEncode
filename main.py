#!/usr/bin/env python3
"""
    File: main.py
"""

import gi
gi.require_version("Gtk", "3.0")
# from gi.repository import GLib, Gio, Gtk
from gi.repository import Gtk
from gi.repository import GLib
from gi.repository import Gio


class SignalHandlers:
    @staticmethod
    def on_destroy(*_args):
        Gtk.main_quit()
        return


if __name__ == '__main__':
    builder = Gtk.Builder()
    builder.add_from_file("ClusterEncode.glade")
    builder.connect_signals(SignalHandlers())
    window = builder.get_object("app_window")
    window.show_all()

    Gtk.main()
