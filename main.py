import automate
import os
import subprocess
import sys
import avd_util
import time
import glob
from pywidevine.device import Device, DeviceTypes
from pathlib import Path
import shutil
import hashlib
import zipfile

def third_dir():
    return os.path.join(os.path.dirname(__file__), "third")

def dumper_dir():
    return os.path.join(third_dir(), "dumper-main")

def start_frida_server():
    frida_files = glob.glob(os.path.join(third_dir(), "frida-server*"))
    if len(frida_files) == 0:
        raise Exception("No frida-server found")

    frida_name = os.path.basename(frida_files[0])
    adb_path = avd_util.adb_path()
    subprocess.run([adb_path, "push", frida_name, "/sdcard"], cwd=third_dir()).check_returncode()
    while not avd_util.adb_file_exists(f"/sdcard/{frida_name}"):
        time.sleep(1)
    shell_cmds = [
        "su",
        f"mv /sdcard/{frida_name} /data/local/tmp",
        f"chmod +x /data/local/tmp/{frida_name}",
        f"/data/local/tmp/{frida_name}"
    ]
    process = subprocess.Popen(
        [adb_path, "shell"],
        stdin=subprocess.PIPE,
        text=True,
        cwd=third_dir()
    )
    process.stdin.write("\n".join(shell_cmds))
    process.stdin.close()


def saveas_wvd(temp_dir, saveas):
    id_files = glob.glob(os.path.join(temp_dir, "*id*"))
    if len(id_files) == 0:
        raise Exception("No id file found")
    id_bytes = Path(id_files[0]).read_bytes()
    private_files = glob.glob(os.path.join(temp_dir, "*private*"))
    if len(private_files) == 0:
        raise Exception("No private file found")
    private_bytes = Path(private_files[0]).read_bytes()

    device = Device(
        type_=DeviceTypes.ANDROID,
        security_level=3,
        flags={},
        private_key=private_bytes,
        client_id=id_bytes
    )
    device.dump(saveas)
    Device.load(saveas)


def start_dumper():
    # https://github.com/lollolong/dumper
    venv_path = os.path.join(dumper_dir(), "venv")
    if not os.path.exists(venv_path):
        subprocess.run([sys.executable, "-m", "venv", "venv"], cwd=dumper_dir())
        subprocess.run([os.path.join(venv_path, "Scripts", "pip.exe"), "install", "-r", "requirements.txt"], cwd=dumper_dir())
    process = subprocess.Popen(
        [os.path.join(venv_path, "Scripts", "python.exe"), "dump_keys.py"],
        stderr=subprocess.PIPE,
        cwd=dumper_dir()
    )
    def wait_dumper():
        for line in iter(process.stderr.readline, b''):
            line = line.decode()
            key = "Key pairs saved at"
            i = line.find(key)
            if i == -1:
                print(f"[dumper]{line}")
                continue
            temp_dir = os.path.join(dumper_dir(), line[i + len(key):].strip())
            print(f"temp_dir: {temp_dir}")
            return temp_dir
        raise Exception("Failed to get temp_dir")

    def terminate_dumper():
        try:
            process.terminate()
        except Exception as e:
            pass
        finally:
            temp_dir = os.path.join(dumper_dir(), "key_dumps")
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

    return terminate_dumper, wait_dumper


def main(wvd_save_path):
    avd_name = avd_util.avd_start_new("system-images;android-28;google_apis;x86", "pixel_6")
    terminate_dumper = None
    try:
        automate.wait_avd_fixed()
        start_frida_server()
        terminate_dumper, wait_dumper = start_dumper()
        automate.aotomate_chrome_open_bitmovin()
        temp_dir = wait_dumper()
        saveas_wvd(temp_dir, wvd_save_path)
    finally:
        if terminate_dumper:
            terminate_dumper()
        avd_util.avd_stop_all()
        avd_util.avd_delete(avd_name)
        if os.path.exists(wvd_save_path):
            print(f"wvd file saved at: {wvd_save_path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python main.py <wvd_save_dir> [count]")
        exit(1)
    wvd_save_dir = os.path.join(sys.argv[1], time.strftime("%Y-%m-%d"))
    count = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    index = 0
    all_wvd_paths = []
    while index < count:
        wvd_path = os.path.join(wvd_save_dir, f"awvd_{index+1}.wvd")
        try:
            main(wvd_path)
            all_wvd_paths.append(wvd_path)
            index += 1
            print("***********************************************\n")
            print(f"generate wvd file success, {index}/{count} \n")
            print(f"dir: {wvd_save_dir} \n")
            print("***********************************************\n")
        except Exception as e:
            print(e)
            print(f"generate wvd file failed, retry...")

    # check same wvd file
    files_md5 = {}
    for p in all_wvd_paths:
        md5 = hashlib.md5(Path(p).read_bytes()).hexdigest()
        if md5 in files_md5:
            raise Exception(f"Found same wvd files")
        else:
            files_md5[md5] = p
    
    # zip wvd files
    zip_path = os.path.join(wvd_save_dir, f"wvd.zip")
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zip_file:
        for p in all_wvd_paths:
            zip_file.write(p, os.path.basename(p), compress_type=zipfile.ZIP_DEFLATED)
    # calc md5
    md5 = hashlib.md5(Path(zip_path).read_bytes()).hexdigest()
    md5_path = zip_path + ".md5"
    Path(md5_path).write_bytes((os.path.basename(zip_path) + ":" + md5).encode())


