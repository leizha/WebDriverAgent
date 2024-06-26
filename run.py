import subprocess
import signal
import sys
import re
import json
import argparse

parser = argparse.ArgumentParser(description="Get device ID for xcode")
parser.add_argument('--device_id', type=str, help='Specify a device ID to use', required=False)
args = parser.parse_args()

device_id = args.device_id

# otherwise use the most recent used device in xcode
if not device_id:
    cmd = "plutil -extract DVTDevicesWindowControllerSelectedDeviceIdentifier raw ~/Library/Preferences/com.apple.dt.Xcode.plist"
    result = subprocess.run(cmd, shell=True, capture_output=True)
    result.check_returncode()

    device_id = result.stdout.decode().strip()
    assert len(device_id) > 0

print("🚨device id:", device_id)
cmd = f"xcodebuild test -allowProvisioningUpdates -project WebDriverAgent.xcodeproj -scheme WebDriverAgentRunner -destination 'platform=iOS,id={device_id}'"

child_process = subprocess.Popen(
    cmd,
    shell=True,
    stdout=subprocess.PIPE,
    text=True,
    bufsize=1,
    universal_newlines=True,
)


def kill(sig, frame):
    print("💀 killing the child process")

    child_process.send_signal(signal.SIGKILL)
    sys.exit(0)


# make sure we kill the child process on ctrl+C
signal.signal(signal.SIGINT, kill)
signal.signal(signal.SIGTERM, kill)

for line in child_process.stdout:
    print(line)
    # WDA starts the http server and logs its ip and port
    m = re.search(r"ServerURLHere->http://([\.\d]+):(\d+)<-ServerURLHere", line)
    if m is not None:
        wda_host, wda_port = m.group(1), m.group(2)
        print("🔥wda http server", wda_host, wda_port)
        with open("/tmp/wda.json", "w") as f:
            json.dump({"host": wda_host, "port": wda_port}, f)
