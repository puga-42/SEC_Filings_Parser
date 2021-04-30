from bs4 import BeautifulSoup
import pandas as pd
import re
import requests


def str_rep(string, old_list, new_list):
    for i in range(len(old_list)):
        string = string.replace(old_list[i], new_list[i])
    return string

def remove_extra_spaces(string):
    return " ".join(string.split())

def bsoup_extract_from_string(string):
    return ' '.join(BeautifulSoup(string, "html.parser").findAll(text=True))

def decode_text(string):
    '''
    Inputs: str
    Outputs: str

    Takes in a string with unicode characters and outputs string with unicode characters removed. 

    This should be a temporary function for readability - there are probably more elegant and complete solutions out there.
    '''

    string = str_rep(string, ['\n', '\xa0', '\x95', 
                '\x92', '\x94', '\x97', '\x93'], [' ', ' ', ' ', 
                                          '', ' ', ' ', ' '])
    return string


def tenK_to_dict():
    tenK_dict = {}
    # create an empty dict for each section to house text
    for section in tenK_sections:
        tenK_dict[section] = {}

    
def parse_filing(filing_location, cik, master_dict):    

    '''
    Inputs: str, str
    returns: dict
    
    Takes in html location of a filing, takes each document present and adds to unique dictionary.
    Returns the dictionary indicated by desired_document
    '''

    
    #get response
    response = requests.get(filing_location)
    # parse response
    soup = BeautifulSoup(response.content, 'lxml')


    ## check to see how deep the master_dict goes
    if cik not in master_dict.keys():
        print('new company')
        #initialize dict to hold all unique documents present in filing
        master_dict[cik] = {'10-K': {}, '10-Q': {}}


    ## store header as a place holder for the date. We will parse that out later 
    sec_header_tag = soup.find('sec-header')
    
    # find all the documents in the filing.
    for filing_document in soup.find_all('document'):        
        #document id will be 10-K or 10-Q (or others but we don't care about those rn)
        document_id = filing_document.type.find(text=True, recursive=False).strip()
        print('from parse_filing. document_id: ', document_id)
        document_filename = filing_document.filename.find(text=True, recursive=False).strip()

        ## we only want docuent id of 10-K or 10-Q
        if (document_id == '10-K') or (document_id == '10-Q'):
            ## we'll use header tag as a placeholder for date - will parse out later
            master_dict[cik][document_id][document_filename] = {'header': sec_header_tag, 'document_code': filing_document.extract(), 'table_of_contents': {}}
            
            return master_dict, document_id, document_filename



def split_by_section(document, document_type):
    '''
    inputs: dict, str
    outputs: dict

    Takes in document, a dictionary, and document_type, a string indicating what document it is. 
    Calls correct splitting function and returns split dict.

    '''

    if document_type == '10-K':
        return_dict = split_tenk_by_section(document)
    
    elif document_type == '10-Q':
        return_dict = split_tenq_by_section(document)

    elif document_type == '8-K':
        return_dict = split_eightk_by_section(document)

    return return_dict


def split_tenk_by_section(tenk_code_dict):
    
    #initialize master 10-k dict
    tenk_document_dict = {}

    parts_to_split = get_table_of_contents(tenk_code_dict['document_code'])

    tenk_text = tenk_code_dict['document_code'].find('text').extract()


    # manually entered parts to split - will come back and figure out how to scrape instead
    # parts_to_split = ['BUSINESS ',
    #                 'RISK FACTORS ',
    #                 'UNRESOLVED STAFF COMMENTS ',
    #                 'PROPERTIES ',
    #                 'LEGAL PROCEEDINGS ',
    #                 'RESERVED ',
    #                 'MARKET FOR REGISTRANTS COMMON EQUITY, RELATED STOCKHOLDER MATTERS AND ISSUER PURCHASES OF EQUITY SECURITIES ',
    #                 'SELECTED FINANCIAL DATA ',
    #                 'MANAGEMENTS DISCUSSION AND ANALYSIS',
    #                 'QUANTITATIVE AND QUALITATIVE DISCLOSURES ABOUT MARKET RISK ',
    #                 'FINANCIAL STATEMENTS AND SUPPLEMENTARY DATA ',
    #                 'CHANGES IN AND DISAGREEMENTS WITH ACCOUNTANTS ON ACCOUNTING AND FINANCIAL DISCLOSURE ',
    #                 'CONTROLS AND PROCEDURES ', 
    #                 'OTHER INFORMATION ', 
    #                 'DIRECTORS, EXECUTIVE OFFICERS AND CORPORATE GOVERNANCE', 
    #                 'EXECUTIVE COMPENSATION', 
    #                 'SECURITY OWNERSHIP OF CERTAIN BENEFICIAL OWNERS', 
    #                 'CERTAIN RELATIONSHIPS AND RELATED TRANSACTIONS', 
    #                 'PRINCIPAL ACCOUNTANT FEES AND SERVICES',
    #                 'EXHIBITS AND FINANCIAL STATEMENT SCHEDULES'
    #                 ]

        

    #get different segments of document
    text_split_into_parts = []

    # for parts I-IV
    for part in parts_to_split:
        next_part = tenk_text.find(lambda tag:tag.name=='b' and part.upper() in tag.text)
        text_split_into_parts.append(next_part)


    #convert all parts to string
    all_parts = [str(part) for part in text_split_into_parts]
    #prep the document text for splitting - convert to string
    tenk_string = str(tenk_text)
    #defing the regex delimeter pattern
    regex_delimiter_pattern = '|'.join(map(re.escape, all_parts))

    #split doc on each break
    split_tenk_string = re.split(regex_delimiter_pattern, tenk_string)

    #store parts in master dict
    i = 1
    for section in parts_to_split:
        tenk_document_dict[section] = split_tenk_string[i]
        i += 1


    return tenk_document_dict


def split_tenq_by_section(tenq_code_dict):
    print('We currently have no structure in place to parse 10-Q. Please try again later!')

def split_eightk_by_section(eightk_code_dict):
    print('We currently have no structure in place to parse an 8-K. Please try again later!')
    return {}

def get_filing_doc_text(filing_doc_code_dict):
    tenk_text_dict = {}
    
    for key in filing_doc_code_dict.keys():
        raw_text = bsoup_extract_from_string(filing_doc_code_dict[key])
        decoded_text = decode_text(raw_text)
        decoded_text = remove_extra_spaces(decoded_text)
        tenk_text_dict[key] = decoded_text
        
    return tenk_text_dict


## this is not used
def get_text_dict(filing_location, filing_doc):
    doc_dict = parse_filing(filing_location, filing_doc)
    code_dict = split_by_section(doc_dict, filing_doc)
    text_dict = get_filing_doc_text(code_dict)

    return text_dict



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
    href_list = []
    text_list = []
    
    #get all tables in html
    all_tables = filingcode.find_all('table')
    
    #table of contents should have elements as hrefs
    for table in all_tables:
        if len(table.find_all('a', href=True)) > 0:
            href_list.append(table.find_all('a', href=True))
    
    for href in href_list[0]:
        text_list.append(href.text.lower())
    
    pruned_list = prune_toc(text_list)

    return pruned_list

# def get_tenq_text_dict(filing_location):
#     tenq_dict = parse_filing(filing_location, '10-Q')
#     code_dict = split_by_section(tenq_dict)  
#     text_dict = 



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
    
    return False
    