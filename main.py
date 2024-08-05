import os
import time
import random
import requests
from tabulate import tabulate
import markdown
from playwright.sync_api import sync_playwright

# 设置 PushPlus 的 Token 和发送请求的 URL
PUSHPLUS_TOKEN = 'bce8da1c4aff46e2bcb45924b7ea444b'
url_pushplus = 'http://www.pushplus.plus/send'

# 用户名和密码从环境变量中获取
USERNAME = os.environ.get("USERNAME")
PASSWORD = os.environ.get("PASSWORD")

HOME_URL = "https://linux.do/"

class LinuxDoBrowser:
    def __init__(self) -> None:
        self.pw = sync_playwright().start()
        self.browser = self.pw.firefox.launch(headless=True)
        self.context = self.browser.new_context()
        self.page = self.context.new_page()
        self.page.goto(HOME_URL)

    def login(self):
        self.page.click(".login-button .d-button-label")
        time.sleep(2)
        self.page.fill("#login-account-name", USERNAME)
        time.sleep(2)
        self.page.fill("#login-account-password", PASSWORD)
        time.sleep(2)
        self.page.click("#login-button")
        time.sleep(10)
        user_ele = self.page.query_selector("#current-user")
        if not user_ele:
            print("Login failed")
            return False
        else:
            print("Check in success")
            return True

    def click_topic(self):
        for topic in self.page.query_selector_all("#list-area .title"):
            page = self.context.new_page()
            page.goto(HOME_URL + topic.get_attribute("href"))
            time.sleep(3)
            if random.random() < 0.02:  # 100 * 0.02 * 30 = 60
                self.click_like(page)
            time.sleep(3)
            page.close()

    def run(self):
        if not self.login():
            return
        self.click_topic()
        self.print_connect_info()

    def click_like(self, page):
        page.locator(".discourse-reactions-reaction-button").first.click()
        print("Like success")

    def print_connect_info(self):
        page = self.context.new_page()
        page.goto("https://connect.linux.do/")
        rows = page.query_selector_all("table tr")

        info = []

        for row in rows:
            cells = row.query_selector_all("td")
            if len(cells) >= 3:
                project = cells[0].text_content().strip()
                current = cells[1].text_content().strip()
                requirement = cells[2].text_content().strip()
                info.append([project, current, requirement])

        print("--------------Connect Info-----------------")
        print(tabulate(info, headers=["项目", "当前", "要求"], tablefmt="pretty"))

        # 准备推送数据
        markdown_content = markdown.markdown(tabulate(info, headers=["项目", "当前", "要求"], tablefmt="grid"))
        push_data = {
            "token": PUSHPLUS_TOKEN,
            "title": "Connect Info",
            "content": markdown_content,
            "template": "markdown"  # 指定使用 Markdown 格式
        }

        # 发送推送请求到 PushPlus
        response_pushplus = requests.post(url_pushplus, data=push_data)
        
        # 打印推送结果
        print(f"PushPlus推送结果: {response_pushplus.text}")
        
        page.close()

if __name__ == "__main__":
    if not USERNAME or not PASSWORD:
        print("Please set USERNAME and PASSWORD")
        exit(1)
    
    l = LinuxDoBrowser()
    l.run()
