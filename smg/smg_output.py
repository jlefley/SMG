#!/usr/bin/env python
#
# smg_output - Module to generate output in support of SMG parsing.
#
# This module is a subsidiary module to the primary smg.py module.  This
# module is called to generate various output to created files
#

# Copyright (c) 2000-2002, Kevin Quick
# All Rights Reserved
# See the LICENSE file for more information.

# Main interfaces:
#


# {{{ Initialization

import sys,os,string
from smg_defs import *


if __name__ == "__main__":
    print 'Please run the smg.py utility instead.'
    sys.exit(1)
    
# }}}


# {{{ gen_C_defs_hdr

def gen_C_defs_hdr(outdesc, cmntlen, sm_name, sm_info, sm_objt, sm_evtt,
                   use_enums, nested_switch, init_state):


    if init_state:
        sinit = "/* Initial state: %s */"%init_state
    else:
        sinit = """
void %(sm_name)s_State_Machine_Init(%(sm_obj_type)s _/OBJ,
                                    %(sm_name)s_state_t initial_state);
                """%{'sm_name':sm_name, 'sm_obj_type':sm_objt}

    pgmspace_include = ["", "#include <avr/pgmspace.h>"][check_control('Program_Space_Strings')]

    sdef_begin = [ """
typedef int %(sm_name)s_state_t;  /* State Type */
#define %(Undef_Trans)s 1
"""%{'sm_name':sm_name, 'Undef_Trans':Undef_Trans},
                   """
typedef enum {
    %(Undef_Trans)s = 1,
    """%{'sm_name':sm_name, 'Undef_Trans':Undef_Trans}
                   ][use_enums]



    sdef_end = [ "", """
} %(sm_name)s_state_t;  /* State Type */
"""%{'sm_name':sm_name}
                 ][use_enums]

    
    
    edef_begin = [ """
typedef int %(sm_name)s_event_t;  /* Event Type */
"""%{'sm_name':sm_name},
                   """
typedef enum {
    """ ][use_enums]



    edef_end = [ "", """
} %(sm_name)s_event_t;  /* Event Type */
"""%{'sm_name':sm_name} ][use_enums]

    

    mdefs = [ """
#define SM_S_E(S,E)  ((int)(S) + (int)(E))
    """, ""][nested_switch];

    tdefs_return_type = ["const char*", "const PROGMEM char*"][check_control('Program_Space_Strings')]

    tdefs = [ """
%(return_type)s %(sm_name)s_State_Name(%(sm_name)s_state_t state);  /* Get State Name */
%(return_type)s %(sm_name)s_State_Desc(%(sm_name)s_state_t state);  /* Get State Desc */
%(return_type)s %(sm_name)s_Event_Name(%(sm_name)s_event_t event);  /* Get Event Name */
%(return_type)s %(sm_name)s_Event_Desc(%(sm_name)s_event_t event);  /* Get Event Desc */
"""%{'sm_name':sm_name, 'return_type':tdefs_return_type}, ""][check_control('Embedded')]
           
    odict = {'sm_name':sm_name, 'hsep':('*' * cmntlen), 'sm_info':sm_info,
             'sm_obj_type':sm_objt, 'sm_evt_type':sm_evtt,
             'pgmspace_include':pgmspace_include,
             'state_def_begin':sdef_begin, 'state_def_end':sdef_end,
             'event_def_begin':edef_begin, 'event_def_end':edef_end,
             'macro_defs':mdefs, 'tdefs':tdefs, 'sinit':sinit}

    
    outdesc.write("""
/**%(hsep)s
 **
 ** Include file definitions
 **
%(sm_info)s
 **/

#ifndef _%(sm_name)s_SM_DEFS_
#define _%(sm_name)s_SM_DEFS_

%(pgmspace_include)s

%(state_def_begin)s
<state_defs>
%(state_def_end)s



%(event_def_begin)s
<event_defs>
%(event_def_end)s


%(macro_defs)s


<entry_defs>


%(sinit)s
%(tdefs)s

void %(sm_name)s_State_Machine_Error( %(sm_obj_type)s _/OBJ,
                                      %(sm_evt_type)s _/EVT,
                                      int err_id,
                                      const char *errtext,
                                      ... );
                                      

void %(sm_name)s_State_Machine_Event( %(sm_obj_type)s _sm_obj,
                                      %(sm_evt_type)s _sm_evt,
                                      %(sm_name)s_event_t event_code );


#ifndef SM_TRACE
#define SM_TRACE_INIT(Obj, Evt, SM_Name, InitState) \\
        printf("** SM %%s 0x%%x: State %%d-%%s  INIT\\n", \\
               #SM_Name, Obj, InitState, SM_Name##_State_Name(InitState));
#define SM_TRACE_EVENT(Obj, Evt, SM_Name, Event) \\
        printf("** SM %%s 0x%%x: State %%d=%%s -- Event %%d=%%s\\n", \\
               #SM_Name, Obj, \\
               Obj->sm_state, SM_Name##_State_Name(Obj->sm_state), \\
               Event, SM_Name##_Event_Name(Event));
#define SM_TRACE_POST_EVENT(Obj, Evt, SM_Name, Event) \\
        printf("** SM %%s 0x%%x: State %%d=%%s -- Event %%d=%%s\\n", \\
               #SM_Name, Obj, \\
               Obj->sm_state, SM_Name##_State_Name(Obj->sm_state), \\
               Event, SM_Name##_Event_Name(Event));
#define SM_TRACE_EXP_EV(Obj, Evt, SM_Name, Event) \\
        printf("** SM %%s 0x%%x: State %%d=%%s ++ Event %%d=%%s\\n", \\
               #SM_Name, Obj, Obj->sm_state, \\
               SM_Name##_State_Name(Obj->sm_state), \\
               Event, SM_Name##_Event_Name(Event));
#endif



#endif   /* _%(sm_name)s_SM_DEFS_ */
               
"""%odict)

# }}}

# {{{ write_sm_error

# Generates code to notify of a state machine error.
# Make sure the relationship between the Error ID and the error text and
# arguments remains constant; other tools or specific uses depend on this
# layout being static.

sm_errs = [
    '0, "unused");\n',
    '1, "Undefined State Transition (State %%d=%%s: %%s), (Event %%d=%%s: %%s)\\n", %(_/OBJ)s->sm_state, %(sm_name)s_State_Name(%(_/OBJ)s->sm_state), %(sm_name)s_State_Desc(%(_/OBJ)s->sm_state), event_code, %(sm_name)s_Event_Name(event_code), %(sm_name)s_Event_Desc(event_code));\n',
    '2, "Invalid STATE!! (%%d=%%s: %%s)\\n", %(_/OBJ)s->sm_state, %(sm_name)s_State_Name(%(_/OBJ)s->sm_state), %(sm_name)s_State_Desc(%(_/OBJ)s->sm_state));\n',
    '3, "Invalid STATE/EVENT!! (State %%d=%%s: %%s) (Event %%d=%%s: %%s)\\n", %(_/OBJ)s->sm_state, %(sm_name)s_State_Name(%(_/OBJ)s->sm_state), %(sm_name)s_State_Desc(%(_/OBJ)s->sm_state), event_code, %(sm_name)s_Event_Name(event_code), %(sm_name)s_Event_Desc(event_code));\n'
    ]
    
def write_sm_error(outf, err_id, sm_name):
    outf.write('%s_State_Machine_Error(%s, %s, '%(sm_name,
                                                XL("_/OBJ"), XL("_/EVT")))
    if check_control("Embedded") or check_control('Program_Space_Strings'):
        etext = '%d, "");\n'%err_id
    else:
        etext = sm_errs[err_id]%{'sm_name':sm_name,
                                "_/OBJ":XL("_/OBJ"),
                                "_/EVT":XL("_/EVT")} 
    outf.write(etext)
    

# }}}
