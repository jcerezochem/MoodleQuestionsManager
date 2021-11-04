#!/home/cerezo/miniconda2/envs/py3/bin/python3
#/usr/bin/env python3

import xml.etree.ElementTree as ET
from moodlexport import Question, Category, includegraphics
from googletrans import Translator
tr = Translator(service_urls=['translate.google.es'])
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

def translate_text(qtext):
    """"
Replace spacial (HTML) chars before translating. 
Keep track of replaced items wiht a numeric ID 
to place back the original tags
"""

    # Clean <span> sections
    # Nota: \w significa alfanumerico+underscore, es decir: \w=A-Za-z0-9_
    # (solo válido para unicode)
    # VER: https://docs.python.org/3/library/re.html
    matches = set(re.findall('<[/]{0,1}span[\w =\-\"]*>',qtext))
    for item in matches:
        qtext = qtext.replace(item,'')
    #qtext = qtext.replace('<p></p>','')
    # # Save some items from the translator
    save_items = {}
    # * Special items (&nbsp,<p>,</p>)
    special_items = ['&nbsp','<p>','</p>']
    for item in special_items:
        ID = generate_unique_ID(save_items.keys())
        save_items[ID] = item
        qtext = qtext.replace(item,' '+str(ID)+' ')
 
    # * <sup>*</sup> blocks
    matches = re.findall("<sup>[a-zA-Z0-9 \-+]+</sup>",qtext)
    matches_set = set(matches)
    for item in matches_set:
        ID = generate_unique_ID(save_items.keys())
        save_items[ID] = item
        qtext = qtext.replace(item,' '+str(ID)+' ')

    # * math envs
    if '«math' in qtext:
        mathq_ = re.findall('«math[\w =¨:\/\.»«§#;&+\-\(\),\[\]]+«/math»',qtext)
        mathq = []
        for item in mathq_:
            if item.count('«math') > 1:
                item_split = item.split('«math')
                mathq += [ '«math'+x for x in item_split[1:] ]
            else:
                mathq.append(item)
        mathq_check = re.findall('«math',qtext)
        if len(mathq)!=len(mathq_check):
            print('ERROR saving «math envs')
        for item in mathq:
            ID = generate_unique_ID(save_items.keys())
            save_items[ID] = item
            qtext = qtext.replace(item,' '+str(ID)+' ')

    # Translate once the items are saved
    try:
        qtext_tr = tr.translate(qtext).text
    except:
        print('Cannot translate the question')
        print(qtext)
        qtext_tr = qtext
    
    # And put items back
    for ID in save_items.keys():
        qtext_tr = qtext_tr.replace(' '+str(ID)+' ',save_items[ID])
        qtext_tr = qtext_tr.replace(str(ID),save_items[ID])

    return qtext_tr

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
    parser = argparse.ArgumentParser(description='Generate simple question banks from exported courses.')
    parser.add_argument('-f',metavar='questions.xml',help='Input XML file name',required=True)
    parser.add_argument('-sname',metavar='default',help='Name for the section',default='default')
    parser.add_argument('-trans',action='store_true',help='Translate questions ES->EN',default=False)
    parser.add_argument('-cleantxt',action='store_true',help='Clean HTML tags',default=False)
    parser.add_argument('-userev',action='store_true',help='Use revised file',default=False)
    parser.add_argument('-genpdf',action='store_true',help='Generate pdf files',default=False)
    # Parse input
    args = parser.parse_args()

    # Set vars from command line args
    clean_text = args.cleantxt
    translate = args.trans
    qfile = args.f
    sname = args.sname
    userev = args.userev
    genpdf = args.genpdf
    # For retrocompatibility
    get_single = False

    if userev:
        if clean_text:
            clean_text = False
            print('-cleantxt disabled with -userev')
        if translate:
            translate = False
            print('-trans disabled with -userev')
        print('')

    tree = ET.parse(qfile)
    root = tree.getroot()
    
    print(f'This file has {len(root)} categories')
    
    category_name = ''
    for qcategory in root:
        if len(qcategory[9]) == 0:
            print(f'\n>Main category: {qcategory[0].text}') 
            category_name =  qcategory[0].text.strip().replace('_','-')
        else:
            print(f'- Subcategory: {qcategory[0].text} ({len(qcategory[9])} questions)') 
            subcategory_name = qcategory[0].text.strip().replace('_','-')
            if sname == 'default':
                full_name = category_name + ' ' + subcategory_name
            else:
                full_name = sname
            category = Category(full_name.strip())
            # Generate or open file for revision
            if userev:
                iomode = 'r'
            else:
                iomode = 'w'
            frev = open(full_name.strip().replace(' ','-')+'.rst',iomode)
            for qentry in qcategory[9]:
                # Get index from tag name
                i = [ x.tag for x in qentry ].index('qtype')
                qtype = qentry[i].text
                # Run over allowed types (note we take multichoiceuam as multichoice)
                if (qtype[:11] == 'multichoice'):
                    question = Question('multichoice')

                    # Question ID
                    qid = int(qentry.attrib['id'])
                    question.idnumber(qid)

                    # Question name
                    qname = qentry[1].text
                    question.name(qname)

                    # Question text
                    if userev:
                        # Get to the next question
                        line = frev.readline()
                        while '**QUESTION:' not in line:
                            line =  frev.readline().strip()
                        qid_ = line.replace('**QUESTION: ','')
                        qid_ = int(qid_.replace('**',''))
                        # Check if ID has changed
                        if qid != qid_:
                            print('NOTE: Question ID has changed. Updating with revfile info.')
                            question.idnumber(qid_)
                        # Get name
                        line = frev.readline()
                        if '.. Name: ' in line:
                            qname_ = line.split(':')[1].strip()
                            # Check if name has changed
                            if qname != qname_:
                                print('NOTE: Question name has changed. Updating with revfile info.')
                                question.name(qname_)
                        # Go to revised text
                        while '.. Processed::' not in line:
                            line =  frev.readline()
                        # Read processed text
                        qtext = ''
                        line = frev.readline().strip()
                        while '.. Single: ' not in line and '.. end of text' not in line:
                            qtext += ' '+line
                            line = frev.readline().strip()
                        if '.. Single: ' in line:
                            # Get value of "single" option
                            single = line.split(':')[1].strip()
                    else:
                        qtext = qentry[2].text
                        print(f'**QUESTION: {qid}**',file=frev)
                        print(f'.. Name: {qname}',file=frev)
                        print('.. Original::',file=frev)
                        print(qtext,file=frev)
                        if clean_text:
                            qtext = strip_tags(qtext)
                        if translate:
                            qtext = translate_text(qtext)
                        print('.. Processed::',file=frev)
                        print(qtext,file=frev)
                        # Get value of "single" option and write to revfile
                        single = qentry[17][1][1].text
                        print(f'.. Single: {single}\n',file=frev)
                    # Manage images
                    if 'includegraphics' in qtext:
                        qtext = add_includegraphics(qtext)
                    question.text(qtext)
                    # For retrocompatibility
                    if 'single' not in locals():
                        print('NOTE: single info not in revfile. Taking from input XML')
                        get_single = True
                    if get_single:
                        single = qentry[17][1][1].text
                    question.single(int(single))

                    # General feedback
                    if userev:
                        while '**General Feedback' not in line:
                            line = frev.readline()
                        while '.. Processed::' not in line:
                            line = frev.readline()
                        # Read Feedback in multiple lines
                        # Ends with ".. end" mark (new versions)
                        # or blank line (for retrocompatibility)
                        fbtext = ''
                        line = frev.readline().strip()
                        while '.. end' not in line and len(line)>0:
                            fbtext += ' '+line
                            line = frev.readline().strip()
                        if 'includegraphics' in fbtext:
                            fbtext = add_includegraphics(fbtext)
                    else:
                        fbtext = qentry[4].text
                        print('**General Feedback**',file=frev)
                        print('.. Original::',file=frev)
                        print(fbtext,file=frev)
                        if fbtext and clean_text:
                            fbtext = strip_tags(fbtext)
                        if fbtext and translate:
                            fbtext = translate_text(fbtext)
                        print('.. Processed::',file=frev)
                        print(fbtext,file=frev)
                        print('.. end',file=frev)
                        print('',file=frev)
                    question.generalfeedback(fbtext)

                    # Answers
                    for i,answer in enumerate(qentry[17][0]):
                        if userev:
                            while '**Answer' not in line:
                                line = frev.readline()
                            while '.. Processed::' not in line:
                                line = frev.readline()
                            atext = frev.readline().strip()
                            while '.. Mark :' not in line:
                                line = frev.readline()
                            mark = line.split(':')[1].strip()
                        else:
                            atext = answer[0].text
                            print(f'**Answer {i}**',file=frev)
                            print('.. Original::',file=frev)
                            print(atext,file=frev)
                            if clean_text:
                                atext = strip_tags(atext)
                            if translate:
                                atext = translate_text(atext)
                            print('.. Processed::',file=frev)
                            print(atext,file=frev)
                            mark = answer[2].text
                        # Try to set the mark (fails it not a number)
                        try:
                            question.answer(atext,float(mark))
                        except:
                            print(full_name)
                            print(atext)
                            print(mark)
                            raise BaseException('Bye bye')
                        if not userev:
                            print(f'.. Mark : {float(mark)}',file=frev)
                            print('',file=frev)

                    # Tags
                    if userev:
                        while '**Tags' not in line:
                            line = frev.readline()
                        while '.. Processed::' not in line:
                            line = frev.readline()
                        tags = frev.readline()
                    else:
                        i = [ x.tag for x in qentry ].index('tags')
                        tags = qentry[i].text.strip()
                        print('**Tags**',file=frev)
                        print('.. Original::',file=frev)
                        print(tags,file=frev)
                        print('.. Processed::',file=frev)
                        print(tags,file=frev)
                        print('',file=frev)
                    #question.tags(tags) <- no existe el atributo


                    # We're done: add question to category
                    question.addto(category)

                #elif (qtype == 'essay'):
                #    qtext = qentry[2].text
                #    if clean_text:
                #        qtext = strip_tags(qtext)
                #    if translate:
                #        qtext = translate_text(qtext)
                #    question.text(qtext)
                else:
                    print(f'Cuestion type not exportable: {qtype}')
                if not userev:
                    print('\n\n======================================\n\n',file=frev)
            print('  ...Exported')
            frev.close()
            # Save category with questions
            category.savexml()
            if genpdf:
                category.savepdf()
