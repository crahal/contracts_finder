"""
    File name: get_all_ch_data.py
    Author: Charlie Rahal
    Date created: 22/02/2023
    Date last modified: 22/02/2023
    Python Version: >3
"""

import requests
import logging
import os
import urllib.request, shutil
from bs4 import BeautifulSoup
from ftplib import FTP


def get_free_data_product(url, path):
    """
     Gets the bulk download of the free data product.
     This is data on companies and their characteristics,
     as opposed to officers, psc, or otherwise (eg accounts)

             Parameters:
                     url (str): A url to find the data at
                     path (str): A place to save the data

             Returns:
                     None
     """

    r = requests.get(url)
    if r.ok:
        soup = BeautifulSoup(r.text, features="html.parser")
        for a in soup.find_all('a', href=True):
            if 'BasicCompanyDataAsOneFile' in a['href']:
                filename = a['href']
                url = 'http://download.companieshouse.gov.uk/' + filename
                if os.path.exists(os.path.join(path, filename)):
                    module_logger.info(filename + ' exists')
                else:
                    module_logger.info(filename + ' doesnt exist')
                    with urllib.request.urlopen(url) as response,\
                    open(os.path.join(path, filename), 'wb') as out_file:
                        shutil.copyfileobj(response, out_file)


def get_psc_data(url, path):
    """
     Gets data on Persons of Significant Control.
     This is data on psc as opposed to officers or
     companies themselves.

             Parameters:
                     url (str): A url to find the data at
                     path (str): A place to save the data
             Returns:
                     None
     """
    r = requests.get(url)
    if r.ok:
        soup = BeautifulSoup(r.text, features="html.parser")
        for a in soup.find_all('a', href=True):
            if 'persons-with-significant-control-snapshot' in a['href']:
                filename = a['href']
                url = 'http://download.companieshouse.gov.uk/' + filename
                if os.path.exists(os.path.join(path, filename)):
                    module_logger.info(filename + ' exists')
                else:
                    module_logger.info(filename + ' doesnt exist')
                    with urllib.request.urlopen(url) as response,\
                    open(os.path.join(path, filename), 'wb') as out_file:
                        shutil.copyfileobj(response, out_file)

def get_accounts_data(url, path):
    """
     Gets data on company accounts.

             Parameters:
                     url (str): A url to find the data at
                     path (str): A place to save the data
             Returns:
                     None
     """
    r = requests.get(url)
    if r.ok:
        soup = BeautifulSoup(r.text, features="html.parser")
        for a in soup.find_all('a', href=True):
            if '.zip' in a['href']:
                filename = a['href']
                url = 'http://download.companieshouse.gov.uk/' + filename
                if os.path.exists(os.path.join(path, filename)):
                    module_logger.info(filename + ' exists')
                else:
                    module_logger.info(filename + ' doesnt exist')
                    with urllib.request.urlopen(url) as response,\
                    open(os.path.join(path, filename), 'wb') as out_file:
                        shutil.copyfileobj(response, out_file)


def get_officer_data(ftpaddress, uname, passwd, path):
    """
     Gets data on Officers from the CH ftp.
     You need a username and password to access this.

             Parameters:
                     ftpaddress (str): location of the ftp server
                     uname (str): your ch username
                     passwd (str): your ch password
                     path (str): A place to save the data
             Returns:
                     None
     """
    ftp = FTP(ftpaddress)
    try:
        ftp.login(uname, passwd)
        module_logger.info('logged in')
        ftp.cwd("/")
        filenames = ftp.nlst()
        for filename in filenames:
            if os.path.exists(os.path.join(path, filename)):
                module_logger.info(filename + ' exists')
            else:
                module_logger.info(filename + ' doesnt exist, getting it')
                local_filename = os.path.join(path, filename)
                file = open(local_filename, 'wb')
                ftp.retrbinary('RETR '+ filename, file.write)
                file.close()
        ftp.quit()
    except:
        module_logger.debug('General exception noted.', exc_info=True)


def load_token(path):
    """
     Loads your CH token from ../tokens/ftp_token

             Parameters:
                     path (str): A place to save the data
             Returns:
                     None
     """
    try:
        with open(path, 'r') as file:
            return str(file.readline()).strip()
    except EnvironmentError:
        module_logger.debug('Error loading access token from file')


def setup_logging(logpath):
    """" Sets up logging for the script"""
    logger = logging.getLogger('get_ch_data')
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler((os.path.abspath(
        os.path.join(logpath, 'get_ch_data.log'))))
    fh.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.ERROR)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger

if __name__ == "__main__":
    module_logger = setup_logging(os.path.join(__file__,
                                               '../..',
                                               'logging'))
    ftp_token = load_token(os.path.abspath(os.path.join(__file__, '../..',\
                                                        'tokens', 'ftp_token')))
    data_url = 'http://download.companieshouse.gov.uk/'
    free_data_url = data_url + 'en_output.html'
    psc_data_url = data_url + 'en_pscdata.html'
    accounts_data_url = data_url + 'en_monthlyaccountsdata.html'
    data_dir = os.path.abspath(os.path.join(__file__, '../..', 'data'))
    try:
        get_free_data_product(free_data_url, os.path.join(data_dir, 'basic_data'))
        module_logger.info('Got the free data product!')
    except Exception as e:
        module_logger.debug('Problem getting the free data product! ', str(e))
    try:
        get_psc_data(psc_data_url, os.path.join(data_dir, 'psc_data'))
        module_logger.info('Got the psc data!')
    except Exception as e:
        module_logger.debug('Problem getting the psc data! ', str(e))
    try:
        get_accounts_data(accounts_data_url,\
                          os.path.join(data_dir, 'accounts_data'))
        module_logger.info('Got the accounts data!')
    except Exception as e:
        module_logger.debug('Problem getting the accounts data!', str(e))
    try:
        get_officer_data('ftp.bulk.companieshouse.gov.uk',\
                         'oxford', ftp_token,\
                         os.path.join(data_dir,'officer_data'))
        module_logger.info('Got the officer FTP data!')
    except Exception as e:
        module_logger.debug('Problem getting the officer data! ', str(e))