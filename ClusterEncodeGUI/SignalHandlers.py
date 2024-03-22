#!/usr/bin/env python3
"""
    File: SignalHandlers.py
"""

from pymediainfo import MediaInfo
import common
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GObject, Gio


class SignalHandlers:
    def __init__(self) -> None:
        self.__version__ = common.__version__
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
        lbl_audio_tracks = common.builder.get_object('lbl_input_audio_num_tracks')
        lbl_audio_tracks.set_label(str(num_audio_tracks))
        # Get and set the number of channels:
        num_channels = media_info.audio_tracks[0].channel_s
        lbl_num_channels = common.builder.get_object('lbl_input_audio_channels')
        lbl_num_channels.set_label(str(num_channels))
        # Get and set the bit rate:
        bit_rate = media_info.audio_tracks[0].bit_rate
        lbl_bit_rate = common.builder.get_object('lbl_input_audio_bit_rate')
        lbl_bit_rate.set_label(str(bit_rate))
        # Get and set the codec:
        codec = media_info.audio_tracks[0].commercial_name
        lbl_codec = common.builder.get_object('lbl_input_audio_codec')
        lbl_codec.set_label(codec)
        # Get and set the duration:
        duration = media_info.audio_tracks[0].other_duration[0]
        lbl_duration = common.builder.get_object('lbl_input_audio_duration')
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
        lbl_codec = common.builder.get_object('lbl_input_video_codec')
        lbl_codec.set_label(codec)
        # Get and set width:
        width = media_info.video_tracks[0].width
        lbl_width = common.builder.get_object('lbl_input_video_width')
        lbl_width.set_label(str(width))
        # Get and set the height:
        height = media_info.video_tracks[0].height
        lbl_height = common.builder.get_object('lbl_input_video_height')
        lbl_height.set_label(str(height))
        # Get and set the duration:
        duration = media_info.video_tracks[0].other_duration[0]
        lbl_duration = common.builder.get_object('lbl_input_video_duration')
        lbl_duration.set_label(duration)
        return

    ##############################
    # Signal Handlers:
    ##############################
    @staticmethod
    def on_destroy(*_args):
        Gtk.main_quit()
        return

    def fbtn_input_file_file_set_cb(self, widget: Gtk.FileChooserWidget, *_args):
        """
        Input file chooser button file-set callback.
        :param widget: FileChooserButton: The widget.
        :param _args: Ignored.
        :return: None
        """
        # Get the file path from the widget:
        file_path = widget.get_file().get_path()
        # Load the media info:
        media_info = MediaInfo.parse(file_path)  # TODO: This causes the dialog to hang on large files.
        # Set the input audio/video labels:
        self._set_input_audio_properties(media_info)
        self._set_input_video_properties(media_info)
        # Enable the 'encode' button:
        encode_button = common.builder.get_object('btn_start_encode')
        encode_button.set_sensitive(True)

        # debug:
        print(_args)
        return

    @staticmethod
    def switch_copy_audio_state_set_cb(widget: Gtk.Switch, *_args):
        # Get the widgets we want to work with:
        audio_encoder_frame: Gtk.Frame = common.builder.get_object('fra_output_audio_encoder')
        audio_encoder_combo: Gtk.ComboBox = common.builder.get_object('cmb_output_audio_encoder')
        chk_downmix: Gtk.CheckButton = common.builder.get_object('chk_output_audio_downmix')
        chk_volume_boost: Gtk.CheckButton = common.builder.get_object('chk_volume_boost')
        slider_volume_level: Gtk.Scale = common.builder.get_object('sbtn_output_audio_boost_value')
        if not widget.get_state():  # Copy audio stream is selected.
            # Turn off audio encoder sensitivities:
            audio_encoder_frame.set_sensitive(False)
            audio_encoder_combo.set_sensitive(False)
            chk_downmix.set_sensitive(False)
            chk_volume_boost.set_sensitive(False)
            slider_volume_level.set_sensitive(False)
        else:  # Encode audio stream is selected.
            audio_encoder_frame.set_sensitive(True)
            audio_encoder_combo.set_sensitive(True)
            chk_downmix.set_sensitive(True)
            chk_volume_boost.set_sensitive(True)
            slider_volume_level.set_sensitive(chk_volume_boost.get_active())  # Set only if chk button is active.
        return

    @staticmethod
    def on_chk_volume_boost_toggled(widget: Gtk.CheckButton, *_args):
        volume_level_slider: Gtk.Scale = common.builder.get_object('sbtn_output_audio_boost_value')
        volume_level_slider.set_sensitive(widget.get_active())
        return

if __name__ == '__main__':
    exit(0)
