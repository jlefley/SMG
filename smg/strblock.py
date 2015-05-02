#!/usr/bin/env python
#
# strblock.py  -- module used to format strings into text blocks.
#

# Copyright (c) 2000, Kevin Quick
# All Rights Reserved
# See the LICENSE file for more information.

# Interfaces:
#    ljustblock(text_string, maximum-line-length, width-to-height-ratio)
#    rjustblock(text_string, maximum-line-length, width-to-height-ratio)
#    centerblock(text_string, maximum-line-length, width-to-height-ratio)
#
# These operations create a left, right, or center justified block of
# text, respectively.  The difference between these functions and the
# string.ljust/string.rjust/string.center functions is that the string
# versions return a single line of text only, whereas the strblock
# versions attempt to replace whitespace with carriage-returns at
# strategic points to create a pleasing block of text (think of a
# paragraph-fill operation in your editor...).

# There are two primary modes of blocking text: paragraph-fill and
# ratio-arrange.

# The paragraph-fill blocking mode is the more customary
# "paragraph-fill" operation which insures that each line has as many
# words as possible but which doesn't exceed a pre-determined right
# margin; the last line will simply terminate after the last word.  To
# select this mode, simply specify the <width-to-height-ratio> to be
# zero.

# The ratio-arrange blocking mode is more complex.  It adheres to the
# min/max set of constraints, but it also tries to arrange the text
# with a given ratio for the height v.s. the width, assuming a
# standard font aspect ratio.
# Examples:  <width-to-height-ratio>    Arrangement
#               1                       square
#               2                       twice as wide as high
#               0.5                     Twice as high as wide

# <maximum-line-length> specifies the maximum number of characters for
# each line.  This parameter overrides all other parameters and will
# not be violated except in the case of a single word which exceeds
# this length.  If zero, then there is no maximum line length (should
# be used only with ratio-arrange blocking mode.

# <width-to-height-ratio> specifies the general ratio of the width of
# the text block to its height.  This ratio is an APPEARANCE
# measurement and assumes standard font aspect ratios: this is NOT the
# ratio for the number-of-characters to number-of-lines.  This value
# may be a floating point value.  If zero, paragraph-fill mode is used
# instead of ratio-arrange.

import string


aspect = 5   # number of characters whose width approx. equals height of 1 line

def _splittext_(text_string, maxchar):
    rtext = []
    minwidth = 0
    while len(text_string) > maxchar:
        ws = string.rfind(text_string, ' ', 0, maxchar)
        #print '   maxchar=%d ws=%d minwidth=%d rtext=%s text_string=%s'%(maxchar, ws, minwidth, rtext, text_string)
        if ws == -1:
            minwidth = 1
            ws = string.find(text_string, ' ', maxchar)
        if ws == -1:
            ws = len(text_string)
        rtext.append(text_string[:ws])
        text_string = text_string[ws+1:]
        while len(text_string) and text_string[0] == ' ':
            text_string = text_string[1:]
    rtext.append(text_string)
    actlen = max(map(len, rtext))
    nlines = len(rtext)
    return (actlen, nlines, minwidth, string.join(rtext, '\n'))

    
def _blocktext_(text_string, maxchar, ratio):
    options = {}
    minwidth = 0

    while minwidth == 0 and maxchar > 1:
        foo = _splittext_(text_string, maxchar)
        nchars, nlines, minwidth, block = foo
        #nchars, nlines, minwidth, block = _splittext_(text_string, maxchar)
        bratio = float(nchars) / float(nlines) / aspect
        #bratio = float(nlines) / (float(nchars) / aspect)
        if ratio == 0 or bratio == ratio:
            # Got lucky and nailed it.  Quit now
            return block
        options[abs(bratio-ratio)] = block
        #print 'minwidth=%d maxchar=%d ratio=%f %s --> bratio=%f'%(minwidth, maxchar, ratio, foo, bratio)
        maxchar = maxchar - 1

    #print 'Final ratio differentials: %s'%options.keys()
    rratio = min(options.keys())
    return options[rratio]


def ljustblock(text_string, maxchar, ratio):
    return _blocktext_(text_string, maxchar, ratio)


def rjustblock(text_string, maxchar, ratio):
    btext = _blocktext_(text_string, maxchar, ratio)
    btl = string.split(btext, '\n')
    btl_len = max(map(len, btl))
    rtext = []
    for tl in btl:
        rtext.append(string.rjust(tl, btl_len))
    return string.join(rtext, '\n')


def centerblock(text_string, maxchar, ratio):
    btext = _blocktext_(text_string, maxchar, ratio)
    btl = string.split(btext, '\n')
    btl_len = max(map(len, btl))
    rtext = []
    for tl in btl:
        rtext.append(string.center(tl, btl_len))
    return string.join(rtext, '\n')


def para(para_str, first_indent, indent, linelen=75):
    """Returns the specified paragraph as a string..  The first
    argument is the paragraph as represented by a string or array of
    strings.  The second argument is the indent string which is used
    to indent the *first* line only.  The third argument is the indent
    string which is used to indent the remaining lines.  The last
    argument is a number which is the maximum right margin.  The
    paragraph is output as one or more lines that are broken at
    whitespace so as to not exceed the right margin.
    A special case is accorded any line which starts with a '#'
    character: this line is NOT indented to preserve maximal C
    directive or comment characteristics of this line.
    Another special case is text enclosed in double quotes, which
    will not be broken across lines."""

    # First, find out if there are any blank lines in the input.  These blank
    # lines are paragraph separators and we have actually been handed
    # multiple paragraphs, where the paragraph divisions must be preserved.
    # Note that we can do this even before we check four double-quoted
    # portions of the text; since we preserve blank lines it doesn't
    # matter if the blank line occurs in the middle of a quoted string or
    # not although we need to 

    lead = first_indent
    
    # Next, find all text enclosed in double quotes and mark that out
    # as separate.

    #locks = string.split(string.strip(para_str), '"')
    blocks = string.split(para_str, '"')

    for blkii in range(0, len(blocks), 2):

        # Find blank lines, first removing whitespace that might be in
        # the way.
##        sections = string.split(string.join(map(string.strip,
##                                                string.split(blocks[blkii],
##                                                             '\n')),
##                                            '\n'),
##                                '\n\n')
        sections = string.split(blocks[blkii], '\n\n')

        for psectii in range(len(sections)):

            # Now separate out lines starting with '#' and don't format those
            lines = string.split(sections[psectii], '\n')
            lines.append('#END')  # Add flag so that everything is caught below
            para = []
            text = []
            for line in lines:
                if len(line) == 0:
                    para.append(line)
                    continue
                if line[0] != '#':
                    text.append(line)
                    continue
                # Current line starts with #; perform paragraph fill on all
                # previous lines, add them to the output, and then add the
                # current line to the output.
                if len(text):
                    # Reblock text based on current indent
                    fmt = string.split(ljustblock(string.join(text),
                                                  linelen - len(lead), 0),
                                       '\n')
                    fmt2 = []
                    for newline in fmt:
                        para.append('%s%s'%(lead, newline))
                        if lead == first_indent and len(lead) != len(indent):
                            # Indent width changed; readjust remainder for
                            # second pass and then break out of current pass
                            lead = indent
                            fmt2 = string.split(ljustblock(
                                string.join(fmt[1:]),
                                linelen - len(lead),
                                0), '\n')
                            break
                        lead = indent
                    # Now do second pass [only for case where first_indent
                    # length doesn't match indent length.
                    for newline in fmt2:
                        para.append('%s%s'%(lead, newline))
                    # Now prepare to continue processing input
                    text = []
                if line != '#END': para.append(line)
            # All input for this section has been processed and reformatted.
            # Replace the previous version with this new version.
            sections[psectii] = string.join(para, '\n')

        blocks[blkii] = string.join(sections, '\n\n')

    # The portions enclosed in double quotes was skipped.  Rebuild the
    # output with the double quoted portions. We might try to reblock
    # around the double quoted portions, but this is more than a little
    # difficult, so we'll punt on this for now.
    return '%s\n'%string.join(blocks, '"')


if __name__ == "__main__":
    import sys
    usage = "%s {l|c|r|p} <max-chars> <ratio> <string>"%sys.argv[0]
    if len(sys.argv) != 5:
        print usage
        sys.exit(1)
    if sys.argv[1] == 'l':
        print ljustblock(sys.argv[4],
                         string.atoi(sys.argv[2]),
                         string.atof(sys.argv[3]))
    elif sys.argv[1] == 'r':
        print rjustblock(sys.argv[4],
                         string.atoi(sys.argv[2]),
                         string.atof(sys.argv[3]))
    elif sys.argv[1] == 'c':
        print centerblock(sys.argv[4],
                          string.atoi(sys.argv[2]),
                          string.atof(sys.argv[3]))
    elif sys.argv[1] == 'p':
        linelen = string.atoi(sys.argv[2])
        print '-'*linelen
        print para(sys.argv[4],
                   '++++ ++ +++ +++++ +++++++++ ++++:',
                   '  ---- -- ------- --------- ----:', linelen)
        print '-'*linelen
        print para(sys.argv[4],
                   '++++ ++ +++ +++++ +++++++++ ++++:',
                   '------- --------- ----:', linelen)
        print '-'*linelen
        print para(sys.argv[4],
                   '+++++ +++++++++ ++++:',
                   '---- -- - --------- --------- ----:', linelen)
        print '-'*linelen
    else:
        print usage
        sys.exit(1)
    sys.exit(0)
