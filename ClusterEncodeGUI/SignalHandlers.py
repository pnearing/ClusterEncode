#!/usr/bin/env python3
"""
    File: SignalHandlers.py
"""
import os.path

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

    def fbtn_input_file_file_set_cb(self, widget: Gtk.FileChooserButton, *_args):
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

        # Set the output file name.
        file_name: str = os.path.split(file_path)[-1]
        if file_name.endswith('.mkv'):
            file_name = file_name[:-4] + 're-encode.mkv'
        else:
            idx = file_name.rfind('.')
            file_name = file_name[:idx] + '.mkv'
        file_name_entry: Gtk.Entry = common.builder.get_object('ent_output_filename')
        file_name_entry.set_text(file_name)
        return

    @staticmethod
    def switch_copy_audio_state_set_cb(widget: Gtk.Switch, *_args):
        """
        Copy Audio switch, set the sensitivities of the encoding options.
        :param widget: Gtk.Switch: The switch widget.
        :param _args: Ignored.
        :return: None
        """
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
        """
        Volume boost check box, set the slider sensitivity.
        :param widget: Gtk.CheckButton: The check button widget.
        :param _args: Ignored.
        :return: None
        """
        volume_level_slider: Gtk.Scale = common.builder.get_object('sbtn_output_audio_boost_value')
        volume_level_slider.set_sensitive(widget.get_active())
        return

    @staticmethod
    def switch_copy_video_state_set_cb(widget: Gtk.Switch, *_args) -> None:
        """
        Copy video switch, sets the sensitivities of the video encoding widgets.
        :param widget: Gtk.Switch: The copy video switch widget.
        :param _args: Ignored.
        :return: None
        """
        video_encoder_frame: Gtk.Frame = common.builder.get_object('fra_output_video_encode')
        video_encoder_combo: Gtk.ComboBox = common.builder.get_object('cmb_output_video_encoder')
        chk_scale_video: Gtk.CheckButton = common.builder.get_object('chk_output_video_scale')
        spin_video_width: Gtk.SpinButton = common.builder.get_object('sbtn_output_video_width')
        seperator_label: Gtk.Label = common.builder.get_object('lbl_output_video_x')
        spin_video_height: Gtk.SpinButton = common.builder.get_object('sbtn_output_video_height')
        if not widget.get_state():
            video_encoder_frame.set_sensitive(False)
            video_encoder_combo.set_sensitive(False)
            chk_scale_video.set_sensitive(False)
            spin_video_width.set_sensitive(False)
            seperator_label.set_sensitive(False)
            spin_video_height.set_sensitive(False)
        else:
            video_encoder_frame.set_sensitive(True)
            video_encoder_combo.set_sensitive(True)
            chk_scale_video.set_sensitive(True)
            spin_video_width.set_sensitive(chk_scale_video.get_active())
            seperator_label.set_sensitive(chk_scale_video.get_active())
            spin_video_height.set_sensitive(chk_scale_video.get_active())
        return

    @staticmethod
    def chk_output_video_scale_toggled_cb(widget: Gtk.CheckButton, *_args) -> None:
        """
        Scale video check box, sets the sensitivities of the width / height widgets.
        :param widget: Gtk.CheckButton: The check box widget.
        :param _args: Ignored.
        :return: None.
        """
        # Get widgets:
        spin_video_width: Gtk.SpinButton = common.builder.get_object('sbtn_output_video_width')
        seperator_label: Gtk.Label = common.builder.get_object('lbl_output_video_x')
        spin_video_height: Gtk.SpinButton = common.builder.get_object('sbtn_output_video_height')
        spin_video_width.set_sensitive(widget.get_active())
        seperator_label.set_sensitive(widget.get_active())
        spin_video_height.set_sensitive(widget.get_active())
        return

    @staticmethod
    def chk_btn_output_cluster_use_local_copy_toggled_cb(widget: Gtk.CheckButton, *_args) -> None:
        """
        Copy video chunk check box, sets the verify copy sensitivity.
        :param widget: Gtk.CheckButton
        :param _args: Ignored.
        :return: None
        """
        # Get the verify copy widget and set it sensitivity based on this buttons value.
        verify_check: Gtk.CheckButton = common.builder.get_object('chk_output_cluster_verify_copy')
        verify_check.set_sensitive(widget.get_active())
        return

    @staticmethod
    def btn_add_host_clicked_cb(widget: Gtk.Button, *_args) -> None:
        """
        Add host button clicked callback.  Brings up the add host dialog, contains add host logic.
        :param widget: Gtk.Button: The add host button.
        :param _args: Ignored.
        :return: None.
        """
        # Get the objects we're going to use:
        add_host_dialog: Gtk.Dialog = common.builder.get_object('add_host_dialog')  # The dialog window.
        name_entry: Gtk.Entry = common.builder.get_object('ent_add_host_name')  # The name property / key.
        address_entry: Gtk.Entry = common.builder.get_object('ent_add_host_ip')  # The IP Address.
        port_spin: Gtk.SpinButton = common.builder.get_object('sbtn_add_host_port')  # The port number.
        secret_entry: Gtk.Entry = common.builder.get_object('ent_add_host_secret')  # The shared secret for this host.

        # Clear the values in the entries since we're adding new, not editing:
        name_entry.set_text('')
        address_entry.set_text('')
        address_entry.set_text('')
        port_spin.set_value(65500)
        secret_entry.set_text('')

        # Run the dialog
        while True:
            response: Gtk.ResponseType = add_host_dialog.run()

            if response == Gtk.ResponseType.OK:
                # Gather info from the entries / spin button:
                name: str = name_entry.get_text()
                address: str = address_entry.get_text()
                port: int = port_spin.get_value_as_int()
                secret: str = secret_entry.get_text()

                # Validate the data, shows a popup with an error if data invalid:
                results = common.validate_host_values(name, address, port, secret)
                if not results:
                    continue

                # TODO: Check the connection.



                # All the vars are good, hide the dialog.
                add_host_dialog.hide()
                break

            elif response == Gtk.ResponseType.CANCEL:
                add_host_dialog.hide()
                return

        return

    @staticmethod
    def btn_test_connection_clicked_cb(widget: Gtk.Button, *_args) -> None:
        """
        Test connection button callback.  Run the connection test, and show the results.
        :param widget: Gtk.Button: The test button.
        :param _args: Ignored.
        :return: None
        """
        # Get the widgets we're going to use:
        name_entry: Gtk.Entry = common.builder.get_object('ent_add_host_name')  # The name property / key.
        address_entry: Gtk.Entry = common.builder.get_object('ent_add_host_ip')  # The IP Address.
        port_spin: Gtk.SpinButton = common.builder.get_object('sbtn_add_host_port')  # The port number.
        secret_entry: Gtk.Entry = common.builder.get_object('ent_add_host_secret')  # The shared secret for this host.
        spin_testing: Gtk.Spinner = common.builder.get_object('spin_test')  # The testing spinner.
        img_test_success: Gtk.Image = common.builder.get_object('img_test_success')  # The checkmark image.
        img_test_failed: Gtk.Image = common.builder.get_object('img_test_failed')  # The 'X' image.

        # Start the spinner:
        spin_testing.start()

        # Collect their values:
        name: str = name_entry.get_text()
        address: str = address_entry.get_text()
        port: int = port_spin.get_value_as_int()
        secret: str = secret_entry.get_text()

        # Validate host values, shows a popup with error:
        results = common.validate_host_values(name, address, port, secret)
        if not results:
            img_test_failed.show()
            spin_testing.stop()
            return

        # Test the connection to the server: