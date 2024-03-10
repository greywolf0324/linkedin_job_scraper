import requests
from bs4 import BeautifulSoup
import pandas as pd
from selenium import webdriver
import time
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import undetected_chromedriver as uc
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
import boto3
from datetime import datetime
from io import StringIO

cli = boto3.client('s3')

def scrape(page, job_title, job_location):
    job_title = job_title.replace(" ", "%20")
    job_location = job_location.replace(" ", "%20")
    url =f'https://www.linkedin.com/jobs/search?keywords={job_title}&location={job_location}&geoId=&trk=public_jobs_jobs-search-bar_search-submit&position=1&pageNum={page}'
    headers = {'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'}
    r = requests.get(url, headers)
    soup = BeautifulSoup(r.content, 'lxml')
    return soup

def main_scraper(soup):
    joblist = []
    jobs = soup.find_all('div', class_="base-card relative w-full hover:no-underline focus:no-underline base-card--link base-search-card base-search-card--link job-search-card")
    print(len(jobs), "_+")
    for i, item in enumerate(jobs):
        title = item.find('a').text.strip()
        company = item.find('h4').text.strip()
        link = item.a['href']
        location = item.find('span', class_='job-search-card__location').text.strip()
        job_posted = item.find('time', class_='job-search-card__listdate')
        if job_posted is not None:
            time_posted = job_posted.text.strip()
            job = {
                'Title': title,
                'Link': link,
                'Company': company,
                'Location': location,
                'Job_posted': time_posted
            }

            # Add job description scraping logic here
            # Navigate to the job posting page and scrape the description
            apply_link = f'{link}'
            print(apply_link)
            description_soup = scrape_job_description(apply_link)

            # Sleeping randomly
            time.sleep(random.choice(list(range(1, 3))))
            print("-----------------------------------------------------------")
            print(description_soup)
            print("-----------------------------------------------------------")
            try:
                job_description = description_soup.find(
                    "div", class_="description__text description__text--rich"
                ).text.strip()
            except AttributeError:
                job_description = None
            print("***********************************************************************")
            print(job_description)
            print("***********************************************************************")
            # Add job description to the job dictionary
            job['Description'] = job_description

            joblist.append(job)
    return joblist


def scrape_job_description(apply_link):
    # try:
        # driver_path = "C:/Users/HUSSIEN/Downloads/chromedriver-win64/chromedriver.exe"
        # options = webdriver.ChromeOptions()
        chrome_options = Options()
        
        chrome_options.add_argument("--headless=new")
        driver = webdriver.Chrome(options=chrome_options)
        # driver = uc.Chrome(driver_executable_path=ChromeDriverManager().install(), options=chrome_options)
        
        driver.get(apply_link)

        # Wait until the job description element is present on the page
        description_element_present = EC.presence_of_element_located((By.CLASS_NAME, "description__text"))
        
        WebDriverWait(driver, 30).until(description_element_present)

        description_soup = BeautifulSoup(driver.page_source, "html.parser")
        driver.quit()
        return description_soup
    # except Exception as e:
    #     print(f"Error during scraping: {str(e)}")
    #     return None





page = int(input(f'Enter the page number you are looking for: '))
c = scrape(page, "Financial Manager", "United Kingdom")
job_list = main_scraper(c)

# Display the job list
for job in job_list:
    print(job)

# Save job list to CSV
df = pd.DataFrame(job_list)
csv_buffer = StringIO()
df.to_csv(csv_buffer)
cli.put_object(
    Body = csv_buffer.getvalue(),
    Bucket='scrapedjob',
    Key='linkedin_job_list_new.csv'
)
# df.to_csv('Linkedin_job_list_new.csv')
