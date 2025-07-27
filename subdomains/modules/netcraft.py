#!/usr/bin/env python3

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from time import sleep
from sys import argv

def netcraft(domain,*args):
    options = Options()
    options.add_experimental_option("detach", True)

    driver = webdriver.Chrome(options=options)

    driver.get(f"https://searchdns.netcraft.com/?host=.{domain}")

    driver.execute_script("""
        while (document.readyState !== 'complete') {
            return;
        }
    """)

    title = driver.execute_script("return document.title;")
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

    try:
        accept_button = driver.find_element(By.XPATH, "//button[contains(@class, 'btn-info') and contains(@class, 'teal')]")
        accept_button.click()
    except NoSuchElementException:
        pass

    while True:
        try:
            table_data = driver.execute_script("""
            const rows = document.querySelectorAll(".results-table tbody tr");
            return Array.from(rows).map(row => 
                Array.from(row.querySelectorAll("td")).map(td => td.innerText.trim())
            );
        """)
            with open("subdomains.netcraft","a") as out:
                out.write("\n".join([i[1] for i in table_data]))
            next_page = driver.find_element(By.CSS_SELECTOR, 'a.btn-info[href*="host="]')
            sleep(3)
            driver.get(next_page.get_attribute("href"))
        except NoSuchElementException:
            driver.quit()
            break


if __name__ == "__main__":
    if len(argv)<2:
        print(f"""Usage:
              {argv[0]} <domain>""")
        exit()
    netcraft(domain=argv[0])