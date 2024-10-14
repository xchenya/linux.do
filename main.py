import os
import time
import random
import requests
from tabulate import tabulate

from playwright.sync_api import sync_playwright

# 设置 PushPlus 的 Token 和发送请求的 URL
PUSHPLUS_TOKEN = os.environ.get("PUSHTOKEN")
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

    def scroll_down(self):
        # 向下滚动以触发懒加载
        self.page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
        time.sleep(2)  # 等待加载新内容

    def click_topic(self):
        max_browse_count = 500  # 希望浏览的帖子数
        browsed_topics = []  # 存储浏览的帖子
        total_count = 0

        while total_count < max_browse_count:
            time.sleep(5)  # 确保页面加载完成
            topics = self.page.query_selector_all("#list-area .title")

            if not topics:
                print("未找到任何帖子，请检查选择器或页面加载情况。")
                break

            # 排除已经浏览过的帖子
            new_topics = [t for t in topics if t not in browsed_topics]
            browsed_topics.extend(new_topics)

            if not new_topics:
                print("没有加载出更多帖子。")
                break

            for topic in new_topics:
                if total_count >= max_browse_count:
                    break

                page = self.context.new_page()
                page.goto(HOME_URL + topic.get_attribute("href"))
                time.sleep(3)
                
                if random.random() < 0.02:  # 保持 2% 点赞几率
                    self.click_like(page)

                total_count += 1
                time.sleep(3)
                page.close()

            print(f"已浏览 {total_count} 个帖子")

            # 滚动以加载更多内容
            self.scroll_down()

        print(f"总共浏览了 {total_count} 个帖子")

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

        # 使用 HTML 表格格式化数据，包含标题
        html_table += "<caption>在过去 100 天内：</caption>"
        html_table = "<table style='border-collapse: collapse; width: 100%; border: 1px solid black;'>"
        html_table += "<caption>在过去 100 天内：</caption>"
        html_table += "<tr><th style='border: 1px solid black; padding: 8px;'>项目</th><th style='border: 1px solid black; padding: 8px;'>当前</th><th style='border: 1px solid black; padding: 8px;'>要求</th></tr>"

        for row in info:
            html_table += "<tr>"
            for cell in row:
                html_table += f"<td style='border: 1px solid black; padding: 8px;'>{cell}</td>"
            html_table += "</tr>"

        html_table += "</table>"

        # 准备推送数据
        push_data = {
            "token": PUSHPLUS_TOKEN,
            "title": "Linux.do 自动签到",
            "content": html_table,
            "template": "html"  # 指定使用 HTML 格式
        }

        # 发送推送请求到 PushPlus
        response_pushplus = requests.post(url_pushplus, data=push_data)
        
        page.close()

if __name__ == "__main__":
    if not USERNAME or not PASSWORD:
        print("Please set USERNAME and PASSWORD")
        exit(1)
    
    l = LinuxDoBrowser()
    l.run()
