#!/bin/bash

# Steps to apply changes made to .rst files and generate new xml and pdf files

# Redo the xml file with -userev and -genpdf
../Tools/extract_questions_new.py -f questions*.xml -userev -genpdf
if (( $? )); then exit; fi
# Fix tex and regenerate pdf
for file in *tex; do echo $file; ../Tools/fix_question_tex.sh $file; pdflatex $file; rm ${file/.tex/}.{aux,log} -v; done
# Check that rst files are ok and then backup rst files
for file in *rst; do cp $file ${file}.bk -v; done

