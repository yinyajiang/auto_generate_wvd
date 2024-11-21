import os
import subprocess
import uuid
import sys
import shutil
import time

def sdk_path():
    return os.path.join(os.environ['LOCALAPPDATA'], 'Android', 'Sdk')


def emulator_path():
    return os.path.join(sdk_path(), 'emulator', 'emulator.exe')
    

def avdmanager_path():
    return os.path.join(sdk_path(), 'cmdline-tools', 'latest', 'bin', 'avdmanager.bat')


def adb_path():
    return os.path.join(sdk_path(), 'platform-tools', 'adb.exe')


def avd_found(name):
    result = subprocess.run([emulator_path(), "-list-avds"], capture_output=True, text=True)
    if name in result.stdout:
        return True
    return False

def adb_file_exists(file_path):
    cmd = f'adb shell "test -e {file_path} && echo 1 || echo 0"'
    result = subprocess.getoutput(cmd).strip()
    return result == '1' 

def avd_list():
    result = subprocess.run([emulator_path(), "-list-avds"], capture_output=True, text=True)
    return [name.strip() for name in result.stdout.splitlines() if name.strip()]


def avd_delete(name):
    subprocess.run([avdmanager_path(), "delete", "avd", "-n", name]).check_returncode()
    avd_dir = os.path.join(r"C:\Android\.android\avd", f"{name}.avd")
    if os.path.exists(avd_dir):
        shutil.rmtree(avd_dir)


def avd_create(name, k, model):
    subprocess.run([avdmanager_path(), "create", "avd", "-n", name, "-k", k, "-d", model,"--force"]).check_returncode()
    avd_ini_path = os.path.join(r"C:\Android\.android\avd", f"{name}.avd", "config.ini")
    
    # 逐行读取并修改内容
    modified_lines = []
    with open(avd_ini_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip().startswith('hw.keyboard'):
                modified_lines.append('hw.keyboard=yes\n')
            else:
                modified_lines.append(line)
    
    # 写回修改后的内容
    with open(avd_ini_path, 'w', encoding='utf-8') as f:
        f.writelines(modified_lines)
    

def avd_create_new(name, k, model):
    if avd_found(name):
        avd_delete(name)
    avd_create(name, k, model)


def avd_start(name):
    subprocess.Popen([emulator_path(), "-avd", name])


def avd_stop_all():
    has = avd_list()
    subprocess.run([adb_path(), "emu", "kill"])
    if has:
        print("Waiting 30 seconds for AVD to stop...")
        time.sleep(30)
        subprocess.run(["taskkill", "/F", "/IM", "qemu-system-x86_64.exe", "/T"])
        subprocess.run(["taskkill", "/F", "/IM", "emulator", "/T"])


def adb_stop():
    subprocess.run([adb_path(), "kill-server"])
    subprocess.run(["taskkill", "/F", "/IM", "adb.exe", "/T"])


def avd_start_new(k, model):
    avd_name = uuid.uuid4().hex
    avd_create_new(avd_name, k, model)
    avd_start(avd_name)
    print(f"AVD Name: {avd_name}")
    return avd_name


def avd_clear():
    avd_stop_all()
    for avd in avd_list():
        avd_delete(avd)


if __name__ == "__main__":
    if len(sys.argv) < 1:
        print("Usage: python avd_util.py new\n")
        print("Usage: python avd_util.py clear\n")
        exit(1)
    if sys.argv[1] == "new":
        avd_start_new("system-images;android-28;google_apis;x86", "pixel_6")
    elif sys.argv[1] == "clear":
        avd_clear()

