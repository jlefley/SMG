#!/usr/bin/env python
#
# smg_defs.h - State Machine Generator Definitions
#
# This file is used to provide common definitions to the SMG Modules.

# Copyright (c) 2000-2002, Kevin Quick
# All Rights Reserved
# See the LICENSE file for more information.

# {{{ Initialization

import sys,os,string

if __name__ == "__main__":
    print 'Please run the smg.py utility instead.'
    sys.exit(1)

# }}}

# {{{ Versioning

smg_version="v1.7.4"

# }}}


# {{{ Controls

Controls = {
'Use_Enums':0,      # True for enum declarations, false for #define instead */

'Nested_Switch':0,  # True for nested switch dispatching; false for one
                    # switch statement with combined state/event cases

'Run_Indent':0,     # True to run indent on the output file
'Verbose':0,        # True to output verbose processing information
'Line_Directives':1,# True to output #line directives to .c file
'GViz_Output':"ps", # Argument to dot's -T option for output type
'Trace_Events':0,   # True to output SM_TRACE for events
'Defer_EvGen':0,    # True to defer event generation in tagged code
'Bounds_Check':0,   # True to bounds check incoming event values
'Embedded':0,       # True to generate tight, embeddable code
}

def adjust_control(control_name, control_value):
    if control_name not in Controls.keys():
        raise "Unknown Control", control_name
    Controls[control_name] = control_value;
    return Controls[control_name]

def check_control(control_name):
    return Controls[control_name]


#Contexts = []

# }}}


# {{{ Exceptions

Parse_Error             ="Error in State Machine input"
Incomplete_SM_Statement ="Incomplete State Machine statement"
No_State_For_Description="State Description does not follow State"
No_Event_For_Description="Event Description does not follow Event"
Unknown_SM_Statement    ="Invalid or Unknown State Machine directive"
FileNotFound            ="File not found"
FileNameNeeded          ="File name must be specified before"
ReadSetSMBeforeWrite    ="State Machine must be read/defined before writing"
OpenNeeded              ="Input must be opened before"
OpenAndReadNeeded       ="Input must be opened and read before"
ReadNeeded              ="Input must be read before"
ConflictingTargetStates ="Multiple Target states for the Same Event"
MultipleCodeSpecs       ="Multiple Code Segments specified for the Same Event"
UnknownCodeTag          ="Code TAG is not defined for specified tag"
DuplicateEvent          ="Event was declared multiple times"
SM_Include_File         ="Need to read sub-SM file from include directive"
UnopenedContextEnd      ="Unopened Context Ended"
OpenContext             ="Unclosed contexts (no SM_END)"
InitAlreadySpecified    ="Init state already specified"
NotSupported            ="Unsupported directive/keyword combination"
OrphanStates            ="Orphan states (no entry or exit)"
UnreachableSourceStates ="Non-INIT_STATE source state (no entries, unreachable)"


# {{{ Global Constants

Undef_Trans = "UNDEFINED_TRANSITION_RESULT"
Undef_Event_Code = "Undefined_Transition"

# for smg_figure:
SMG_FIG_CLEAN   = 'Standard'
SMG_FIG_FULL    = 'Full'
SMG_FIG_PRIMARY = 'Class 1'
SMG_FIG_EVCLEAN = 'Event-Only'

# for smg_input
### Phrase Types
C_code=" Original C code"
SM_stmt="SM"
SM_code="SC"
P_code="Promela"

# in paths, a trailing * means all (normal wildcard) and a # means
# insert -vN where N is the optional second parameter on the SM_INCL
# line.
SM_Include_Paths = [ '.',
                     '/usr/local/lib/SMG/*#',
                     '/usr/local/lib/SMG/*',
                     '/usr/local/lib/SMG',
                     '.'
                     ]

SM_Commands = [ 'SM_NAME',   # <--special: starts new State Machine
                'SM_DESC', 'SM_OBJ', 'SM_EVT', 'SM_INCL',
                'STATE', 'INIT_STATE', 'ST_DESC',
                'EVENT', 'EV_DESC',
                'TRANS', 'TRANS+', 'TRANS=',
                'SM_DEF', 'SM_IF', 'SM_ELSE', 'SM_END',
                'CODE' ]

SM_Code_Delimiters = [ 'CODE_{', 'CODE_}' ]

P_Code_Delimiters = [ 'PROMELA_{', 'PROMELA_}' ]


### Code Keyword Replacement
Code_Xlate = { "_#OBJ" : "_sm_obj",
               "_/OBJ" : "_sm_obj",
               "_#EVT" : "_sm_evt",
               "_/EVT" : "_sm_evt" }

def XL(key): return Code_Xlate[key]

def CXL(code, sm_name):
    for xlate in Code_Xlate.keys():
        code = string.replace(code, xlate, Code_Xlate[xlate])
    code = string.replace(code, "_#SM_NAME", sm_name)
    code = string.replace(code, "_/SM_NAME", sm_name)
    return code


GenFileWarning = """/*

                    ####                             ########### 
                   ######                   ####################### 
                  ########      ######################################
                  ########      ######################################
                   #######            ###############################
                    ####                             ########### 

    WARNING: This file has been automatically generated.  Any editing
             performed directly on this file will be lost if the file
             is regenerated.

             SMG %s

*/
"""%smg_version

# }}}


# {{{ Global Support Functions

def progress(phase, element):
    if check_control("Verbose"):
        phs = string.strip(phase)
        phl = len(phase)
        print '%s%s:  %s'%(('.' * (33 - phl)), phs, element)


# }}}
