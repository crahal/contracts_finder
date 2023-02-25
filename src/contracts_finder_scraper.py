import numpy as np
import traceback
import time
import os
import csv
import re
import logging
from bs4 import BeautifulSoup
from datetime import date
from tqdm import tqdm
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


def setup_logging(logpath, today):
    """
    Sets up and returns a logger for the scraper
         Parameters:
            logpath (str): path to our logger
            today (str): today's date to write paths
         Returns:
            logger (logging object): logger to call
    """
    filename = 'contracts_finder_' + str(today) + '.log'
    if os.path.exists(logpath):
        if os.path.isfile(os.path.abspath(
                          os.path.join(logpath, filename))):
            os.remove(os.path.abspath(
                      os.path.join(logpath, filename)))
    else:
        os.makedirs(logpath)
    logger = logging.getLogger('contracts_finder')
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler((os.path.abspath(os.path.join(logpath, filename))))
    fh.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.ERROR)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    logger.addHandler(fh)
    logger.addHandler(ch)
    logger.info('Setting up the logger!')
    return logger


def setup_driver():
    """
    Sets up and returns our selenium webdriver
    Parametres:
        None
    Returns:
        driver: a selenium webdriver
    """
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-software-rasterizer")
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get("https://www.contractsfinder.service.gov.uk/Search")
    return driver

def define_search(driver):
    """
    Define our initial search parametres.
    i.e. for all date ranges and for
    contracts which have already been appointed
         Parameters:
            driver: our selenium webdriver
         Returns:
            None
    """
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    WebDriverWait(driver, 20).\
        until(EC.element_to_be_clickable((By.XPATH, ".//*[contains(text(),'Awarded')]"))).click()
    WebDriverWait(driver, 20).\
        until(EC.element_to_be_clickable((By.XPATH, ".//*[contains(text(),'opportunity')]"))).click()
    WebDriverWait(driver, 20).\
        until(EC.element_to_be_clickable((By.XPATH, ".//*[contains(text(),'Opportunity')]"))).click()
    WebDriverWait(driver, 20).\
        until(EC.element_to_be_clickable((By.XPATH, ".//*[contains(text(),'engagement')]"))).click()
    WebDriverWait(driver, 20).\
        until(EC.element_to_be_clickable((By.XPATH, ".//*[contains(text(),'Search')]"))).click()
    time.sleep(5)


def get_page_data_from_html(html_source_code):
    """
    Get data from each procurement page
    Parameters:
        html_source_code (str): the html of a page grabbed
    Returns:
        page_dict (dict) a dictionary of data to save out
    """
    soup = BeautifulSoup(html_source_code, 'html.parser')
    result_header = soup.find_all(class_="govuk-heading-l break-word")
    page_dict = {}
    commissioner = soup.find_all(lambda tag: tag.name == 'div' and
                                             tag.get('class') == ['standard-col'])[0]
    publication_date = soup.find_all(lambda tag: tag.name == 'div' and
                                                 tag.get('class') == ['search-no-top-margin'])
    contract_details = list(soup.find_all(lambda tag: tag.name == 'div' and
                                                      tag.get('class') == ['content-block']))
    contract_details2 = list([element.get_text() for element in contract_details])
    string_version = "".join(contract_details2)
    string_version = "".join([s for s in string_version.strip().splitlines(True) if s.strip()])
    page_dict['commissioner'] = [element.get_text() for element in commissioner][0]

    refno = string_version[string_version.find('Procurement reference'):string_version.
        find('Published date', string_version.find('Procurement reference'))]
    if 'tender' in refno.lower():
        page_dict['reference_no'] = refno.split('tender_')[1]
    else:
        page_dict['reference_no'] = refno.split('reference')[1]
    page_dict['title'] = list([element.get_text() for element in result_header[0: len(result_header)]])[0]
    page_dict['description'] = string_version[string_version.find('Description') +
                                              len('Description'):string_version.rfind('More')]
    page_dict['contract_SIC'] = string_version[string_version.find('Industry') +
                                               len('Industry'):string_version.rfind('Location')]
    page_dict['contract_location'] = string_version[string_version.find('Location of contract') +
                                                    len('Location of contract'):string_version.
        find('Value', string_version.find('Location of contract'))]
    page_dict['published_date'] = string_version[string_version.
                                                     find('Published date') +
                                                 len('Published date'):string_version.
        find('Closing date', string_version.find('Published date'))]
    page_dict['closing_date'] = string_version[string_version.find('Closing date') +
                                               len('Closing date'):
                                               string_version.rfind('Closing time')]
    page_dict['awarded_date'] = string_version[string_version.
                                                   find('Awarded date') +
                                               len('Awarded date'):
                                               string_version.rfind('Contract start date')]
    page_dict['contract_start_date'] = string_version[string_version.
                                                          find('Contract start date\n') +
                                                      len('Contract start date\n'):string_version.
        find('Contract end date', string_version.find('Contract start date'))]
    page_dict['contract_end_date'] = string_version[string_version.
                                                        find('Contract end date') +
                                                    len('Contract end date'):
                                                    string_version.rfind('Contract type')]
    page_dict['contract_type'] = string_version[string_version.find('Contract type') +
                                                len('Contract type'):
                                                string_version.rfind('Procedure type')]
    page_dict['suitable_for_SMEs'] = string_version[string_version.find('SMEs?') + len('SMEs?'):
                                                    string_version.rfind('Contract is suitable for VCSEs')]
    page_dict['suitable_for_VCSEs'] = string_version[string_version.find('VCSEs?') + len('VCSEs?'):
                                                     string_version.rfind('Description')]
    page_dict['advertised_value'] = string_version[
                                    string_version.find('Value of contract') +
                                    len('Value of contract'):
                                    string_version.rfind('Procurement reference')]
    page_dict['awarded_value'] = string_version[
                                 string_version.find('Total value of contract') +
                                 len('Total value of contract'):
                                 string_version.rfind('This contract')]
    page_dict['suppliers_n'] = int(string_version[string_version.find('was awarded to ') +
                                              len('was awarded to '):string_version.
        find('\n', string_version.find('was awarded to'))].split(' ')[0])
    page_dict['commissioner_name'] = string_version[string_version.find('Contact name') +
                                                    len('Contact name'):
                                                    string_version.rfind('Address')]
    page_dict['commissioner_address'] = string_version[string_version.find('Contact name') +
                                                       len('Contact name'):string_version.rfind('Email')]
    if 'supplier.' in string_version:
        suppliers_string = string_version[string_version.find('supplier.\n') + len('supplier.\n'):
                                          string_version.find('\nAbout the buyer')]
    else:
        suppliers_string = string_version[string_version.find('suppliers.\n') + len('suppliers.\n'):
                                          string_version.find('\nAbout the buyer')]
    suppliers_string = suppliers_string.split('\n')
    supplier_name = []
    supplier_address = []
    supplier_reference = []
    supplier_sme = []
    supplier_vcse = []
    for line in range(len(suppliers_string)):
        if suppliers_string[line] == "Show supplier information":
            supplier_name.append(suppliers_string[line-1])
            if suppliers_string[line+1].lower().startswith('address'):
                add_line = suppliers_string[line+1]
                supplier_address.append(add_line[7:add_line.find(' Reference')])
                supplier_reference.append(add_line[add_line.find(' Reference') + len(' Reference'):
                                                   add_line.find('Supplier')])
                if 'Supplier is SME?Yes' in add_line:
                    supplier_sme.append('Yes')
                else:
                    supplier_sme.append('No')
                if 'Supplier is VCSE?Yes' in add_line:
                    supplier_vcse.append('Yes')
                else:
                    supplier_vcse.append('No')
    page_dict['supplier_name'] = supplier_name
    page_dict['supplier_address'] = supplier_address
    page_dict['supplier_reference'] = supplier_reference
    page_dict['supplier_is_VCSE'] = supplier_vcse
    page_dict['supplier_is_SME'] = supplier_sme
    if 'Website' in string_version:
        page_dict['commissioner_website'] = string_version[string_version.find('Website') +
                                                           len('Website'):string_version.rfind('/')]
    else:
        page_dict['commissioner_website'] = np.nan
    if 'Procedure type' in string_version:
        page_dict['procedure_type'] = string_version[string_version.
                                                         find('Procedure type') +
                                                     len('Procedure type'):string_version.rfind('What')]
    else:
        page_dict['procedure_type'] = np.nan
    return page_dict


def save_data(data_keys, data_values, file_path, url, page_number, page):
    """
    Saves data out to a csv.
    Parameters:
        data_keys (list): A list of keys from our page_dict
        data_values (list): a list of procurement data
        file_path (str): where to save the data
        url (str): the url of the page being scraped
        page_number (int): which page are we on?
        page (int): which page on page_number are we on?
     Returns:
        None
    """
    data_keys = list(data_keys)
    data_keys.extend(['url', 'page_number', 'number'])
    data_values.extend([url, page_number, page])
    if os.path.exists(file_path) is False:
        with open(file_path, 'w', newline='\n', encoding="utf-8") as csvfile:
            data_writer = csv.writer(csvfile, delimiter=',')
            data_writer.writerow(data_keys)
            data_writer.writerow(data_values)
    else:
       with open(file_path, 'a', newline='\n', encoding="utf-8") as csvfile:
           data_writer = csv.writer(csvfile, delimiter=',')
           data_writer.writerow(data_values)


def clean_page(data_dict):
    """ Clean the data dictionary where required"""
    data_values = [str(x).replace('\n', '') for x in data_dict.values()]
    data_keys = data_dict.keys()
    return data_keys, data_values


def main():
    global number_pages, max_pages
    driver = setup_driver()
    data_path = os.path.join(os.getcwd(), '..', 'data')
    today = date.today()
    if os.path.exists(data_path) is False: os.mkdir(data_path)
    contracts_path = os.path.join(data_path, 'contracts_finder')
    if os.path.exists(contracts_path) is False: os.mkdir(contracts_path)
    log_path = os.path.join(os.getcwd(), '..', 'logging')
    if os.path.exists(log_path) is False: os.mkdir(log_path)
    file_path = os.path.join(contracts_path, 'contracts_data_' + str(today) + '.csv')
    logger = setup_logging(log_path, today)
    define_search(driver)
    counter = 1
    scrape_passed = False
    html = driver.execute_script("return document.body.innerHTML;")
    try:
        number_pages = re.findall('"Results page(.+?)"', html)
        max_pages = np.max(list(map(int, number_pages)))
    except Exception as e:
        logging.debug('Unable to get the page_number from the initiated html')
    for page_number in tqdm(range(0, max_pages)):
        for page in range(0, 20):
            attempt = 0
            while (scrape_passed is False) and (attempt < 5):
                try:
                    content = driver.find_elements(By.CLASS_NAME, "search-result-header")
                    WebDriverWait(driver, 20).until(EC.element_to_be_clickable(content[page])).click()
                    html = driver.execute_script("return document.body.innerHTML;")
                    page_data = get_page_data_from_html(html)
                    data_keys, data_values = clean_page(page_data)
                    url = driver.current_url
                    save_data(data_keys, data_values, file_path, url, page_number, page)
                    logger.info('Just scraped: page number: ' + str(counter))
                    driver.back()
                    scrape_passed = True
                except Exception as e:
                    print(traceback.format_exc())
                    logger.debug('Problem scraping ' + str(counter) + '. Exception: ' + str(e))
                    logger.info('Taking a bit of a rest for a short while...')
                    time.sleep(360)
                    scrape_passed = False
                    attempt += 1
            scrape_passed = False
            counter += 1
            time.sleep(1)
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable(
            (By.XPATH, ".//*[contains(@class, 'standard-paginate-next govuk-link break-word')]"))).click()


if __name__ == "__main__":
    main()