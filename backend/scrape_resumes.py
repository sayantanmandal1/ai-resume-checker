from bs4 import BeautifulSoup
import bs4
from selenium import webdriver
import pandas as pd
import hashlib
import os
import time
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service)

job_list = ['HR', 'designer', 'Information-Technology',
            'Teacher', 'Advocate', 'Business-Development',
            'Healthcare', 'Fitness', 'Agriculture', 'BPO', 'Sales', 'Consultant',
            'Digital-Media', 'Automobile', 'Chef', 'Finance',
            'Apparel', 'Engineering', 'Accountant', 'Construction',
            'Public-Relations', 'Banking', 'Arts', 'Aviation']

category = []
link = []

for job in job_list:
    JOB = job.lower()
    for i in range(1, 13):  # Pages 1 to 12
        PAGE = str(i)
        URL = f"https://www.livecareer.com/resume-search/search?jt={JOB}&bg=85&eg=100&comp=&mod=&pg={PAGE}"
        driver.get(URL)
        time.sleep(1)  # Let page load
        aTagsInLi = driver.find_elements(By.CSS_SELECTOR, 'li a')
        for a in aTagsInLi:
            if a.get_attribute('rel') == "ugc":
                category.append(JOB)
                link.append(a.get_attribute('href'))

df = pd.DataFrame()
df["Category"] = category
df["link"] = link

def generate_id(x):
    return int(hashlib.md5(x.encode('utf-8')).hexdigest(), 16)

df["id"] = df["link"].apply(generate_id)

df["Resume"] = ""
df["Raw_html"] = ""

for i in range(df.shape[0]):
    url = df.link[i]
    driver.get(url)
    time.sleep(1)  # Let page load
    page_source = driver.page_source.replace(">", "> ")
    soup = bs4.BeautifulSoup(page_source, 'html.parser')
    div = soup.find("div", {"id": "document"})
    df.at[i, "Raw_html"] = str(div) if div else ""
    try:
        df.at[i, "Resume"] = div.text if div else ""
    except Exception:
        pass

driver.quit()

if not os.path.exists("resumes"):
    os.makedirs("resumes")

df.to_csv("resumes/Resume.csv", index=False)

print("Scraping complete! Resumes saved to 'resumes/Resume.csv'")
