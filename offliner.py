#!python
# -*- coding: utf-8 -*-

import sys
from pathlib import Path
import os
import shutil
from inspect import currentframe, getframeinfo # for clear diagnostics
import urllib.request

import web.http

__all__ = ['process_data']

#########
def _USAGE():
    """Function to print script usage"""
    
    print("""\
    Usage: """,
    sys.argv[0],
    """ [OPTIONS]
        -h          Display this usage message
        url         Web page to be retrieved in the URL format:
                    scheme:[//[user:password@]host[:port]][/]path[?query][#fragment]
    """)

#########
def _get_charset(charset):
    """Function for converting charset from HTML form to Python's one"""

    if charset == "windows-1251":
        return "cp1251"
    elif charset == None: # default charset
        return "utf-8"
    else:
        return charset
         
#########
def _retrieve_data(url, is_text):
    """Function for retrieving data using URL"""

    # TODO: Deprecated since version 2.6: The urlopen() function has been
    #       removed in Python 3 in favor of urllib2.urlopen().
    try:
        response = urllib.request.urlopen(url)

        # print('RESPONSE:', response)
        print('URL     :', response.geturl())

        headers = response.info()
        # print('DATE    :', headers['date'])
        # print('HEADERS :')
        # print('---------')
        # print(headers)
        # print('---------')
        # print('CHARSET :', response.headers.get_content_charset())
        # print('---------')

        if is_text:
            data = response.read().decode(_get_charset(response.headers.get_content_charset()))
        else:
            data = bytearray(response.read())
        
        # print('LENGTH  :', len(data))
        # print('DATA    :')
        # print('---------')
        # print(data)
        print('=========')
    except urllib.error.HTTPError as e:
        sys.stderr.write("WARNING ({},{}): Unable to process the url '{}':\n\t{}: {}\n".
            format(getframeinfo(currentframe()).filename,
                   getframeinfo(currentframe()).lineno,
                   url, str(sys.exc_info()[0]), e))
    except Exception as e:
        sys.stderr.write("ERROR ({},{}): Unable to process the url '{}':\n\t{}: {}\n".
            format(getframeinfo(currentframe()).filename,
                   getframeinfo(currentframe()).lineno,
                   url, str(sys.exc_info()[0]), e))
    else:
        return (headers, data)
    
    return -1, -1
    
#########
def process_data(url):
    """Function for process retrieved HTML data"""

    (headers, data) = _retrieve_data(url, 1)
    
    raw_filename = "_input.html";
    txt_filename = "_output.txt";
   
    ### Output directory
    try:
        cwdir = Path.cwd()
        address = '_' + str(url.split('/')[2])
        print("Address=", address)
        
        if Path(address).exists():
            print("Not empty: ", cwdir, address)
            shutil.rmtree(address)       
        Path(address).mkdir(777, True)
    except Exception as e:
        sys.stderr.write("ERROR ({},{}): Unable to create the directory '_{}':\n\t{}: {}\n".
            format(getframeinfo(currentframe()).filename,
                   getframeinfo(currentframe()).lineno,
                   address, str(sys.exc_info()[0]), e))
        return 1
    
    ### Debug: save raw input file
    try:
        raw_ffilename = os.path.join(address, raw_filename)
        print("<= raw_ffilename=", raw_ffilename)
        f = open(raw_ffilename, 'w')
        f.write(str(data.encode("utf-8")))
        f.close()
    except Exception as e:
        sys.stderr.write("ERROR ({},{}): Unable to write to the file '{}':\n\t{}: {}\n".
            format(getframeinfo(currentframe()).filename,
                   getframeinfo(currentframe()).lineno,
                   raw_ffilename, str(sys.exc_info()[0]), e))
        return 1

    ### Get & parse HTML document
    try:
        parser = web.http.OfflinerHTMLParser(headers['date'])
        parser.feed(data)        
        (content, img_urls) = parser.get_content()
    except Exception as e:
        sys.stderr.write("ERROR ({},{}): Unable to process HTML by the url '{}':\n\t{}: {}\n".
            format(getframeinfo(currentframe()).filename,
                   getframeinfo(currentframe()).lineno,
                   url, str(sys.exc_info()[0]), e))
        return 1

    ### Get images
    try:        
        for i_url in img_urls.split(' '):
            if i_url:
                img_ffilename = str(i_url[i_url.rfind('/')+1:])
                if i_url[0] == '/': # related path, adding the URL prefix
                    i_url = url + i_url
#                print("\tProcessing image via the url ", i_url)
                (headers, data) = _retrieve_data(i_url, 0)
                
                if headers != -1 and data != -1:                 
                    print("\t\tSaving in file", img_ffilename)
                    img_ffilename = os.path.join(address, img_ffilename)               
                    f = open(img_ffilename, 'wb') # TODO
                    f.write(data)
                    f.close()
    except Exception as e:
        sys.stderr.write("ERROR ({},{}): Unable to process images from the url '{}':\n\t{}: {}\n".
            format(getframeinfo(currentframe()).filename,
                   getframeinfo(currentframe()).lineno,
                   url, str(sys.exc_info()[0]), e))
        return 1

    ### Print out results
    try:
        txt_ffilename = os.path.join(address, txt_filename)
        print("=> txt_ffilename=", txt_ffilename)
        tf = open(txt_ffilename, "w")
        tf.write(str(content))
        tf.close()
    except Exception as e:
        sys.stderr.write("ERROR ({},{}): Unable to write to the file '{}':\n\t{}: {}\n".
            format(getframeinfo(currentframe()).filename,
                   getframeinfo(currentframe()).lineno,
                   txt_ffilename, str(sys.exc_info()[0]), e))
        return 1
    
    return 0

#########
if __name__ == '__main__':
    exit_code = 1
    
    try:
        exit_code = process_data(sys.argv[1])
    except IndexError as e:
        _USAGE()
    except Exception as e:
        sys.stderr.write("ERROR ({},{}): {} '{}':\n\t{}: {}\n".
            format(getframeinfo(currentframe()).filename,
                   getframeinfo(currentframe()).lineno,
                   sys.argv[0], sys.argv[1], str(sys.exc_info()[0]), e))
    
    print("[ Exit code", exit_code , "]")
    sys.exit(exit_code)
