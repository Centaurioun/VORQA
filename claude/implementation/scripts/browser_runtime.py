"""Resolve an installed Chromium without silently downloading or disabling security flags."""
import os
from pathlib import Path
import shutil


def launch_chromium(playwright):
    configured=os.environ.get('AVRL_CHROMIUM_EXECUTABLE')
    if configured:
        path=Path(configured)
        if not path.is_file():raise ValueError('AVRL_CHROMIUM_EXECUTABLE is not a file')
        return playwright.chromium.launch(headless=True,executable_path=str(path))
    try:
        return playwright.chromium.launch(headless=True)
    except Exception as exc:
        found=shutil.which('chromium') or shutil.which('google-chrome-stable') or shutil.which('google-chrome')
        if found:return playwright.chromium.launch(headless=True,executable_path=found)
        raise RuntimeError('Chromium unavailable. Run: python3 -m playwright install chromium') from exc
