#! /usr/bin/env python

# sffms2rtf - LaTeX (sffms class) to RTF converter
# Copyright (C) 2013 Avi Rozen <avi.rozen@gmail.com>
#
# sffms2rtf is based on a PHP script available at
# https://github.com/mcdemarco/mcdemarco.github.com/tree/master/sffms/sffms2rtf
# Copyright (C) 2013 M. C. DeMarco <mcd@mcdemarco.net>
#
# sffms2rtf is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import sys
import re

def cleanline(line):
   newline = line;
   newline = newline.replace("\\", "\a")
   # eat space at start of line
   newline = newline.strip()
   # handle LaTeX comments and \%
   newline = newline.replace("\a%", "[\a:percent]")
   newline = re.sub(r"%.*$", "", newline)
   newline = newline.replace("[\a:percent]", "%")
   # handle explicit spacing
   newline = newline.replace("~", " ")
   # escape sequences: \{, \}, \\, literal openbrace, closebrace, or backslash
   newline = newline.replace("\a{", "[\a:obr]")
   newline = newline.replace("\a}", "[\a:cbr]")
   newline = newline.replace("\a#", "#")
   newline = re.sub(r"\a\a[ ]*", "\\line ", newline)
   # handle some accents in a bad way
   newline = newline.replace( "\av{", "{\\cf2 ^")
   newline = newline.replace( "\a'{", "{\\cf2 '")
   # handle known LaTeX font commands
   newline = newline.replace( "\aemph{", "{\\ul ")
   newline = newline.replace( "\aem ", "\\ul ")
   newline = newline.replace( "\athought{", "{\\ul ")
   newline = newline.replace( "\atextit{", "{\\ul ")
   newline = newline.replace( "\ait ", "\\ul ")
   newline = newline.replace( "\atextsl{", "{\\ul ")
   newline = newline.replace( "\asl ", "\\ul ")
   newline = newline.replace( "\aslshape ", "\\ul ")
   # for double underline, use \uldb, for actual sc use \scaps
   newline = newline.replace( "\atextsc{", "{\\uldb ")
   newline = newline.replace( "\asc ", "\\uldb ")
   newline = newline.replace( "\ascshape ", "\\uldb ")
   newline = newline.replace( "\atextbf{", "{\\b ")
   newline = newline.replace( "\abf ", "\\b ")
   newline = newline.replace( "\abfseries ", "\\b ")
   # handle some introduced commands
   newline = newline.replace( "\adots\a", "...")
   newline = newline.replace( "\adots", "...")
   return newline.strip()


def main():
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print >>sys.stderr, 'Usage: %s <sffms-latex-file> [<rtf-file>]\n' % sys.argv[0]
        return -1

    latex_path = os.path.normpath(os.path.expanduser(sys.argv[1]))
    if not os.path.exists(latex_path):
        latex_path = latex_path + '.tex'
        if not os.path.exists(latex_path):
            raise RuntimeError('cannot find source LaTeX file -- %s' % latex)
    if len(sys.argv) == 2:
        rtf_path = re.sub('\.tex$', '', latex_path) + '.rtf'
    else:
        rtf_path = os.path.normpath(os.path.expanduser(sys.argv[2]))

    latex_file = open(latex_path, 'rt')
    rtf_file = open(rtf_path, 'wt')

    rtf_file.write( \
       "{\\rtf1\\ansi\\deff1\\ansicpg10000\n" +
       "{\\fonttbl\\f0\\fmodern\\fcharset77 Courier;\\f1\\froman\\fcharset77 Times New Roman;}\n" + 
       "{\\colortbl;\\red255\\green255\\blue255;\\red255\\green0\\blue0;}\n" + 
       "\\margl1440\\margr1440\\vieww12240\\viewh15840\\viewkind1\\viewscale100\\titlepg\n")

    # parse document header
    thehead = ''
    for line in latex_file:
        if re.search(r'\\begin\{document\}', line):
            break
        line = cleanline(line)
        if thehead:
            thehead += ' ' + line
        else:
            thehead = line
    
    # get the sffms options, though we're not using them (yet)
    options = []
    matches = re.search(r'(\adocumentclass\[)(.*?)(\])', thehead)
    if matches:
       options = matches.group(2).split(',')

    # get the title, author, wc, etc
    title = 'A Story'
    matches = re.search(r'(\atitle{)(.*?)(})', thehead)
    if matches:
       title = matches.group(2)
    author = 'John Doe'
    matches = re.search(r'(\aauthor{)(.*?)(})', thehead)
    if matches:
       author = matches.group(2)
    authorname = author
    matches = re.search(r'(\aauthorname{)(.*?)(})', thehead)
    if matches:
       authorname = matches.group(2)
    surname = author.split()[-1]
    matches = re.search(r'(\asurname{)(.*?)(})', thehead)
    if matches:
       surname = matches.group(2)
    runningtitle = title
    matches = re.search(r'(\arunningtitle{)(.*?)(})', thehead)
    if matches:
       runningtitle = matches.group(2)
    address = ''
    matches = re.search(r'(\aaddress{)(.*?)(})', thehead)
    if matches:
       address = matches.group(2)
    disposable = True if re.search(r'\adisposable ', thehead) else False

    # word count:
    # - take the most recent value computed by latex, if any
    # - override with value specified by the \wordcount macro (empty
    #   string disables wordcount display)
    # - if no value was set then insert a formula field to compute
    #   publisher wordcount as 275 times the page count to get a
    #   result close enough to what sffms computes (the field is
    #   updated upon save/print etc. from ms word)
    wordcount = ''
    try:
       auxfile_path = re.sub('\.tex$', '', latex_path) + '.aux'
       if os.stat(auxfile_path).st_mtime > os.stat(latex_path).st_mtime:
          auxfile = open(auxfile_path, 'rt')
          for auxline in auxfile:
             matches = re.search(r'\\newlabel{sffmswc}{{([0-9]*)}', auxline)
             if matches:
                wordcount = matches.group(1)
                break
          auxfile.close()
    except:
       pass
    matches = re.search(r'(\awordcount{)(.*?)(})', thehead)
    if matches:
       wordcount = matches.group(2)
    if not wordcount:
       if not matches:
          wordcount = '{\\field{\\*\\fldinst { = 275 * \\field{\\*\\fldinst NUMPAGES \\\\*MERGEFORMAT} } \\\\*MERGEFORMAT}{\\fldrslt 0}}'

    rtf_file.write( \
       "{\\info\n" +
       ("{\\title %s}\n" % title) +
       "{\\doccomm Converted from LaTeX with sffms2rtf.py, Copyright (C) 2013 Avi Rozen}" +
       ("{\\author %s}}" % author) +
       "{\\headerf}\n" +
       "{\\header\\pard\\qr\\f0{" + surname + " / " + runningtitle.upper() + " / " + "{\\field{\\*\\fldinst PAGE }}}\\par}\n" +
       "{\\i0\\scaps0\\b0\n" + 
       "\\deftab360\n" +
       "\\pard\\tx7500\\pardeftab360\\ql\\qnatural\n" +
       "\\f0\\fs24 \\cf0\n" +
       authorname +
       (("\\tab " + wordcount + " words") if wordcount else "") +
       "\\line\n" +
       address + "\\par\n" +
       "\\pard\\pardeftab720\\ql\\qnatural\\sb4000\\par\n" + 
       "\\pard\\sl510 \\qc\\f0\\fs24\n" + 
       title.upper() + "\\\n"
       "by " + author + "\\par\n" +
       "\\pard\\sl510\\f0\\fs24\n" + 
       "\\cf0 \\\n"
       )
    
    # parse document body
    breaking = False
    done = False
    prefix = ''
    suffix = ' '
    for line in latex_file:
        line = cleanline(line)
        if line.strip() == '':
           line = ''
           suffix = ''
           if not breaking:
              breaking = True
              prefix = '\\par\n'
        else:
           if breaking:
              breaking = False
              prefix = '\\pard\\sl510\\f0\\fs24\\cf0      '
           line = line.replace('\t', ' ')
           line = line.replace('\a ', ' ')
           line = line.replace('~', ' ')
           line = line.replace('--', '-')
           line = line.replace('{``}', '\"')
           line = line.replace('{''}', '\"')
           line = line.replace("``", '\"')
           line = line.replace("''", '\"')
           if re.search(r'\ascenebreak', line):
              line = line.replace('\ascenebreak', '\\pard\\sl510\\qc\\cf0 #')
              prefix = ''
           if re.search(r'\anewscene', line):
              line = line.replace('\anewscene', '\\pard\\sl510\\qc\\cf0 #')
              prefix = ''
           if re.search(r'\achapter\{', line):
              line = line.replace('\achapter{', '\\pard\\sl510\\qc\\cf0 \\par\\pard\\sl510\\qc\\cf0 {\\b ')
              prefix = ''
           if re.search(r'\achapter\*\{', line):
              line = line.replace('\achapter*{', '\\pard\\sl510\\qc\\cf0 {\\b ')
              prefix = ''
           if re.search(r'\apart\{', line):
              line = line.replace('\apart{', '\\pard\\sl510\\qc\\cf0 {\\b ')
              prefix = ''
           if re.search(r'\aend\{document\}', line):
              line = '\\pard\\par\\pard\\sl510 \\qc\\f0\\fs24 # # # # #\\par'
              prefix = ''
              done = True

        # mark unknown macros in red 
        line = re.sub(r'(\a)([A-Za-z0-9]*)', r'{\\cf2 \\\\\2}', line);
        rtf_file.write(prefix + line + suffix)
        prefix = ''
        suffix = ' '
        if done:
           rtf_file.write('}}\n')
           break

    rtf_file.close()
    latex_file.close()
            
    return 0

if __name__ == '__main__':
    sys.exit(main())
