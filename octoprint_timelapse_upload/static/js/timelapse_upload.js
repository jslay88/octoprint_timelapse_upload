/*
 * View model for OctoPrint-Timelapse-Upload
 *
 * Author: Justin Slay
 * License: AGPLv3
 */
$(function() {
    // A custom ViewModel for holding custom upload events
    function AdditionalUploadEventViewModel(event_name, payload_path_key){
        let self = this;
        self.event_name = ko.observable(event_name);
        self.payload_path_key = ko.observable(payload_path_key);
    }
    function TimelapseUploadSettingsViewModel(parameters) {
        let self = this;

        self.settings = parameters[0];
        self.plugin_settings = null;

        self.onBeforeBinding = function() {
            // Make plugin setting access a little more terse
            self.plugin_settings = self.settings.settings.plugins.timelapse_upload;
        };
        // Add a custom event
        self.addUploadEvent = function() {
            self.plugin_settings.additional_upload_events.push(
                new AdditionalUploadEventViewModel("","")
            );
        };
        // Remove a custom event
        self.removeUploadEvent = function(index) {
            self.plugin_settings.additional_upload_events.splice(index, 1);
        };

        self.Popups = {};

        // Listen for plugin messages
        // This could probably be made a bit simpler.
        self.onDataUpdaterPluginMessage = function (plugin, data) {
            if (plugin !== "timelapse_upload") {
                return;
            }
            let popup_options = null
            switch (data.type) {
                case 'upload-start':
                {
                    popup_options = {
                        title: 'Uploading to Dropbox...',
                        text: '\'' + data.file_name + '\' is uploading to dropbox now.',
                        type: 'info',
                        hide: true,
                        desktop: {
                            desktop: true
                        }
                    };
                    // Show at most one of these at a time.
                    self.displayPopupForKey(popup_options,data.type, [data.type]);
                    break;
                }
                case 'upload-success':
                {
                    popup_options = {
                        title: 'Dropbox upload complete!',
                        text: '\'' + data.file_name + '\' was uploaded to Dropbox successfully!.',
                        type: 'success',
                        hide: false,
                        desktop: {
                            desktop: true
                        }
                    };
                     self.displayPopup(popup_options);
                     // Close the upload-start popup if it hasn't closed already to keep things clean
                     self.closePopupsForKeys('upload-start');
                    break;
                }
                case 'upload-failed':
                {
                    popup_options = {
                        title: 'Droopbox upload failed!',
                        text: '\'' + data.file_name + '\' failed to upload to Dropbox!  Please check plugin_timelapse_upload.log for more details.',
                        type: 'error',
                        hide: false,
                        desktop: {
                            desktop: true
                        }
                    };
                     self.displayPopup(popup_options);
                     // Close the upload-start popup if it hasn't closed already to keep things clean
                     self.closePopupsForKeys('upload-start');
                    break;
                }
                case 'delete-failed':
                {
                    popup_options = {
                        title: 'Delete After Dropbox Upload failed!',
                        text: '\'' + data.file_name + '\' could not be deleted.  Please check plugin_timelapse_upload.log for more details.',
                        type: 'error',
                        hide: false,
                        desktop: {
                            desktop: true
                        }
                    };
                     self.displayPopup(popup_options);
                     // No need to close the upload-start popup if it hasn't closed already here, since the success/fail
                    // popup will take care of that!
                    break;
                }
                defalut:
                    console.error("timelapse_upload - An unknown plugin message type of " + data.type + "was received.");
                    break;
            }
        };

        self.displayPopup = function(options)
        {
            options.width = '450px';
            new PNotify(options);
        };

        // Show at most one popup for a given key, close any popups with the keys provided.
        self.displayPopupForKey = function (options, popup_key, remove_keys) {
            self.closePopupsForKeys(remove_keys);
            options.width = '450px';
            let popup = new PNotify(options);
            self.Popups[popup_key] = popup;
            return popup;
        };

        self.closePopupsForKeys = function (remove_keys) {
            if (!$.isArray(remove_keys)) {
                remove_keys = [remove_keys];
            }
            for (let index = 0; index < remove_keys.length; index++) {
                let key = remove_keys[index];
                if (key in self.Popups) {
                    let notice = self.Popups[key];
                    if (notice.state === "opening") {
                        notice.options.animation = "none";
                    }
                    notice.remove();
                    delete self.Popups[key];
                }
            }
        };
    }

    /* view model class, parameters for constructor, container to bind to
     * Please see http://docs.octoprint.org/en/master/plugins/viewmodels.html#registering-custom-viewmodels for more details
     * and a full list of the available options.
     */
    OCTOPRINT_VIEWMODELS.push({
        construct: TimelapseUploadSettingsViewModel,
        // ViewModels your plugin depends on, e.g. loginStateViewModel, settingsViewModel, ...
        dependencies: [ "settingsViewModel" ],
        // Elements to bind to, e.g. #settings_plugin_timelapse_upload, #tab_plugin_timelapse_upload, ...
        elements: [ "#timelapse_upload_settings" ]
    });
});
