import pyautogui
import time
import os


def wait_for_screen(element, max_seconds=100, return_region=False, **kwargs):
    start_time = time.time()
    while True:
        try:
            locate = pyautogui.locateOnScreen(element, **kwargs)
            if locate:
                return (locate.left,locate.top,locate.width,locate.height) if return_region else locate
        except Exception as e:
            time.sleep(1)
        if time.time() - start_time > max_seconds:
            raise Exception(f"wait for {element} timeout")
        
def wait_and_click(element, max_seconds=100, **kwargs):
    locate = wait_for_screen(element, max_seconds, **kwargs)
    x,y = pyautogui.center(locate)
    pyautogui.click(x,y)


def screenshot_path(name):
    path = os.path.join(os.path.dirname(__file__), f"screenshot\\{name}")
    return path


def start_chrome():
    regionApps = wait_for_screen(screenshot_path("avd_apps.png"), return_region=True)
    wait_and_click(screenshot_path("avd_chrome.png"), region=regionApps)
    chrome_region = wait_for_screen(screenshot_path(r"chrome_step\region.png"), return_region=True)
    print(f"chrome region: {chrome_region}")
    return chrome_region


def wait_avd_fixed():
    wait_for_screen(screenshot_path("avd_apps.png"), max_seconds=300)
    wait_and_click(screenshot_path("avd_fix.png"))


def aotomate_chrome_open_bitmovin():
    chrome_region = start_chrome()
    wait_and_click(screenshot_path(r"chrome_step\1.png"), region=chrome_region)
    wait_and_click(screenshot_path(r"chrome_step\2.png"), region=chrome_region)
    wait_and_click(screenshot_path(r"chrome_step\3.png"), region=chrome_region)
    wait_and_click(screenshot_path(r"chrome_step\4.png"), region=chrome_region)
    wait_and_click(screenshot_path(r"chrome_step\5.png"), region=chrome_region)
    wait_for_screen(screenshot_path(r"chrome_step\keys.png"), region=chrome_region)
    time.sleep(1)
    pyautogui.write("https://bitmovin.com/demos/drm", interval=0.3)
    pyautogui.press("enter")
    regionDialog = wait_for_screen(screenshot_path(r"drm_step\1.png"), return_region=True, region=chrome_region)
    wait_and_click(screenshot_path(r"drm_step\2.png"), region=regionDialog)
    wait_and_click(screenshot_path(r"drm_step\3.png"), region=chrome_region)
    time.sleep(1.5)
    pyautogui.scroll(-500)
