import os
import sys
from inspect import currentframe, getframeinfo # for clear diagnostics
from html.parser import HTMLParser

#### Constants & globals
title = ()
header_date = ""
content = ""
img_urls = ""
raw_content = ""
title_found = 0
is_title = 0
is_body = 0
skip = 0
wrap_columns = 79
#########

class OfflinerHTMLParser(HTMLParser):
    # Tag constants
#    decor_tags = ('b', 'center', 'font', 'i', 'span', 'strike', 'strong', 'time', 'h1', 'h2', 'h3', 'u', 'ul') # TODO: correct work with 'strike'
    break_line_tags = ('hr')
    star_mark_tags = ('li', 'ol')
    newline_tags = ('blockquote', 'br', 'div', 'p', 'tr')
    element_tags = ('img', 'select')
    link_tags = ('a')
    skip_tags = ('applet', 'audio', 'form', 'iframe', 'link', 'map', 'option', 'noscript', 'script', 'span', 'style', 'video') # TODO: correct work with 'iframe'

    #########
    def __init__(self, hdate):
        global header_date
    
        super().__init__(convert_charrefs=True)
        header_date = hdate
        header_date = hdate
    
    #########
    def handle_starttag(self, tag, attrs):   
        """Function for work with starting tags"""

        global img_urls
        global raw_content
        global is_title
        global title_found
        global is_body
        global skip

        try:
            self.mod_tag = tag.lower()
            if is_body == -1: # ignore the rest of the document
                return
            
#            print("Encountered a start tag: '", self.mod_tag, "'")

            ### Title tag ###
            if self.mod_tag == "title":
                is_title = 1
                title_found = 1

            ### Body tag ###
            elif self.mod_tag == "body":
                is_body = 1

            else:
                ### Tags to skip ###
                if self.mod_tag in self.skip_tags:
                    skip = 1

                if is_body == 1:
                
                    # if self.mod_tag in self.decor_tags:
                        # raw_content += ' '

                    ### Thematic change line tags ###
                    if self.mod_tag in self.break_line_tags:
                        raw_content += '\n' if raw_content != '' else ''
                        raw_content += ('-' * 79) + '\n'

                    ### Star mark tags ###
                    elif self.mod_tag in self.star_mark_tags:
                        raw_content += '\n' if raw_content != '' else ''
                        raw_content += '* '

                    ### New line tags ###
                    elif self.mod_tag in self.newline_tags:
                        raw_content += '\n' if raw_content != '' else ''

                    ### Element tags ###
                    elif self.mod_tag in self.element_tags:
                        raw_content += '[' + self.mod_tag.upper()
                        if self.mod_tag == "img": # images
                            for key, value in attrs:
#                                print("IMG key=", key, " value=", value)
                                if key == 'alt' and value != '':
                                    raw_content += ': ' + value
                                elif key == 'src':
                                    img_name = str(value[value.rfind('/')+1:])
                                    raw_content += ' <' + img_name + '>'
                                    
                                    # File extention exists and there are no special script-like symbols
                                    # and Lenta.ru specifics like src="//.."
                                    if value[0:2] != "//" and \
                                       img_name.rfind('.') != -1 and \
                                       img_name.rfind('?') == -1 and \
                                       img_name.rfind('&') == -1:
                                        img_urls += ' ' + value
#                                        print("\tsrc=", value, "First_two_symbols=", value[0:2])
                                
                    ### Link tags ###
                    elif self.mod_tag in self.link_tags:
                        raw_content += ' [ '
        except Exception as e:
            sys.stderr.write("ERROR ({},{}): Unable to handle starttag:\n\t{}: {}\n".
                format(getframeinfo(currentframe()).filename,
                       getframeinfo(currentframe()).lineno,
                       str(sys.exc_info()[0]), e))
            return 1

    #########
    def handle_endtag(self, tag):
        """Function for work with ending tags"""

        global is_title
        global is_body
        global skip
        global content
        global raw_content
    
        try:
            self.mod_tag = tag.lower()
            if is_body == -1:            
                return

#            print("Encountered an end tag: '", self.mod_tag, "'")

            ### Title tag ###
            if self.mod_tag == "title":
                is_title = 0

            ### Body tag ###
            elif self.mod_tag == "body":            
                # Specify title
                content = title
                
                # Delete empty lines
                raw_content = "".join([s for s in raw_content.strip().splitlines(True) if s.strip()])

                # Wrap text
                count = 0
                for word in raw_content.split(' '): # split into words
                    count += len(word)
                    if count <= wrap_columns:
                        content += ' ' + word
                    else:
#                        print("Symbols=", count, ", wrapping")
                        content += '\n' + word
                        count = 0                    
            
                is_body = -1
                
            else:

                ### Tags to skip ###
                if tag in self.skip_tags:
                    skip = 0

                if is_body == 1:
                    # if tag in self.decor_tags:
                        # raw_content += ' '

                    ### New line tags ###
                    if tag in self.newline_tags:
                        raw_content += '\n'

                    ### Element tags ###
                    elif self.mod_tag in self.element_tags:
                        raw_content += ']'

                    ### Link tags ###
                    elif self.mod_tag in self.link_tags:
                        raw_content += ' ] '
        except Exception as e:
            sys.stderr.write("ERROR ({},{}): Unable to handle endtag:\n\t{}: {}\n".
                format(getframeinfo(currentframe()).filename,
                       getframeinfo(currentframe()).lineno,
                       str(sys.exc_info()[0]), e))
            return 1
                                
    #########
    def handle_data(self, data):
        """Function for work with data between tags"""

        global title
        global raw_content
        
        try:
            if data == None or data == '':
                return
        
            ### Title tag ###
            if is_title == 1:
                # title = self.mod_data.split()
                # print("Title: '", ' ""'.join(title),"'"" '", self.mod_data)
                title = data + "\n(" + header_date + ")\n" + ('-' * 31) + "\n\n"
            else:
                if skip == 1:
                    return

                if is_body == 1 and data and data != ' ':
                    raw_content += data
        except Exception as e:
            sys.stderr.write("ERROR ({},{}): Unable to handle data:\n\t{}: {}\n".
                format(getframeinfo(currentframe()).filename,
                       getframeinfo(currentframe()).lineno,
                       str(sys.exc_info()[0]), e))
            return 1
                
    #########
    def get_content(self):
        """Function for returning the final content"""

        return content, img_urls
        
