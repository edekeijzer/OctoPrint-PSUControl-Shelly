# OctoPrint PSU Control - Shelly
Adds Shelly support to OctoPrint-PSUControl as a sub-plugin

## Setup
- Install the plugin using Plugin Manager from Settings
- Configure this plugin
- Select this plugin as a Switching and/or Sensing method in [PSU Control](https://github.com/kantlivelong/OctoPrint-PSUControl)

## Configuration
The plugin can be used either with a direct connection to your Shelly or via Shelly Cloud.

### Local connection
* Uncheck the *Use Shelly Cloud* checkbox
* Enter IP address
* If your Shelly is password protected, check *Use authentication* and enter your username and password.

### Shelly Cloud
* Login at [Shelly Cloud](https://my.shelly.cloud/)
* Go to *User Settings > Security > Autorisation Cloud Key*
* Click *Get Key*
* Copy your server address (for example: https://shelly-13-eu.shelly.cloud) to the *Server address* field
* Copy your authorization key (the long random string) to the *Auth key* field
* Go to your Shelly device and click *Settings > Device Information*
* Copy the device ID (the hexadecimal ID, not the numeric part between parentheses) to the *Device ID* field

### Both options
If your Shelly has multiple outputs (Shelly 2, 2.5, 3EM or 4PRO) select the correct output. For Shelly 1, keep it at 0.

## Support
Please check your logs first. If they do not explain your issue, open an issue in GitHub. Please set *octoprint.plugins.psucontrol* and *octoprint.plugins.psucontrol_shelly* to **DEBUG** and include the relevant logs. Feature requests are welcome as well.

## Todo
- [ ] Add descriptions to settings page
- [ ] Add images to documentation
- [ ] Improve transition for cloud mode so it won't send new requests until status is returned.
- [ ] Retrieve Shelly model and set available options accordingly.
- [ ] Add an option to disable switch input to prevent accidental shutdowns.
