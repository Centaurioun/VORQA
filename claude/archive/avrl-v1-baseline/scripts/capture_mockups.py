#!/usr/bin/env python3
"""Create deterministic reference PNGs before operator signs the eval digest."""
from pathlib import Path
from playwright.sync_api import sync_playwright
from browser_runtime import launch_chromium

ROOT=Path(__file__).resolve().parents[1]
MOCK=ROOT/'specs'/'example-signup'/'mockups'


def main():
    with sync_playwright() as playwright:
        browser=launch_chromium(playwright)
        for name,viewport in [('desktop',{'width':1280,'height':800}),('mobile',{'width':390,'height':844}),('edge',{'width':1280,'height':800})]:
            page=browser.new_page(viewport=viewport,device_scale_factor=1,color_scheme='light',locale='en-US',reduced_motion='reduce')
            page.set_content((MOCK/(name+'.html')).read_text(),wait_until='load')
            page.screenshot(path=str(MOCK/(name+'.png')),full_page=True,animations='disabled')
            page.close()
            print('CAPTURED',name,viewport)
        browser.close()

if __name__=='__main__':main()
