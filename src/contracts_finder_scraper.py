import numpy as np
import time
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

def setup_driver():
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    options = webdriver.ChromeOptions()
    options.add_argument("headless")
    driver.get("https://www.contractsfinder.service.gov.uk/Search")
    return driver

def define_search(driver):
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
    page_dict['commissioner'] = [element.get_text() for element in commissioner]
    page_dict['reference_no'] = string_version[string_version.
                                                   find('Procurement reference'):string_version.
        find('Published date', string_version.find('Procurement reference'))]
    page_dict['title'] = list([element.get_text() for element in result_header[0: len(result_header)]])
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
                                               len('Closing date'):string_version.rfind('Closing time')]
    page_dict['awarded_date'] = string_version[string_version.
                                                   find('Awarded date') +
                                               len('Awarded date'):string_version.rfind('Contract start date')]
    page_dict['contract_start_date'] = string_version[string_version.
                                                          find('Contract start date\n') +
                                                      len('Contract start date\n'):string_version.
        find('Contract end date', string_version.find('Contract start date'))]
    page_dict['contract_end_date'] = string_version[string_version.
                                                        find('Contract end date') +
                                                    len('Contract end date'):string_version.rfind('Contract type')]
    page_dict['contract_type'] = string_version[string_version.find('Contract type') +
                                                len('Contract type'):string_version.rfind('Procedure type')]
    page_dict['suitable_for_SMEs'] = string_version[string_version.find('SMEs?') +
                                                    len('SMEs?'):string_version.
        rfind('Contract is suitable for VCSEs')],
    page_dict['suitable_for_VCSEs'] = string_version[
                                      string_version.find('VCSEs?') +
                                      len('VCSEs?'):string_version.rfind('Description')]
    page_dict['Advertised_value'] = string_version[
                                    string_version.find('Value of contract') +
                                    len('Value of contract'):string_version.rfind('Procurement reference')]
    page_dict['Awarded_value'] = string_version[
                                 string_version.find('Total value of contract') +
                                 len('Total value of contract'):string_version.rfind('This contract')]
    page_dict['suppliers_n'] = string_version[string_version.find('was awarded to') +
                                              len('was awarded to'):string_version.
        find('\n', string_version.find('was awarded to'))]
    page_dict['supplier_address'] = string_version[string_version.find('Address') +
                                                   len('Address'):string_version.
        find('Reference', string_version.find('Address'))]
    page_dict['supplier_is_SME'] = string_version[string_version.find('is SME?') +
                                                  len('is SME?'):string_version.
        find('Supplier', string_version.find('is SME?'))]
    page_dict['supplier_is_VCSE'] = string_version[string_version.find('is VCSE?') +
                                                   len('is VCSE?'):string_version.
        find('About the buyer', string_version.find('is VCSE?'))]
    page_dict['supplier_reference'] = string_version[string_version.find('Reference') +
                                                     len('Reference'):string_version.
        find('Supplier is SME?', string_version.find('Reference'))]
    page_dict['commissioner_name'] = string_version[string_version.find('Contact name') +
                                                    len('Contact name'):string_version.rfind('Address')]
    page_dict['commissioner_address'] = string_version[string_version.find('Contact name') +
                                                       len('Contact name'):string_version.rfind('Email')]
    if 'supplier.' in string_version:
        page_dict['supplier_name'] = string_version[
                                     string_version.find('supplier.') +
                                     len('supplier.'):string_version.find('Show supplier')]
    else:
        page_dict['supplier_name'] = string_version[
                                     string_version.find('suppliers.') +
                                     len('suppliers.'):string_version.find('Show supplier')]

    if 'suppliers.' in string_version:
        page_dict['shared_supplier_information'] = string_version[string_version.find('is VCSE?') +
                                                                   len('is VCSE?'):string_version.
            find('About the buyer', string_version.find('is VCSE?'))]
    else:
        page_dict['shared_supplier_information'] = np.nan
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

def main():
    driver = setup_driver()
    define_search(driver)
    for y in range(301):
        for x in range(1, 20):
            print(x)
            content = driver.find_elements(By.CLASS_NAME, "search-result-header")
            WebDriverWait(driver, 20).until(EC.element_to_be_clickable(content[x])).click()
            html = driver.execute_script("return document.body.innerHTML;")
            page_data = get_page_data_from_html(html)
            print(page_data)
            driver.back()
            time.sleep(3)
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable(
            (By.XPATH, ".//*[contains(@class, 'standard-paginate-next govuk-link break-word')]"))).click()


if __name__ == "__main__":
    main()