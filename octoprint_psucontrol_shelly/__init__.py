# coding=utf-8
from __future__ import absolute_import

__author__ = "Erik de Keijzer <erik.de.keijzer@gmail.com>"
__license__ = "GNU Affero General Public License http://www.gnu.org/licenses/agpl.html"
__copyright__ = "Copyright (C) 2021 Erik de Keijzer - Released under terms of the AGPLv3 License"

import octoprint.plugin
import requests
from requests.auth import HTTPBasicAuth, HTTPDigestAuth
import re as regex

class PSUControl_Shelly(
    octoprint.plugin.StartupPlugin,
    octoprint.plugin.RestartNeedingPlugin,
    octoprint.plugin.TemplatePlugin,
    octoprint.plugin.SettingsPlugin,
):

    def __init__(self):
        self.config = dict()
        self.transition = False

    def get_settings_defaults(self):
        return dict(
            use_cloud = False,
            ng_device = False,
            server_address = '',
            auth_key = '',
            device_id = '',
            local_address = '',
            enable_auth = False,
            username = '',
            password = '',
            output = 0,
        )

    def on_settings_initialized(self):
        self.reload_settings()

    def reload_settings(self):
        for k, v in self.get_settings_defaults().items():
            if type(v) == str:
                v = self._settings.get([k])
            elif type(v) == int:
                v = self._settings.get_int([k])
            elif type(v) == float:
                v = self._settings.get_float([k])
            elif type(v) == bool:
                v = self._settings.get_boolean([k])

            self.config[k] = v
            self._logger.debug("{}: {}".format(k, v))

    def on_startup(self, host, port):
        psucontrol_helpers = self._plugin_manager.get_helpers("psucontrol")
        if not psucontrol_helpers or 'register_plugin' not in psucontrol_helpers.keys():
            self._logger.warning("The version of PSUControl that is installed does not support plugin registration.")
            return

        self._logger.debug("Registering plugin with PSUControl")
        psucontrol_helpers['register_plugin'](self)

    def send(self, url, data=None, auth=None):
        response = None
        try:
            if data:
                response = requests.post(url, auth=auth, data=data)
            else:
                response = requests.get(url, auth=auth)
        except (
                requests.exceptions.InvalidURL,
                requests.exceptions.ConnectionError
        ):
            self._logger.error("Unable to communicate with server. Check settings.")
        except Exception:
            self._logger.exception("Exception while making API call")
        else:
            # if data:
            #     self._logger.debug("url={}, data={}, status_code={}, text={}".format(url, data, response.status_code, response.text))
            # else:
            #     self._logger.debug("url={}, status_code={}, text={}".format(url, response.status_code, response.text))
            self._logger.debug("url={}, status_code={}, text={}".format(url, response.status_code, response.text))

            if response.status_code == 401:
                self._logger.warning("Server returned 401 Unauthorized. Check username/password or API key.")
                response = None
            elif response.status_code == 400:
                self._logger.warning("Server returned 400 Bad Request. Check Device ID.")
                response = None

        return response

    def change_psu_state(self, state):
        if self.transition:
            # This one is mostly for the Shelly Cloud API which is rather slow.
            self._logger.info("Still in transition between sending and receiving change, not sending command.")
            return

        output = self.config['output']

        auth = None
        data = None

        if self.config['use_cloud']:
            url = self.config['server_address'] + '/device/relay/control'
            url = url if regex.match('^http[s]*:\/\/', url) else 'https://' + url

            data = dict(
                auth_key = self.config['auth_key'],
                id = self.config['device_id'],
                turn = state,
                channel = str(output),
            )
            sensing_method = self._settings.global_get(['plugins', 'psucontrol', 'sensingMethod'])
            sensing_plugin = self._settings.global_get(['plugins', 'psucontrol', 'sensingPlugin'])
            if sensing_method == "PLUGIN" and sensing_plugin == "psucontrol_shelly":
                self._logger.debug("PSUControl is using us for sensing")
                self.transition = True

        else:
            url = self.config['local_address'] + '/relay/' + str(output) + '?turn=' + state
            url = url if regex.match('^http[s]*:\/\/', url) else 'http://' + url

            if self.config['enable_auth']:
                if self.config['ng_device']:
                    auth = HTTPDigestAuth(self.config['username'], self.config['password'])
                else:
                    auth = HTTPBasicAuth(self.config['username'], self.config['password'])

        self.transition = True
        self.send(url=url, data=data, auth=auth)

    def turn_psu_on(self):
        self._logger.debug("Switching PSU On")
        self.change_psu_state('on')

    def turn_psu_off(self):
        self._logger.debug("Switching PSU Off")
        self.change_psu_state('off')

    def get_psu_state(self):
        self.transition = False
        output = self.config['output']

        auth = None
        data = None

        if self.config['use_cloud']:
            url = self.config['server_address'] + '/device/status'
            url = url if regex.match('^http[s]*:\/\/', url) else 'https://' + url

            data = dict(
                auth_key = self.config['auth_key'],
                id = self.config['device_id'],
            )
        else:
            url = self.config['local_address'] + '/relay/' + str(output)
            url = url if regex.match('^http[s]*:\/\/', url) else 'http://' + url

            if self.config['enable_auth']:
                if self.config['ng_device']:
                    auth = HTTPDigestAuth(self.config['username'], self.config['password'])
                else:
                    auth = HTTPBasicAuth(self.config['username'], self.config['password'])

        response = self.send(url=url, data=data, auth=auth)
        if not response:
            return False
        json_data = response.json()

        status = None
        try:
            if self.config['use_cloud']:
                status = json_data['data']['device_status']['relays'][output]['ison']
            else:
                status = json_data['ison']
        except KeyError:
            pass

        if status == None:
            self._logger.error("Unable to determine status. Check settings.")
            status = False

        return status

    def on_settings_save(self, data):
        octoprint.plugin.SettingsPlugin.on_settings_save(self, data)
        self.reload_settings()

    def get_settings_version(self):
        return 1

    def on_settings_migrate(self, target, current=None):
        pass

    def get_template_configs(self):
        return [
            dict(type="settings", custom_bindings=False)
        ]

    def get_update_information(self):
        return dict(
            psucontrol_shelly=dict(
                displayName="PSU Control - Shelly",
                displayVersion=self._plugin_version,

                # version check: github repository
                type="github_release",
                user="edekeijzer",
                repo="OctoPrint-PSUControl-Shelly",
                current=self._plugin_version,

                # update method: pip w/ dependency links
                pip="https://github.com/edekeijzer/OctoPrint-PSUControl-Shelly/archive/{target_version}.zip"
            )
        )

__plugin_name__ = "PSU Control - Shelly"
__plugin_pythoncompat__ = ">=3,<4"

def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = PSUControl_Shelly()

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information
    }