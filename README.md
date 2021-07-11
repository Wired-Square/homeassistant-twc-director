# Home Assistant Tesla Wall Charger Integration

## Use at your own risk

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

## Installation

This integration has been tested against Home Assistant 2021.5.0. The twc-director library at https://github.com/Wired-Square/twc-director is a required dependency, for now it needs to be manually installed into the Home Assistant virtual environment.

The integration can be installed by cloning this repository into the Home Assistant ```custom_components``` directory.

Assuming Home Assistant is running on a Raspberry Pi using the installation guide at https://www.home-assistant.io/installation/raspberrypi for the Home Assistant Core version, the following commands could be used to install the integration. Alter as needed to suit your installation.
```bash
sudo su - homeassistant
cd /srv/homeassistant/data

# If the custom_components directory doesn't exist, create it
mkdir custom_components

# Clone repo into custom_components directory
git clone https://github.com/Wired-Square/homeassistant-twc-director.git twcdirector
```

Once Home Assistant has been restarted the integration can be activated under Configuration -> Integrations -> "+ Add Integration"
Search for twc, an integration with the name "Tesla Wall Charger Director" will appear, there is no logo yet.

You will be asked two questions, select the device name from the list and then set the maximum shared current (not currently used) in 100ths of an amp, for example 3200 for 32A. This will be made more user-friendly after implementing the current sharing feature. 

