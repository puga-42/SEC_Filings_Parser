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
    string = str_rep(string, ['\n', '\xa0', '\x95', 
                '\x92', '\x94', '\x97', '\x93'], [' ', ' ', ' ', 
                                          '', ' ', ' ', ' '])
    return string


def tenK_to_dict():
    tenK_dict = {}
    # create an empty dict for each section to house text
    for section in tenK_sections:
        tenK_dict[section] = {}

    
def parse_filing(filing_location, desired_document):    

    '''
    Inputs: str, str
    returns: dict
    
    Takes in html location of a filing, takes each document present and adds to unique dictionary.
    Returns the dictionary indicated by desired_document
    '''

    htmlText = filing_location
    #get response
    response = requests.get(htmlText)
    # parse response
    soup = BeautifulSoup(response.content, 'lxml')
    
    #initialize dict to hold all unique documents present in filing
    master_document_dict = {}

    # find all the documents in the filing.
    for filing_document in soup.find_all('document'):
        # define the document type, found under the <type> tag, this will serve as our key for the dictionary.
        document_id = filing_document.type.find(text=True, recursive=False).strip()
        document_sequence = filing_document.sequence.find(text=True, recursive=False).strip()
        document_filename = filing_document.filename.find(text=True, recursive=False).strip()
        document_description = filing_document.description.find(text=True, recursive=False).strip()

        # initalize our document dictionary
        master_document_dict[document_id] = {}

        # add the different parts, we parsed up above.
        master_document_dict[document_id]['document_sequence'] = document_sequence
        master_document_dict[document_id]['document_filename'] = document_filename
        master_document_dict[document_id]['document_description'] = document_description

        # store the document itself, this portion extracts the HTML code. We will have to reparse it later.
        master_document_dict[document_id]['document_code'] = filing_document.extract()
    
    return master_document_dict[desired_document]



def split_by_section(tenk_code_dict):
    
    #initialize master 10-k dict
    tenk_document_dict = {}

    tenk_text = tenk_code_dict['document_code'].find('text').extract()


    # manually entered parts to split - will come back and figure out how to scrape instead
    parts_to_split = ['BUSINESS ',
                    'RISK FACTORS ',
                    'UNRESOLVED STAFF COMMENTS ',
                    'PROPERTIES ',
                    'LEGAL PROCEEDINGS ',
                    'RESERVED ',
                    'MARKET FOR REGISTRANTS COMMON EQUITY, RELATED STOCKHOLDER MATTERS AND ISSUER PURCHASES OF EQUITY SECURITIES ',
                    'SELECTED FINANCIAL DATA ',
                    'MANAGEMENTS DISCUSSION AND ANALYSIS',
                    'QUANTITATIVE AND QUALITATIVE DISCLOSURES ABOUT MARKET RISK ',
                    'FINANCIAL STATEMENTS AND SUPPLEMENTARY DATA ',
                    'CHANGES IN AND DISAGREEMENTS WITH ACCOUNTANTS ON ACCOUNTING AND FINANCIAL DISCLOSURE ',
                    'CONTROLS AND PROCEDURES ', 
                    'OTHER INFORMATION ', 
                    'DIRECTORS, EXECUTIVE OFFICERS AND CORPORATE GOVERNANCE', 
                    'EXECUTIVE COMPENSATION', 
                    'SECURITY OWNERSHIP OF CERTAIN BENEFICIAL OWNERS', 
                    'CERTAIN RELATIONSHIPS AND RELATED TRANSACTIONS', 
                    'PRINCIPAL ACCOUNTANT FEES AND SERVICES',
                    'EXHIBITS AND FINANCIAL STATEMENT SCHEDULES'
                    ]

    #get different segments of document
    text_split_into_parts = []

    # for parts I-IV
    for part in parts_to_split:
        next_part = tenk_text.find(lambda tag:tag.name=='b' and part in tag.text)
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


def get_tenk_text(tenk_code_dict):
    tenk_text_dict = {}
    
    for key in tenk_code_dict.keys():
        raw_text = bsoup_extract_from_string(tenk_code_dict[key])
        decoded_text = decode_text(raw_text)
        decoded_text = remove_extra_spaces(decoded_text)
        tenk_text_dict[key] = decoded_text
        
    return tenk_text_dict


def get_tenk_text_dict(filing_location):
    tenk_dict = parse_filing(filing_location, '10-K')
    code_dict = split_by_section(tenk_dict)
    text_dict = get_tenk_text(code_dict)

    return text_dict