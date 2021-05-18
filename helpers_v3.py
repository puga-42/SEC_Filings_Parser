

from bs4 import BeautifulSoup
import pandas as pd
import re
import requests
from time import sleep
from tabulate import tabulate
import unicodedata


def get_data_from_edgar(list_of_companies, list_of_years, filing_types, master_df):
    
    ## first we need to go to edgar database company by company
    for company in list_of_companies:
        link_date_dict = get_filing_doc_location(company, list_of_years, filing_types)

        # now we have a list of links to the .txt files
        #next up we should extract the document code for 10-K or 10-Q
        master_df = extract_relevant_document_code_from_filing_doc(link_date_dict, company, master_df)
        #now we need to go into document code and split by section
        
        
    return master_df

def get_filing_doc_location(cik, years, doc_list):
    '''
    inputs:
    cik (list)
    years (tuple or two element list)
    doc_list (tuple or list of 10-K and/or 10-Q)
    
    returns:
    list of addresses (strings) where txt documents are held
    '''
    
    for doc in doc_list:
        path = 'https://www.sec.gov/cgi-bin/srch-edgar?text=' + cik + '+' + doc + '&first=' + years[0] + '&last=' + years[1]        
        print(path)
        #get response
        response = requests.get(path)

        soup = soup_xtml_or_htmlparser(response)
        
        txt_links = []
        dates = []
        for tr in soup.find_all('tr'):
            if '[text]' in tr.text:
                for date in tr.find_all('td', text=re.compile(r'(\d+/\d+/\d+)')):
                    dates.append(date.text)
                for a in tr.find_all('a', href=True, text='[text]'):
                    link = 'https://www.sec.gov/'+a['href']
                    txt_links.append(link)


    link_dict = dict(zip(txt_links, dates))
    return link_dict

def soup_xtml_or_htmlparser(response):
    try:
        soup = BeautifulSoup(response.content, 'html.parser')
    except Exception:
        soup = BeautifulSoup(response.content, 'lxml')
        print('lxml used')

    return soup


def extract_relevant_document_code_from_filing_doc(link_date_dict, cik, master_df):
    '''
    for each link provided, will go to destination and add the document code of any
    10-K and 10-Qs present to the master_dict
    
    returns:
    '''

    for link, date in link_date_dict.items():
        master_df = add_filing_info_to_master_df(link, date, cik, master_df)
    return master_df


def add_filing_info_to_master_df(filing_location, date, cik, master_df):   

    '''
    Inputs: str, str
    returns: dict with 
    company -> 
    filing_type -> 
    date -> 
    document_code (bs4.element.Tag), header (bs4.element.Tag), toc (list of strings)
    
    Takes in html location of a filing, takes each document present and adds to unique dictionary.
    Returns the dictionary indicated by desired_document
    '''

    # parse response

    soup_counter = 0
    problems = False
    while True:
        if soup_counter > 1:
            problems = True
            print("we're having problems. Here is what we're dealing with:")
            print('filing_location:', filing_location, '\ndate:', date, '\ncik', cik)
        #get response
        response = requests.get(filing_location)

        soup = soup_xtml_or_htmlparser(response)
        num_documents = soup.find_all('document')
        soup_counter += 1
        if len(num_documents) > 0:
            if problems == True:
                print('looks like the problem got fixed')
            break
   
    # find all the documents in the filing.
    for filing_document in soup.find_all('document'):
        if (filing_document.type.find(text=True, recursive=False).strip() != '10-K') and (filing_document.type.find(text=True, recursive=False).strip() != '10-Q'):
            continue
        #document id will be 10-K or 10-Q (or others but we don't care about those rn)
        document_id = filing_document.type.find(text=True, recursive=False).strip()
        document_filename = filing_document.filename.find(text=True, recursive=False).strip()

        ## we only want docuent id of 10-K or 10-Q
        if (document_id == '10-K') or (document_id == '10-Q'):
            ## we'll use header tag as a placeholder for date - will parse out later
            master_df.loc[len(master_df.index)] = [document_filename, cik, document_id, date, filing_document.extract()]
            return master_df




def get_table_of_contents(filingcode):
    
    '''
    outputs list of text elements from first with hrefs in an html doc. Might work, but will need to test
    
    to use:
    1. call parse_filing with appropriate .txt location and document type. filing = parse_filing()
    2. use filing['document code'] as parameter
    
    Inputs:
    filingcode - bs4 tag in html format
    
    Returns:
    text_list - list of text elements of table of contents hopefully
    
    '''
    text_list = []
    
    #get all tables in html
    all_tables = filingcode.find_all('table')
    
    #table of contents should have elements as hrefs
    for table in all_tables:
        ## look for correct table
        if len(table.find_all('a', text=re.compile(r'Financial Statements'))) > 0:
            
        
            # look for Item column
            for tr in table.find_all('tr'):
                if 'item' in tr.text.lower():
                    for td in tr.find_all('td'):
                        normalized_list = unicodedata.normalize('NFKD', td.text.lower())
                        text_list.append(normalized_list)
                    
            break
        else:
            continue
        break
        

    pruned_list = prune_toc(text_list)
    return pruned_list


def prune_toc(table_of_contents):
    '''
    Removes unnecessary elements from toc list
    
    inputs:
    table_of_contents - list
    
    returns:
    table_of_contents - list
    '''
    
    new_toc = []
    
    for word in table_of_contents:
        if check_regex(word) == False:
            word = word.replace('\n', '')
            new_toc.append(word)

    return new_toc

def check_regex(word):
    
    '''
    check for two regex patterns in table of contents indices
    
    inputs:
    word - string
    
    returns - True or False depending on whether a pattern is found
    '''
    
    check_1 = re.findall(r"^\D{4}\s[\d+ | i]", word)
    check_2 = re.findall(r"^\d{1,3}", word)
    if len(check_1) or len(check_2) > 0:
        return True
    if len(word) < 10:
        return True
    return False



