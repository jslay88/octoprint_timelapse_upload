# coding=utf-8
from __future__ import absolute_import
from os.path import basename
from typing import Optional

from .client_discovery import discover_clients
from .clients.base import BaseClient

import octoprint.plugin
from octoprint.events import Events


class TimelapseUploadPlugin(
    octoprint.plugin.StartupPlugin,
    octoprint.plugin.SettingsPlugin,
    octoprint.plugin.AssetPlugin,
    octoprint.plugin.TemplatePlugin,
    octoprint.plugin.EventHandlerPlugin
):
    def __init__(self):
        super(TimelapseUploadPlugin, self).__init__()
        self._clients = dict()
        self.upload_events = dict()

    def _add_upload_event(self, event_name, payload_path_key):
        # make sure the event exists
        if hasattr(Events, event_name):
            event = getattr(Events, event_name)
            if event not in self.upload_events:
                self.upload_events[event] = payload_path_key
            else:
                self._logger.warning('Attempted to add a duplicate movie event: %s', event_name)
        else:
            self._logger.warning('Attempted to add an event that does not exist: %s', event_name)

    def _add_all_upload_events(self):
        # clear the events set
        self.upload_events = dict()
        # add the stock timelapse event
        self.upload_events[Events.MOVIE_DONE] = 'movie'
        # add any additional movie events that are stored within the settings
        for additional_event in self.additional_upload_events:
            self._add_upload_event(additional_event['event_name'], additional_event['payload_path_key'])

    def on_after_startup(self):
        # Render out generator to list
        self._clients = discover_clients()
        # Add in upload events
        self._add_all_upload_events()
        print(self.client)

    def on_settings_save(self, data):
        self._logger.info(f'Saving settings: {data}')
        octoprint.plugin.SettingsPlugin.on_settings_save(self, data)
        # the settings have changed, reload the movie events
        self._add_all_upload_events()

    def get_settings_defaults(self):
        return dict(
            client=None,
            delete_after_upload=False,
            additional_upload_events=[
                {
                    'event_name': 'PLUGIN_OCTOLAPSE_MOVIE_DONE',
                    'payload_path_key': 'movie'
                },
                {
                    'event_name': 'PLUGIN_OCTOLAPSE_SNAPSHOT_ARCHIVE_DONE',
                    'payload_path_key': 'archive'
                }
            ]
        )

    def get_template_configs(self):
        return [
            dict(type='settings', custom_bindings=True, template='timelapse_upload_settings.jinja2')
        ]

    @property
    def delete_after_upload(self):
        return self._settings.get_boolean(['delete_after_upload'])

    @property
    def additional_upload_events(self):
        return self._settings.get(['additional_upload_events'])

    @property
    def client(self) -> Optional[BaseClient]:
        client = self._settings.get(['client'])
        if not client:
            return None
        self._logger.warning(f"Settings Client: {client}")
        self._logger.warning(f"Settings Client Config: {self._settings.get(['client_config'])}")
        return self._clients[client](self._settings.get(['client_config']))

    def get_assets(self):
        return {
            "js": ["js/timelapse_upload.js"],
            "css": ["css/timelapse_upload.css"],
            "less": ["less/timelapse_upload.less"]
        }

    def get_update_information(self):
        return {
            "timelapse_upload": {
                "displayName": "Timelapse Upload",
                "displayVersion": self._plugin_version,

                # version check: github repository
                "type": "github_release",
                "user": "jslay88",
                "repo": "octoprint_timelapse_upload",
                "current": self._plugin_version,

                # update method: pip
                "pip": "https://github.com/jslay88/octoprint_timelapse_upload/archive/{target_version}.zip",
            }
        }

    def on_event(self, event, payload):
        if event in self.upload_events:
            payload_path_key = self.upload_events[event]
            if payload_path_key in payload:
                file_path = payload[payload_path_key]
                file_name = basename(file_path)
                self._plugin_manager.send_plugin_message(
                    self._identifier, {'type': 'upload-start', 'file_name': file_name}
                )
                try:
                    if self.client.upload(file_path):
                        self._plugin_manager.send_plugin_message(
                            self._identifier, {'type': 'upload-success', 'file_name': file_name}
                        )
                    else:
                        raise Exception("Client returned False!")
                except Exception as e:
                    self._logger.error(e)
                    self._logger.error(f"Client failed to upload! See logs.")
                    self._plugin_manager.send_plugin_message(
                        self._identifier, {'type': 'upload-failed', 'file_name': file_name}
                    )
            else:
                self._plugin_manager.send_plugin_message(
                    self._identifier, {'type': 'upload-failed', 'file_name': "UNKNOWN"}
                )
                self._logger.error(f"Unable to find the '{payload_path_key}' key within the {event} event payload.")


# If you want your plugin to be registered within OctoPrint under a different name than what you defined in setup.py
# ("OctoPrint-PluginSkeleton"), you may define that here. Same goes for the other metadata derived from setup.py that
# can be overwritten via __plugin_xyz__ control properties. See the documentation for that.
__plugin_name__ = "Timelapse Upload"


# Set the Python version your plugin is compatible with below. Recommended is Python 3 only for all new plugins.
# OctoPrint 1.4.0 - 1.7.x run under both Python 3 and the end-of-life Python 2.
# OctoPrint 1.8.0 onwards only supports Python 3.
__plugin_pythoncompat__ = ">=3.7,<4"  # Only Python 3


def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = TimelapseUploadPlugin()

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information
    }
