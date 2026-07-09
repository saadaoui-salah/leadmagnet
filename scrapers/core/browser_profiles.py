import random
import re

from fake_useragent import UserAgent

_ua = UserAgent()

CHROME_IMPERSONATE = ["chrome136", "chrome142", "chrome145", "chrome146"]
FIREFOX_IMPERSONATE = ["firefox144", "firefox147"]
SAFARI_IMPERSONATE = ["safari180", "safari184"]
EDGE_IMPERSONATE = ["edge101"]


def _detect_browser(ua_string):
    ua = ua_string.lower()
    if "edg/" in ua or "edge/" in ua:
        return "edge"
    if "firefox/" in ua:
        return "firefox"
    if "safari/" in ua and "chrome" not in ua and "chromium" not in ua:
        return "safari"
    if "chrome/" in ua or "chromium/" in ua:
        return "chrome"
    return "chrome"


def _detect_os(ua_string):
    ua = ua_string.lower()
    if "windows" in ua:
        return "Windows"
    if "mac os" in ua or "macintosh" in ua:
        return "macOS"
    if "linux" in ua:
        return "Linux"
    if "cros" in ua:
        return "Chrome OS"
    return "Windows"


def _build_sec_ch_ua(ua_string, os_name):
    match = re.search(r"Chrome/(\d+)", ua_string)
    if not match:
        return None, None, None

    version = match.group(1)
    brands = [
        f'"Chromium";v="{version}"',
        f'"Google Chrome";v="{version}"',
        '"Not.A/Brand";v="99"',
    ]

    platform = f'"{os_name}"'
    return "; ".join(brands), "?0", platform


def get_random_profile():
    browser_type = random.choices(
        ["chrome", "firefox", "safari", "edge"],
        weights=[50, 20, 20, 10],
        k=1,
    )[0]

    if browser_type == "chrome":
        ua_string = _ua.random
        if "Chrome/" not in ua_string:
            ua_string = _ua.chrome
        impersonate = random.choice(CHROME_IMPERSONATE)
    elif browser_type == "firefox":
        ua_string = _ua.firefox
        impersonate = random.choice(FIREFOX_IMPERSONATE)
    elif browser_type == "safari":
        ua_string = _ua.safari
        impersonate = random.choice(SAFARI_IMPERSONATE)
    else:
        ua_string = _ua.edge
        impersonate = random.choice(EDGE_IMPERSONATE)

    os_name = _detect_os(ua_string)
    sec_ch_ua, sec_ch_ua_mobile, sec_ch_ua_platform = _build_sec_ch_ua(ua_string, os_name)

    return {
        "impersonate": impersonate,
        "user_agent": ua_string,
        "sec_ch_ua": sec_ch_ua,
        "sec_ch_ua_mobile": sec_ch_ua_mobile,
        "sec_ch_ua_platform": sec_ch_ua_platform,
    }


def get_headers():
    profile = get_random_profile()
    headers = {
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.9",
        "dnt": "1",
        "origin": "https://www.zillow.com",
        "referer": "https://www.zillow.com/homes/for_rent/",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": profile["user_agent"],
    }
    if profile["sec_ch_ua"]:
        headers["sec-ch-ua"] = profile["sec_ch_ua"]
        headers["sec-ch-ua-mobile"] = profile["sec_ch_ua_mobile"]
        headers["sec-ch-ua-platform"] = profile["sec_ch_ua_platform"]
    return headers
