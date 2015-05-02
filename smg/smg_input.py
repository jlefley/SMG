#!/usr/bin/env python
#
# smg_input - Module to read in an SMG file and create a State Machine for it
#
# This module is a subsidiary module to the primary smg.py module.  This
# module is called to read and parse the input smg file.
#

# Copyright (c) 2000-2002, Kevin Quick
# All Rights Reserved
# See the LICENSE file for more information.

# Main interfaces:
#
#    sfile = smg_file(filename=None)   - Opens an SMG input file
#    sfile.filename(filename=None)     - Reads or sets-and-reads the filename
#    sfile.read()                      - Reads & parses input file into phrases
#    sfile.phrases()                   - Returns phrases read from input file
#
#    phrase + text     - Appends text to the phrase
#    phrase.type()     - Return phrase type: C_code, SM_stmt, SM_code, P_code
#    phrase.contents() - Return text contents of phrase
#    phrase.filename() - Filename from which phrase was obtained
#    phrase.line_num() - Line number for first line of phrase in input file
#    phrase.write_C_code(outfile) - Writes C code for phrase to outfile


# {{{ Initialization

import sys,os,string,time
from smg_defs import *


if __name__ == "__main__":
    print 'Please run the smg.py utility instead.'
    sys.exit(1)
    
# }}}

##############################################################################
##############################################################################
# {{{      Class: smg_phrase

#


### Phrase Class

class _smg_phrase:

    """A State Machine is composed of a number of phrases, which roughly
       represent portions of the input file.  One type of phrase is one
       or more lines of input C code.  Another type of phrase is a State
       Machine (class smg_state_machine) as constructed while reading
       the input file.
    """
    
    _phrase = (None, 0, [ "" ] );

    #----------------------------------------------------------------
    #
    def __init__(self, type=C_code, file='', line_num=0, phrase=None):
        self._phrase = (None, "", 0, [ "" ] );
        if phrase:
            self.set_phrase(type, file, line_num, phrase)

    #----------------------------------------------------------------
    #
    def set_phrase(self, type=C_code, file='', line_num=0, phrase="\n"):
        "Set characteristics of this phrase"
        self._phrase = (type, file, line_num, phrase)

    #----------------------------------------------------------------
    #
    def __add__(self, addition):
        "Add more of the phrase's contents to this phrase object"
        self._phrase = (self._phrase[0], self._phrase[1], self._phrase[2],
                        self._phrase[3] + addition)
        return self

    #----------------------------------------------------------------
    #
    def type(self):
        return self._phrase[0]

    def contents(self):
        return self._phrase[3]

    def line_num(self):
        return self._phrase[2]

    def filename(self):
        return self._phrase[1]
    
    #----------------------------------------------------------------
    #
    def write_C_code(self, outdesc):
        "Write this formatted phrase to the specified output descriptor."
        if check_control("Line_Directives"):
            outdesc.write('#line %d "%s"  /* %s */\n'%(self._phrase[2],
                                                       self._phrase[1],
                                                       self._phrase[0]))
        for l in self._phrase[3]:
            outdesc.write(l)   # write(self,l)

# }}}



##############################################################################
##############################################################################
# {{{     Class: smg_file

#

class smg_file:

    """Used to represent a .sm input file.  Reads and parses the file,
       returning a collection of smg_phrases that represent the input
       file.  The input file is comprised of alternating C_code and State
       Machine phrases. The ordering of the phrases is maintained for
       output purposes, although the State Machine phrases are significantly
       different between input and output.
       * There may be multiple state machines defined in a single .sm file.
    """
    
    _filename = None
    _phrases = []

    Contexts = [ 'SMG_SYNTAX_A' ]


    #----------------------------------------------------------------
    # Initialization and Validation
    #
    def __init__(self, filename=None):
        self._filename = None
        if filename: self._access(filename)
        self._phrases = []
        return

    def filename(self, filename=None):
        "Sets the filename used for input"
        if filename: self._access(filename)

    def _access(self, filename):
        "Internal function to validate access to the specified filename"
        if os.path.exists(filename):
            self._filename = filename
        else:
            raise FileNotFound(filename)

    #----------------------------------------------------------------
    # Read and process input .sm file to generate phrases
    #
    def read(self, filename=None):
        "Reads in the contents of a State Machine input file."
        if filename:
            self._filename = filename
        if not self._filename:
            raise FileNameNeeded("read")

        f = open(self._filename)
        l = f.readlines()
        f.close()

        c_phrase = None
        sm_phrase = None
        smg_phrase = None
        last_phrase_type = None
        line_num = 0
        nblanks = 0   # Used to suppress superfluous adjacent blank lines
        out_context = []

        #.............................................................
        # Semi-intelligent parsing.  Detects one of the following:
        #  1) SM comment ('##') -- discarded.
        #  2) SM out-of-context block
        #  3) SM statement
        #  4) SM code
        #  5) C code
        #
        for line in l:
            line_num = line_num + 1;

            if len(line) > 1 and line[0] == '#' and line[1] == '#':
                continue               # Strip SMG comments

            words = string.split(line)
            if len(words) == 0:
                nblanks = nblanks + 1
                if nblanks > 5: continue
            else:
                nblanks = 0

            if last_phrase_type == SM_code:
                phrase_type = SM_code
            elif last_phrase_type == P_code:
                phrase_type = P_code
            else:
                phrase_type = C_code       # default assumption

            if len(line) and len(words) and len(words[0]) and \
               line[0] == words[0][0] and words[0] in SM_Commands:
                phrase_type = SM_stmt
                if words[0] == 'SM_DEF':
                    if len(words) != 2:
                        raise Incomplete_SM_Statement("%s, line %d"%(
                            self._filename, line_num))
                    if words[1] not in self.Contexts:
                        self.Contexts.append(words[1])
                    continue
                elif words[0] == 'SM_IF':
                    if len(words) != 2:
                        raise Incomplete_SM_Statement("%s, line %d"%(
                            self._filename, line_num))
                    if words[1] not in self.Contexts:
                        out_context.append(words[1])
                    continue
                elif words[0] == 'SM_ELSE':
                    if len(words) != 2:
                        raise Incomplete_SM_Statement("%s, line %d"%(
                            self._filename, line_num))
                    if len(out_context) == 0:
                        out_context.append(words[1])
                    elif words[1] != out_context[-1]:
                        out_context.append(words[1])
                    else:
                        out_context = out_context[:-1]
                    continue
                elif words[0] == 'SM_END':
                    if len(words) != 2:
                        raise Incomplete_SM_Statement("%s, line %d"%(
                            self._filename, line_num))
                    if len(out_context) > 0:
                        if words[1] != out_context[-1]:
                            raise UnopenedContextEnd("%s @ %s:%d %s"%(
                                words[1], self._filename, line_num,
                                out_context))
                        out_context = out_context[:-1]
                    continue
                #KWQ: verify len(out_context)==0 at very end

            if len(line) and len(words) and len(words[0]) and \
               line[0] == words[0][0] and words[0] == SM_Code_Delimiters[0]:
                phrase_type = SM_code

            if len(line) and len(words) and len(words[0]) and \
               line[0] == words[0][0] and words[0] == P_Code_Delimiters[0]:
                phrase_type = P_code

            # Now that the phrase has been classified, figure out what to
            # do with it.

            if len(out_context): continue
            
            if phrase_type == C_code:
                if last_phrase_type == phrase_type:
                    c_phrase = c_phrase + line
                else:
                    if c_phrase: self._phrases.append(c_phrase)
                    c_phrase = _smg_phrase(C_code, self._filename,
                                           line_num, line)
                last_phrase_type = phrase_type
                continue
            
            if phrase_type == SM_code:
                if len(words) and words[0] == SM_Code_Delimiters[1]:
                    self._phrases.append(smg_phrase)
                    smg_phrase = None
                    last_phrase_type = None
                    continue
                if smg_phrase: smg_phrase = smg_phrase + line
                else: smg_phrase = _smg_phrase(phrase_type, self._filename,
                                               line_num, line)
                last_phrase_type = phrase_type
                continue

            if phrase_type == P_code:
                if len(words) and words[0] == P_Code_Delimiters[1]:
                    self._phrases.append(smg_phrase)
                    smg_phrase = None
                    last_phrase_type = None
                    continue
                if smg_phrase: smg_phrase = smg_phrase + line
                else: smg_phrase = _smg_phrase(phrase_type,
                                               self._filename, line_num,
                                               line)
                last_phrase_type = phrase_type
                continue
            
## Uncomment this for all SM statements in a single phrase
#            if len(words) and words[0] == SM_Commands[0]:
#                if sm_phrase: self._phrases.append(sm_phrase)
#                sm_phrase = _smg_phrase(phrase_type, line)
#            else:
#                sm_phrase = sm_phrase + line #!!!!!!!!!!!!!

## Uncomment this for one phrase per SM statement
            if c_phrase:
                self._phrases.append(c_phrase)
                c_phrase = None
            self._phrases.append(_smg_phrase(phrase_type, self._filename,
                                             line_num, line))

            last_phrase_type = phrase_type


        if last_phrase_type == C_code:
            if c_phrase: self._phrases.append(c_phrase)
        if sm_phrase: self._phrases.append(sm_phrase)
        if last_phrase_type != C_code:
            if c_phrase: self._phrases.append(c_phrase)

        if len(out_context):
            raise OpenContext('Contexts open (outer-to-inner): %s'%out_context)
            
        return self._phrases

    #----------------------------------------------------------------
    # Return collection of phrases generated from input file
    #
    def phrases(self):
        return self._phrases

# }}}

