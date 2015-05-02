#!/usr/bin/env python
#
# entitle_ps - Module to add a title and other page decoration to a
#              Postscript file.  There are some rather broad assumptions
#              made, resulting in applicability to a fairly narrow range
#              of Postscript files, but the main target is output from
#              the GViz dot program.

# Copyright (c) 2000,2007, Kevin Quick
# All Rights Reserved
# See the LICENSE file for more information.

#
# Main interfaces:
#
#    entitle_ps(ps_filename, title, urtext=None, ultext=None, lltext=None)
#
# where:
#   ps_filename = output Postscript file
#   title       = title text to place on first page
#   urtext      = text line(s) for upper right of page
#   ultext      = text line(s) for upper left of page
#   lltext      = text line(s) for lower left of page
#


# {{{ Initialization

import sys,os,string,shutil

if __name__ == "__main__":
    print 'No command line use supported...'
    os.system("head -12 %s"%sys.argv[0])
    sys.exit(1)

# }}}


def start_eq(fullstring, startstring):
    return fullstring[:len(startstring)] == startstring


def add_ps_string(ps_file, text_string, _x_, _y_,
                  fontname="Times-Roman", fontsize='12.00', align='c'):
    ps_file.write('%s /%s set_font\n'%(fontsize, fontname))
    ps_file.write('gsave 10 dict begin\n')
    ps_file.write('%s %s moveto (%s) %d %s %s alignedtext\n'%(
        _x_, _y_, text_string, len(text_string), fontsize,
        {'c':"-0.5", 'l':'0.0', 'r':'-1.0'}[align]))
    ps_file.write('end grestore\n')
    

def entitle_ps(ps_filename, title, urtext=None, ultext=None, lltext=None):
    ofilename = '%sO'%ps_filename
    ofile = open(ofilename, 'w')
    
    ifile = open(ps_filename, 'r')
    inp_ps = ifile.readlines()
    ifile.close()

    # Control variables
    TITLESIZE="18.00"
    TEXTSIZE="6.00"
    #TITLEFONT="Times-Bold"
    #TEXTFONT="Times-Roman"
    TITLEFONT="Palatino-Bold"
    TEXTFONT="Palatino-Roman"

    # Initialize values that are set by reality as we parse the PS file
    tcenter = 1

    # Internal use
    top = 40
    if urtext:
        top = 30 + (len(string.split(urtext, '\n')) * 10)
    if top < 40: top = 40
    
    found = []

    for line in inp_ps:
        if start_eq(line, '%%Title:'):
            ofile.write('%%%%Title: %s\n'%title)
        elif start_eq(line, '%%BoundingBox: '):
            try:
                a,b,c,d=list(map(string.atoi, string.split(line, " ")[1:5]))
                if a > 21: a = 21
                if b > 45: b = 45
                if c < 570: c = 570
                if d < 755: d = 755
                ofile.write('%%%%BoundingBox: %d %d %d %d\n'%(a,b,c,d))
            except: pass
        elif start_eq(line, '%%PageBoundingBox: '):
            pass
        elif start_eq(line, '%%Page: 1 1'):
            ofile.write(line)
            found.append("Page 1 1")
        elif start_eq(line, 'gsave') and \
             "Page 1 1" in found and \
             "Titled" not in found:
            ofile.write("gsave\n1.0 1.0 scale\n90 rotate\n")
            ofile.write("0 -%d translate\n"%top)
            add_ps_string(ofile, title, 422, 5,
                          TITLEFONT, TITLESIZE, ['l', 'c'][tcenter])
            if urtext:
                urlines = string.split(urtext, '\n')
                for urlnum in range(len(urlines)):
                    ury = top - 20 - ((urlnum + 1) * 7)
                    add_ps_string(ofile, urlines[urlnum], 750, ury,
                                  TEXTFONT, TEXTSIZE, 'r')
            if ultext:
                lines = string.split(ultext, '\n')
                for lnum in range(len(lines)):
                    uly = top - 20 - ((lnum + 1) * 6)
                    add_ps_string(ofile, lines[lnum], 40, uly,
                                  TEXTFONT, TEXTSIZE, 'l')
                
            if lltext:
                ofile.write("grestore\ngsave\n1.0 1.0 scale\n90 rotate\n")
                #ofile.write("0 0 translate\n")  #kwq why doesn't this work?!
                ofile.write("50 -570 translate\n");
                lllines = string.split(lltext, '\n')
                top = len(lllines) * 7 + 8
                for llnum in range(len(lllines)):
                    add_ps_string(ofile, lllines[llnum],
                                  0, (top - ((llnum+1) * 7)),
                                  TEXTFONT, TEXTSIZE, 'l')
            ofile.write("grestore\n")
            ofile.write(line)
            found.append("Titled")
        elif string.find(line, "/bold { 2 setlinewidth } bind def") > -1:
            # Default bolded lines are too narrow and hard to see still.
            ofile.write("/bold { 3 setlinewidth } bind def\n");
        else:
            ofile.write(line)

    ofile.close()
    shutil.copyfile(ofilename, ps_filename)
    os.remove(ofilename)
