from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
import re
import time
import json

driver = webdriver.Edge()
driver.get("https://lawnet.vn/tai-chinh/vb.html")
print(driver.title)
wait = WebDriverWait(driver, 10)
# Các thành viên cần lấy sẽ thuộc từ 3 - 17  
##index-list-result > div > ul > li:nth-child(1) > div > div.align-top.col-lg-9.pr-lg-0 > div > div > div.pl-0.pl-md-2.pr-2.pr-md-0 > a > span
##index-list-result > div > ul > li:nth-child(20) > div > div.align-top.col-lg-9.pr-lg-0 > div > div > div.pl-0.pl-md-2.pr-2.pr-md-0 > a > span
old_content = ""
for page in range(1):

    href_links = []
    for i in range(1, 21):
        element = wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, 
                f"#index-list-result > div > ul > li:nth-child({i}) > div > div.align-top.col-lg-9.pr-lg-0 \
                > div > div > div.pl-0.pl-md-2.pr-2.pr-md-0 > a")
            )
        )
        href_links.append(element.get_attribute('href'))

    with open('links.json', 'w', encoding='utf-8') as f: 
        json.dump(href_links, f, indent=4, ensure_ascii=False)

    #docs = []
    for i, link in enumerate(href_links):
        print(link)
        driver.get(link)
        # name_element = wait.until(
        #     EC.presence_of_element_located(
        #         (By.CSS_SELECTOR, 
        #          "#h1-tit"
        #         )
        #     )
        # )
        element = wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, 
                "#tab-noidung > div > div > div") 
                # #tab-noidung > div > div > div > div.MainContentAll.rawContent-9F052
            )
        )
        #name = name_element.text
        text = element.text
        #docs.append(text)
        #crawl\data\-BTC.pdf
        with open(f"doc{i}.txt", "w", encoding="utf-8") as f:
            f.write(text)


    # driver.get("https://vbpq.mof.gov.vn")
    # anchor_element = wait.until(
    #     EC.presence_of_element_located(
    #         (By.CSS_SELECTOR, 
    #          "#showallData > div:nth-child(3) > div.panel-heading > a > h5")
    #     )
    # )
    # old_content = anchor_element.text 
    # pagination = f'#showallData > div.pagination-angular > div.navbar-right.pagination-detail > ul > li:nth-child({page+4}) > a'
    # # #searchController > div:nth-child(2) > div.col-md-9.pl-md-0 > div.mb-3.paging > ul > li.page-item.active > button 
    # # #searchController > div:nth-child(2) > div.col-md-9.pl-md-0 > div.mb-3.paging > ul > li:nth-child(5) > button 
    # # #searchController > div:nth-child(2) > div.col-md-9.pl-md-0 > div.mb-3.paging > ul > li:nth-child(11) > button
    # print(pagination)
    # pagination_link = wait.until(EC.presence_of_element_located(
    #         (By.CSS_SELECTOR, pagination ) 
    #     ))
    # #//*[@id="showallData"]/div[18]/div[2]/ul/li[4]/a
    # # Thực hiện click bằng JavaScript để đảm bảo sự kiện ng-click được kích hoạt
    # driver.execute_script("arguments[0].click();", pagination_link)
    # # Chờ cho đến khi nội dung của phần tử thay đổi
    # WebDriverWait(driver, 10).until(
    #     lambda driver: driver.find_element(
    #         By.CSS_SELECTOR, "#showallData > div:nth-child(3) > div.panel-heading > a > h5"
    #     ).text != old_content
    # )

driver.quit()