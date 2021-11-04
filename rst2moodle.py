#!/home/cerezo/miniconda2/envs/py3/bin/python3
#/usr/bin/env python3

import xml.etree.ElementTree as ET
from moodlexport import Question, Category, includegraphics
import re
import random

from io import StringIO
from html.parser import HTMLParser

class MLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.reset()
        self.strict = False
        self.convert_charrefs= True
        self.text = StringIO()
    def handle_data(self, d):
        self.text.write(d)
    def get_data(self):
        return self.text.getvalue()

def strip_tags(html):
    s = MLStripper()
    s.feed(html)
    return s.get_data()

def generate_unique_ID(IDs,i0=1000,ilast=9999,verbose=False):
    """
    Generate ID that is not in IDs. 
    The list IDs is NOT updated in the subrouite
    """

    ID = random.randint(i0,ilast)
    w = ilast-i0 +1
    while ID in IDs and len(IDs)<w:
        if verbose:
            print('ID in IDs',ID)
        ID = random.randint(0,9)
    if len(IDs)<w:
        #IDs.append(ID)
        return ID
    else:
        print('No unique ID can be formed')
        return -9999
    
def add_includegraphics(qtext):
    image_commands = re.findall('includegraphics\([\w\'\".\/,=]+\)',qtext)
    for image_command in image_commands:
        image_string = image_command.replace('includegraphics(','')
        image_string = image_string.replace(')','')
        image_options = image_string.split(',')
        image_path = image_options[0].replace("'",'')
        image_path = image_path.replace('"','')
        w,h,s = None,None,None
        for option in image_options[1:]:
            kwd = option.split('=')[0].strip()
            if kwd == 'width':
                w = int(option.split('=')[1].strip())
            elif kwd == 'height':
                h = int(option.split('=')[1].strip())
            elif kwd == 'style':
                s = option.split('=')[1].strip().replace("'",'')
                s = s.replace('"','')
        # Break the text to embeded the image
        qtext_fragments = qtext.split(image_command)
        if len(qtext_fragments) == 2:
            qtext_bfr = qtext_fragments[0]
            qtext_aft = qtext_fragments[1]
        else:
            # The same image appears more than once. This can be done, but requires some coding...
            print('WARNING: will not be properly handle. Maybe appears twice in the text')
            # For the moment work only on the first appearance
            qtext_bfr = qtext_fragments[0]
            qtext_aft = qtext_fragments[1]
        # Use option includegraphics from moodlexport
        if w and h and s:
            qtext = qtext_bfr + includegraphics(image_path,width=w,height=h,style=s) + qtext_aft
        elif w and h:
            qtext = qtext_bfr + includegraphics(image_path,width=w,height=h) + qtext_aft
        elif w and s:
            qtext = qtext_bfr + includegraphics(image_path,width=w,style=s) + qtext_aft
        elif h and s:
            qtext = qtext_bfr + includegraphics(image_path,height=h,style=s) + qtext_aft
        elif w:
            qtext = qtext_bfr + includegraphics(image_path,width=w) + qtext_aft
        elif h:
            qtext = qtext_bfr + includegraphics(image_path,height=h) + qtext_aft
        elif s:
            qtext = qtext_bfr + includegraphics(image_path,style=s) + qtext_aft
        else:
            qtext = qtext_bfr + includegraphics(image_path) + qtext_aft
            
    return qtext


if __name__ == '__main__':

    import argparse

    # Input parser. Set flags
    parser = argparse.ArgumentParser(description='Generate simple question banks from rst files.')
    parser.add_argument('-f',metavar='questions.rst',help='Input rst file name',required=True)
    parser.add_argument('-sname',metavar='default',help='Name for the section',default='default')
    parser.add_argument('-genpdf',action='store_true',help='Generate pdf files',default=False)
    # Parse input
    args = parser.parse_args()

    # Set vars from command line args
    qfile = args.f
    sname = args.sname
    genpdf = args.genpdf
    
    # Initialization
    question = None
    
    # Generate or open file revised rst file
    iomode = 'r'
    frev = open(qfile,iomode)
    
    # Create category
    if sname == 'default':
        # Check if the file starts with category name
        line = frev.readline()
        if '**CATEGORY:' in line:
            sname = line.replace('**CATEGORY: ','')
            sname = sname.replace('**','').strip()
        else:
            frev.close()
            frev = open(qfile,iomode)
            sname = qfile.replace('.srt','-rst')
    
    # Start category
    category = Category(sname)

    # Run over the whole file
    for line in frev:
        
        # New question
        if '**QUESTION:' in line:
            if question is not None:
                # Add las question to category
                question.addto(category)
            question = Question('multichoice')
            # Get ID
            qid = line.replace('**QUESTION: ','')
            qid = int(qid.replace('**',''))
            question.idnumber(qid)
            
        # Question name
        elif '.. Name: ' in line:
            qname = line.split(':')[1].strip()
            question.name(qname)
            
        # Processed Question text
        elif '.. Processed::' in line:
            qtext = ''
            line_ = frev.readline().strip()
            while '.. Single: ' not in line_ and '.. end of text' not in line_:
                qtext += line_
                line_ = frev.readline().strip()
            if '.. Single: ' in line_:
                # Get value of "single" option
                single = line_.split(':')[1].strip()
            # Manage images
            if 'includegraphics' in qtext:
                add_includegraphics(qtext)
            question.text(qtext)
            # Set "single" parameter
            question.single(int(single))
            
        # Get value of "single" option (in case it was not already taken
        elif '.. Single: ' in line:
            single = line.split(':')[1].strip()
            question.single(int(single))
            
        # General feedback
        elif '**General Feedback' in line:
            line_ = frev.readline()
            while '.. Processed::' not in line_:
                line_ = frev.readline()
            # Read Feedback in multiple lines
            # Ends with ".. end" mark (new versions)
            # or blank line (for retrocompatibility)
            fbtext = ''
            line = frev.readline().strip()
            while '.. end' not in line and len(line)>0:
                fbtext += line
                line = frev.readline().strip()
            if 'includegraphics' in fbtext:
                fbtext = add_includegraphics(fbtext)
            question.generalfeedback(fbtext)

        # Answers
        elif '**Answer' in line:
            line_ = frev.readline()
            while '.. Processed::' not in line_:
                line_ = frev.readline()
            line_ = frev.readline().strip()
            atext = ''
            while '.. Mark :' not in line_:
                atext += line_
                line_ = frev.readline().strip()
            mark = line_.split(':')[1].strip()
            # Create answer
            question.answer(atext,float(mark))

        # Tags
        if '**Tags' in line:
            line_ = frev.readline()
            while '.. Processed::' not in line_:
                line_ = frev.readline()
            tags = frev.readline()
            #question.tags(tags) <- no existe el atributo

      
    print('  ...Done')
    frev.close()
    # Save category with questions
    category.savexml()
    if genpdf:
        category.savepdf()
