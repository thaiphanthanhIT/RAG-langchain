from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
import re
import time

driver = webdriver.Edge()
driver.get("https://vbpq.mof.gov.vn")
print(driver.title)
wait = WebDriverWait(driver, 10)
# Các thành viên cần lấy sẽ thuộc từ 3 - 17 
old_content = ""
for page in range(2):

    href_links = []
    for i in range(3, 18):
        element = wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, 
                f"#showallData > div:nth-child({i}) > div.panel-body > div.action-content > div > a.taive-hover")
            )
        )
        href_links.append(element.get_attribute('href'))

    docs = []
    for link in href_links:
        driver.get(link)
        element = wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, 
                "#taive > table > tbody > tr > td > a")
            )
        )
        name = element.get_attribute('download')
        name = f'crawl/data/' + re.sub(r'\/','_', name)
        link = element.get_attribute('href')
        docs.append((name, link))
        

    for _, (name, link) in enumerate(docs): 
        print(f"Name: {name}, link: {link}")
        response = requests.get(link)
        if response.status_code == 200: 
            with open(name, 'wb') as f:
                f.write(response.content)
                print(f"Download {name} successfully!")
        else:
            print(f"Fet error {response.status_code}")


    driver.get("https://vbpq.mof.gov.vn")
    anchor_element = wait.until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, 
             "#showallData > div:nth-child(3) > div.panel-heading > a > h5")
        )
    )
    old_content = anchor_element.text 
    pagination = f'#showallData > div.pagination-angular > div.navbar-right.pagination-detail > ul > li:nth-child({page+4}) > a'
    print(pagination)
    pagination_link = wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, pagination ) 
        ))
    #//*[@id="showallData"]/div[18]/div[2]/ul/li[4]/a
    # Thực hiện click bằng JavaScript để đảm bảo sự kiện ng-click được kích hoạt
    driver.execute_script("arguments[0].click();", pagination_link)
    # Chờ cho đến khi nội dung của phần tử thay đổi
    WebDriverWait(driver, 10).until(
        lambda driver: driver.find_element(
            By.CSS_SELECTOR, "#showallData > div:nth-child(3) > div.panel-heading > a > h5"
        ).text != old_content
    )

driver.quit()