#!/usr/bin/env python
#
# smg - State Machine Generator
#
# This utility is used to compile SMG syntax statements into C code.

# Copyright (c) 2000-2007, Kevin Quick
# All Rights Reserved
# See the LICENSE file for more information.

# {{{ Initialization

import sys,os,string,StringIO, smg_defs
from strblock import para
from smg_defs import *
from smg_figure import smg_figure
from smg_input import smg_file
from smg_output import *

# }}}

# {{{ Global Variables


# }}}





##############################################################################
##############################################################################
# {{{      Class: smg_state

#
class smg_state:

    """Object which represents an single state within a state machine."""

    #----------------------------------------------------------------
    # Initialization and Validation
    #
    def __init__(self, name, desc=''):
        self._name = name
        self._desc = desc
        self._role = 'Processing'
        self._numv = -1
        self.events = {}
        self.expected_events = []

    def set_desc(self, desc):
        if len(self._desc):
            self._desc = '%s %s'%(self._desc, desc)
        else:
            self._desc = desc

    def name(self):
        return self._name

    def desc(self):
        return self._desc

    def role(self, new_role = None):
        if new_role:
            self._role = new_role
        return self._role   # Processing, Source, Terminal, or Orphan

    def numeric_value(self, new_val=None):
        if new_val or new_val == 0:
            self._numv = new_val
        return self._numv

    
    #----------------------------------------------------------------
    # Evaluation Information
    #
    def event(self, event_name, new_state=None, pre_group_code=None,
              pre_solo_code=None, post_group_code=None, post_solo_code=None,
              Default_spec=0, Expected=0):
        if Expected: self.expected_events.append(event_name)
        if event_name in self.events.keys() and \
           self.events[event_name][0] != Undef_Trans and \
           not self.events[event_name][5]:
            if (new_state and self.events[event_name][0] and
                new_state != self.events[event_name][0]):
                raise ConflictingTargetStates('State %s, Event %s\n' \
                      '\t\tExisting\tNew\n' \
                      'Tgt State\t%s\t%s\n' \
                      'Pre Grp Code\t%s\t%s\n' \
                      'Pre Solo Code\t%s\t%s\n' \
                      'Post Grp Code\t%s\t%s\n' \
                      'Post Solo Code\t%s\t%s\n' \
                      'Default\t%s\t%s\n'%(
                    self._name, event_name,
                    self.events[event_name][0], new_state,
                    self.events[event_name][1], pre_group_code,
                    self.events[event_name][2], pre_solo_code,
                    self.events[event_name][3], post_group_code,
                    self.events[event_name][4], pre_solo_code,
                    self.events[event_name][5], Default_spec
                    ))
            if pre_solo_code and self.events[event_name][2]:
                raise MultipleCodeSpecs(\
                      'State %s, Event %s, Pre-state code'%(
                    self._name, event_name))
            if post_solo_code and self.events[event_name][4]:
                raise MultipleCodeSpecs(\
                      'State %s, Event %s, Post-state code'%(
                    self._name, event_name))
            if Default_spec:
                discard4,\
                            discard1,\
                            pre_solo_code,\
                            discard2,\
                            post_solo_code,\
                            discard3 = self.events[event_name]
        if event_name in self.events.keys():
            discard1,\
                       pregroupcode,\
                       discard2,\
                       postgroupcode,\
                       discard3,\
                       discard4 = self.events[event_name]
            if pre_group_code and pre_group_code not in pregroupcode:
                pregroupcode.append(pre_group_code)
            if post_group_code and post_group_code not in postgroupcode:
                postgroupcode.append(post_group_code)
            pre_group_code = pregroupcode
            post_group_code = postgroupcode
        
        if type(pre_group_code) != type([]):
            pre_group_code = [ pre_group_code ]
        if type(post_group_code) != type([]):
            post_group_code = [ post_group_code ]
        self.events[event_name] = (new_state,
                                   pre_group_code,
                                   pre_solo_code,
                                   post_group_code,
                                   post_solo_code,
                                   Default_spec)

    #----------------------------------------------------------------
    # Output C code
    #
    def write_C_defs(self, outdesc, use_enums):
        "Write definition for this state to the output descriptor."
        cmntlen=70
        if use_enums:
            defline="    %s  \t= %4d,    "%(self._name, self._numv)
        else:
            defline="#define %s  \t%4d   "%(self._name, self._numv)
        if len(self._desc):
            dline = '%s /* '%string.expandtabs(defline)
            outdesc.write(para('%s */'%self._desc,
                               dline,
                               ' ' * len(dline),
                               70))
        else:
            outdesc.write("%s\n"%defline)

    def _write_C_event(self, outdesc, sm_name, event,
                       code2_indent, code_library):
        "Writes code for an specified event"

        (new_state,
         pre_group_code,
         pre_solo_code,
         post_group_code,
         post_solo_code, defspec) = self.events[event]

        pfx = []
        sfx = []
        ecode = []
        if len(pre_group_code):
            for tag in pre_group_code:
                if not tag: continue;
                if tag == '--': continue
                # Group should be otherwise grouped?
                ecode.append("%s/**< Group: %s */\n"%(code2_indent, tag))
                ecode.append(
                    code_library[tag].tagged_C_code(sm_name,
                                                    self.events.keys()))

        if pre_solo_code and len(pre_solo_code) and pre_solo_code != "--":
            ecode.append("%s/**< %s */\n"%(code2_indent, pre_solo_code))
            ecode.append(
                code_library[pre_solo_code].tagged_C_code(sm_name,
                                                          self.events.keys()))

        if new_state and \
           len(new_state) and \
           new_state != "--" and \
           type(new_state) != type([]):
            ecode.append("%s%s->sm_state = %s;\n"%(code2_indent,
                                                    XL("_/OBJ"),
                                                    new_state))

        if post_solo_code and \
           len(post_solo_code) and \
           post_solo_code != "--":
            ecode.append("%s/**> %s */\n"%(code2_indent, post_solo_code));
            ecode.append(
                code_library[post_solo_code].tagged_C_code(sm_name,
                                                           self.events.keys()))

        if len(post_group_code):
            for tag in post_group_code:
                if not tag: continue;
                if tag == '--': continue
                # Group should be otherwise grouped?
                ecode.append("%s/**> Group: %s */\n"%(code2_indent, tag))
                ecode.append(
                    code_library[tag].tagged_C_code(sm_name,
                                                    self.events.keys()))

        outdesc.write('%s{\n'%code2_indent)
        ## Write prefixes
        for code in ecode:
            if type(code) == type(()):
                outdesc.write(code[0])
        ## Write tagged code sections
        for code in ecode:
            if type(code) == type(()):
                outdesc.write(para(code[1], code2_indent, code2_indent, 77))
            else:
                outdesc.write(para(code, code2_indent, code2_indent, 77))
        ## Write suffixes
        for code in ecode:
            if type(code) == type(()):
                outdesc.write(code[2])
        outdesc.write('%s}\n'%code2_indent)


    def write_C_expected(self, outdesc, sm_name, event, code_library):
        "Writes C code for the event if expected for this state."
        code_indent = "    "
        if event in self.expected_events:
            outdesc.write("%sif (%s->sm_state == %s) {\n"%(
                code_indent, XL("_/OBJ"), self._name))

            if check_control("Trace_Events"):
                outdesc.write(
                    '    SM_TRACE_EXP_EV(%s, %s, %s, %s);\n\n'%(
                    XL("_/OBJ"), XL("_/EVT"), sm_name, event))

            self._write_C_event(outdesc, sm_name, event,
                                "%s        "%code_indent, code_library)
            outdesc.write("%s        return;\n%s}\n\n"%(
                code_indent, code_indent))
            

    def write_C_code(self, outdesc, sm_name, code_library):
        "Writes C code for the switch statement handling this state."
        code_indent = "       "

        if check_control("Nested_Switch"):
            case='      case %s:    '%self._name
            if len(self._desc):
                outdesc.write(para('%s */'%self._desc,
                                   '%s /* '%case,
                                   ' ' * (len(case)+4),
                                   70))
            else:
                outdesc.write('%s\n'%case)

            outdesc.write("%sswitch (event_code) {\n"%code_indent);
            code2_indent = "%s        "%code_indent
        else:
            code_indent = '%s      '%code_indent
            code2_indent = code_indent

        did_events = []
        
        for event in self.events.keys():

            if event in did_events: continue
            did_events.append(event)
            
            for other in self.events.keys():
                if other in did_events: continue
                if self.events[event] == self.events[other]:
                    if check_control("Nested_Switch"):
                        outdesc.write("%s    case %s:\n"%(code_indent, other))
                    else:
                        outdesc.write("        case SM_S_E(%s, %s):\n"%(
                            self._name, other))
                    did_events.append(other)
                    
            if check_control("Nested_Switch"):
                outdesc.write("%s    case %s:\n"%(code_indent, event))
            else:
                outdesc.write("        case SM_S_E(%s, %s):\n"%(self._name,
                                                                event))

            self._write_C_event(outdesc, sm_name, event,
                                code2_indent, code_library)
        
            outdesc.write("%sbreak;\n"%code2_indent)

        if check_control("Nested_Switch"):
            outdesc.write("%s}\n"%code_indent)
            outdesc.write("%sbreak;\n\n"%code_indent)
            

    def write_P_code(self, outdesc, sm, event, enames, code_library):
        "Writes Promela code for handling this state."
        evinfo = self.event_info(event.name())
        pretags,ename,posttags,ev_exp = evinfo[0]
        next_states = self.next_states(event.name())

        for tag in pretags:
            try:
                outdesc.write("""
          /** < %(tag)s **/
          %(code)s"""%{'tag':tag,
                'code':code_library[tag].tagged_P_code(
                sm, enames, code_library, self)})
            except KeyError:
                pass    # OK to not have Promela code for tag

        if len(next_states) == 0:
            outdesc.write("     pass;   /*no state change */\n")
        elif len(next_states) == 1:
            outdesc.write("     state = %s;\n"%next_states[0])
            if check_control("Trace_Events"):
                outdesc.write('     printf("MSC: state = %s\\n");\n'%next_states[0])
        else:
            outdesc.write("                if\n")
            for nxt in next_states:
                outdesc.write("                :: pass -> state = %s;\n"%nxt)
                if check_control("Trace_Events"):
                    outdesc.write('                           printf("MSC: state = %s\\n");\\n'%nxt)
            outdesc.write("                fi\n")

        for tag in posttags:
            try:
                outdesc.write("""
          /** > %(tag)s **/
          %(code)s"""%{'tag':tag,
                'code':code_library[tag].tagged_P_code(
                sm, enames, code_library, sm._states[next_states[0]])})
            except KeyError:
                pass    # OK to not have Promela code for tag


    def event_names(self):
        return self.events.keys()

    def event_info(self, event_name=None):
        """Returns an array of tuples.  Each tuple represents a possible
           event transition from the current state.  Each tuple is has
           three elements:  ( <list of pre-code stmts>,
                              <name of event>,
                              <list of post-code stmts>,
                              <boolean-true-if-expected> )"""
        ra = []

        if event_name:
            enames = [ event_name ]
        else:
            enames = self.events.keys()
            
        for event in enames:

            (new_states,
             pre_group_code,
             pre_solo_code,
             post_group_code,
             post_solo_code, defspec) = self.events[event]

            lbl_pre_words = []
            lbl_post_words = []

            for words, taglist in [
                (lbl_pre_words, pre_group_code),
                (lbl_pre_words, [ pre_solo_code ]),
                (lbl_post_words, post_group_code),
                (lbl_post_words, [ post_solo_code ]) ]:
                for tag in taglist:
                    if not tag: continue
                    if tag == '--': continue
                    if tag == [None]: continue
                    words.append(tag)
                
            ra.append( (lbl_pre_words, event, lbl_post_words,
                        event in self.expected_events) )

        return ra
    

    def next_states(self, event_name):
        """Returns the names of the target states for the occurrence of this
           event as an array.  Typically there will be just one entry in the
           returned array."""
        ns = self.events[event_name][0]
        if ns == '--':
            ns = self._name
        if type(ns) != type([]):
            ns = [ ns ]
        return ns

# }}}

##############################################################################
##############################################################################
# {{{      Class: smg_event

#
class smg_event:

    """Object which represents an single event within a state machine."""

    #----------------------------------------------------------------
    # Initialization and Validation
    #
    def __init__(self, name, entry=None, prep=None, desc=''):
        self._name = name
        self._desc = desc
        self._numv = -1
        self._entry_code_tag = entry
        self._prep_code_tag = prep

    def set_desc(self, desc):
        if len(self._desc):
            self._desc = '%s %s'%(self._desc, desc)
        else:
            self._desc = desc

    def desc(self, desc=None):
        if desc and len(desc):
            self._desc = desc
        return self._desc

    def entry(self, entry=None):
        if entry and len(entry):
            self._entry_code_tag = entry
        return self._entry_code_tag

    def prep(self, prep=None):
        if prep and len(prep):
            self._prep_code_tag = prep
        return self._prep_code_tag

    def name(self, name=None):
        if name and len(name):
            self._name = name
        return self._name

    def numeric_value(self, new_val=None):
        if new_val or new_val == 0:
            self._numv = new_val
        return self._numv


    #----------------------------------------------------------------
    # Output C code
    #
    def write_C_defs(self, outdesc, use_enums):
        "Write definition for this event to the output descriptor."
        cmntlen=70
        if use_enums:
            defline="    %s  \t= %4d,    "%(self._name, self._numv)
        else:
            defline="#define %s  \t%4d   "%(self._name, self._numv)
        if len(self._desc):
            dline = '%s /* '%string.expandtabs(defline)
            outdesc.write(para('%s */'%self._desc,
                               dline,
                               ' ' * len(dline),
                               70))
        else:
            outdesc.write("%s\n"%defline)

# }}}

##############################################################################
##############################################################################
# {{{     Class: smg_code

#
class smg_code:

    """Object which represents a state machine tagged portion of code"""

    #----------------------------------------------------------------
    # Initialization and Validation
    #
    def __init__(self, tag, filename, linenum, code):
        self._tag = tag
        self._linenum = linenum
        self._filename = filename
        self._code = [ code ]

    def __add__(self, more_code):
        self._code.append(more_code)
        return self

    def tag(self, newtag=None):
        if newtag:
            self._tag = tag
        return tag

    def code(self, code=None):
        if code:
            self._code = [ code ]
        return string.join(self._code, '\n')

    def tagged_C_code(self, sm_name, event_names=[]):
        pfx = ''
        sfx = ''
        pfxi = 1
        if check_control("Line_Directives"):
            rstr = '\n#line %d "%s - %s"\n%s'%(self._linenum+1, self._filename,
                                               self._tag,
                                               string.join(self._code, '\n'))
        else:
            rstr = '\n%s'%string.join(self._code, '\n')
        # Make sure we match longest first...
        enames = event_names
        enames.sort()
        enames.reverse()
        # Look for event substitutions
        for event in enames:
            for sid in [ "_#", "_/" ] :
                if string.find(rstr, "%s%s"%(sid,event)) != -1:
                    if check_control("Defer_EvGen"):
                        pfx = '%s    %s_event_t _deferred_ev%d = %s;\n' \
                              '    int _gen_ev%d = 0;\n'%(
                            pfx, sm_name, pfxi, event, pfxi)
                        r = string.find(rstr, "%s%s"%(sid,event))
                        p = 0
                        nstr = ''
                        while r != -1:
                            nstr = '%s%s_gen_ev%d++'%(nstr, rstr[p:r], pfxi)
                            p = r + len('%s%s'%(sid,event))
                            r = string.find(rstr, "%s%s"%(sid,event), p)
                        rstr = '%s%s'%(nstr, rstr[p:])
                        pfxi = pfxi + 1
                    else:
                        rstr = string.replace(rstr, "%s%s"%(sid,event),
                                             "%s_State_Machine_Event(_/OBJ, _/EVT, %s)"%(
                            sm_name, event))
        for indx in range(1,pfxi):
            sfx='%s\n    while (_gen_ev%d-- > 0)\n' \
                 '        %s_State_Machine_Event(%s, %s, _deferred_ev%d);\n'%(
                sfx, indx, sm_name, XL("_/OBJ"),
                XL("_/EVT"), indx)
        rstr = CXL(rstr, sm_name)
        rstr = string.replace(rstr, "_#", "_sm_obj->sm_state = ")
        rstr = string.replace(rstr, "_/", "_sm_obj->sm_state = ")
        if check_control("Defer_EvGen") and pfxi > 1:
            return (pfx, rstr, sfx)
        return rstr

#kwq: might be targeted to a different state machine...

    def tagged_P_code(self, sm, event_names=[], code_library={}, state=None):
        pfx = ''
        sfx = ''
        pfxi = 1
        rstr = '\n%s'%string.join(self._code, '\n')
        # Make sure we match longest first...
        enames = event_names
        enames.sort()
        enames.reverse()
        # Look for event substitutions
        for event in enames:
            for sid in [ "_#", "_/" ] :
                if string.find(rstr, "%s%s"%(sid,event)) != -1:
                    if check_control("Defer_EvGen"):
                        print 'No handling yet for deferred events in Promela'
                    else:
                        if state:
                            subh = StringIO.StringIO()
                            state.write_P_code(subh,
                                               sm,
                                               sm.event(event),
                                               event_names,
                                               code_library)
                            subhandling = subh.getvalue()
                            rstr = string.replace(
                                rstr, "%s%s"%(sid,event),
                                #kwq: _/OBJ: sm_name instance!
                                """
/* -------------------------------------------------------------------------
 * Generate handing for cascaded sub-event %(event)s in state %(state_name)s
 * Immediate handling as if: in_events!SM_EVENT(%(event)s) in %(state_name)s
  ........................................................................*/
%(subhandling)s
/* .........................................................................
 * End of cascaded sub-event %(event)s in state %(state_name)s
 * -----------------------------------------------------------------------*/
"""%{
                                'sm_name':sm.name(), 'event':event,
                                'state_name':state.name(),
                                'subhandling':subhandling
                                })
                        else:
                            raise NotSupported('%(event)s cascaded sub-event for any state')
                            rstr = string.replace(
                                rstr, "%s%s"%(sid,event),
                                #kwq: _/OBJ: sm_name instance!
                                """
/*KWQ: generate handing for event %(event)s for any state */
in_events!SM_EVENT(%(event)s)"""%{
                                'sm_name':sm.name(), 'event':event})
        rstr = CXL(rstr, sm.name()) #kwq? valid promela?
        rstr = string.replace(rstr, "_#", "state = ")  #kwq? valid promela?
        rstr = string.replace(rstr, "_/", "state = ")  #kwq? valid promela?
        return rstr
    

    identifier_chars = '%s%s_'%(string.letters, string.digits)
    
    def target_states(self, valid_states):
        """Scans the code segment for any _#XXX or _/XXX specifications which
           match the list of valid states.  These specifications are to
           be replaced by actual code setting to that target state.  This scan
           simply returns a unique-entry array of destination STATE values
           found in the code."""
        rlist = []
        for code in self._code:
            code = CXL(code, "GENERIC STATE MACHINE")
            for sid in [ "_#", "_/" ]:
                directive_loc = string.find(code, sid)
                while directive_loc != -1:
                    end_direct = directive_loc + 2
                    while code[end_direct] in self.identifier_chars:
                        end_direct = end_direct + 1
                    dspec = code[directive_loc+2:end_direct]
                    if (dspec not in rlist) and \
                       (dspec in valid_states):
                        rlist.append(code[directive_loc+2:end_direct])
                    directive_loc = string.find(code[end_direct:], sid)
        return rlist

# }}}


##############################################################################
##############################################################################
# {{{      Class: smg_transition

#
class smg_transition:

    """Object which represents an single transition within a state machine."""

    #----------------------------------------------------------------
    # Initialization and Validation
    #
    def __init__(self, trans_type, from_state, to_state, event,
                 pre_code_tag='', post_code_tag=''):
        self._trans_type = trans_type
        if event == '*':
            raise NotSupported("event wildcard for TRANS statement")
        self._trans = (from_state, event, to_state)
        self._pre_code_tag = pre_code_tag
        self._post_code_tag = post_code_tag

    def from_state(self, state=None):
        if (state):
            self._trans = (state, self._trans[1], self._trans[2])
        return self._trans[0]
    
    def to_state(self, state=None):
        if (state):
            self._trans = (self._trans[0], self._trans[1], state)
        return self._trans[2]
    
    def event(self, evt=None):
        if (evt):
            self._trans = (self._trans[0], evt, self._trans[2])
        return self._trans[1]

    def pre_code_tag(self, tag=None):
        if (tag):
            self._pre_code_tag = tag
        return self._pre_code_tag

    def post_code_tag(self, tag=None):
        if (tag):
            self._post_code_tag = tag
        return self._post_code_tag

    def type(self, new_type=None):
        if (new_type):
            self._trans_type = new_type
        return self._trans_type

# }}}

##############################################################################
##############################################################################
# {{{     Class: smg_state_machine

#
class smg_state_machine:

    """Object which represents an actual (single) state machine."""

    def __init__(self, name,
                 desc="Generic State Machine",
                 obj_type="void *",
                 evt_type="void *"):
        self._name = name
        self._desc = desc
        self._objt = obj_type
        self._evtt = evt_type
        self._states = {}
        self._events = []
        self._trans  = []
        self._codes  = {}
        self._pcodes = {}
        self._status = ['Incomplete', 'Unevaluated']
        self._events_names = []
        self._last_state = None
        self.init_state = None

    def name(self):
        return self._name
    
    def __str__(self):
        return "State Machine '%s': %s\n\tOBJ Type: %s\n\tEVT Type: %s\n"%(
            self._name, self._desc, self._objt, self._evtt)

    def description(self):
        return self._desc

    def status(self, clear=None, set=None):
        if set:
            new_status = set
        else:
            new_status = []
        for sts in self._status:
            if not clear or sts not in clear:
                new_status.append(sts)
        self._status = new_status
        rsts = self._status[0]
        for sts in self._status[1:]:
            rsts = '%s %s'%(rsts,sts)
        return rsts

    def info(self, cmntlen=76):
        rs = []
        rs.append("%s\n"%('-' * cmntlen))
        rs.append("## State Machine | %s\n"%self._name)
        rs.append("##\n");
        rs.append(para(self._desc,
                       "## Description   | ",
                       "##               | ", cmntlen))
        rs.append("##\n");
        rs.append("##     OBJ Type  | %s\n"%self._objt)
        rs.append("##     EVT Type  | %s\n"%self._evtt)
        rs.append("##   Num States  | %d\n"%len(self._states))
        rs.append("##   Num Events  | %d\n"%len(self._events))
        rs.append("##    Num Trans  | %d\n"%len(self._trans))
        rs.append("## Num Codesegs  | %d\n"%len(self._codes))
        rs.append(para(string.join(self._status),
                           "##   Definition  | ",
                           "##               | ", cmntlen))
        rs.append("%s\n"%('-' * cmntlen))
        return string.join(rs, '')

    def summary(self):
        return "States: %d\nEvents: %d\nTransitions: %d\n%s"%(
            len(self._states), len(self._events), len(self._trans),
            self._status)

    def state_list(self):               #kwq temporary for smg_figure
        return self._states.values()    #kwq temporary for smg_figure

    def event(self, event_name):
        for event in self._events:
            if event.name() == event_name:
                return event
            
    #----------------------------------------------------------------
    #
    def __add__(self, addition):
        """Add another statement to this state machine.  The 'addition' is an
           array of words representing the statement to be added."""
        words = string.split(addition.contents())
        filename = addition.filename()
        if len(words) < 2:
            raise Incomplete_SM_Statement("%s, line %d"%(filename,
                                                          addition.line_num()))
        if words[0] == 'SM_DESC':
            self._desc = "%s\n%s"%(self._desc, string.join(words[1:]))
        elif words[0] == 'SM_OBJ':
            self._objt = string.join(words[1:])
        elif words[0] == 'SM_EVT':
            self._evtt = string.join(words[1:])
        elif words[0] == 'SM_INCL':
            if len(words) > 2:
                raise SM_Include_File((words[1], words[2]))
            else:
                raise SM_Include_File(words[1])
        elif words[0] == 'STATE':
            sdesc = ''
            if len(words) > 2: sdesc = string.join(words[2:])
            if words[1] not in self._states.keys():
                self._states[words[1]] = smg_state(words[1], sdesc)
            elif len(sdesc):
                self._states[words[1]].set_desc(sdesc)
            self._last_state = words[1]
        elif words[0] == 'INIT_STATE':
            if self.init_state and len(self.init_state):
                raise InitAlreadySpecified(words[1])
            sdesc = ''
            if len(words) > 2: sdesc = string.join(words[2:])
            if words[1] not in self._states.keys():
                self._states[words[1]] = smg_state(words[1], sdesc)
            elif len(sdesc):
                self._states[words[1]].set_desc(sdesc)
            self._last_state = words[1]
            self.init_state = words[1]
        elif words[0] == 'EVENT':
            edesc = ''
            entry = None
            prep  = None
            if len(words) > 2: entry = words[2]
            if len(words) > 3: prep  = words[3]
            if len(words) > 4: edesc = string.join(words[4:])
            if words[1] not in self._events_names:
                self._events_names.append(words[1])
                self._events.append(smg_event(words[1], entry, prep, edesc))
            else:
                raise DuplicateEvent(\
                      "%s, line %d, Event %s"%(filename,
                                               addition.line_num(),
                                               words[1]))
        elif words[0] == 'ST_DESC':
            if len(self._states):
                self._states[
                    self._last_state].set_desc(string.join(words[1:]))
            else:
                raise No_State_For_Description(\
                      "%s, line %d"%(filename, addition.line_num()))
        elif words[0] == 'EV_DESC':
            if len(self._events):
                self._events[-1].set_desc(string.join(words[1:]))
            else:
                raise No_Event_For_Description(\
                      "%s, line %d"%(filename, addition.line_num()))
        elif words[0] in ('TRANS', 'TRANS+', 'TRANS='):
            if len(words) < 4:
                raise Incomplete_SM_Statement(\
                      "%s, line %d"%(filename, addition.line_num()))
            pre_code = None
            post_code = None
            if len(words) == 5:
                post_code = words[4]
            elif len(words) == 6:
                pre_code = words[4]
                post_code = words[5]
            try:
                self._trans.append(smg_transition(words[0],
                                                  words[1],
                                                  words[3],
                                                  words[2],
                                                  pre_code, post_code))
            except NotSupported, why:
                raise NotSupported('%s, line %d -- %s'%(filename,
                                                         addition.line_num(),
                                                         why))
        elif words[0] == 'CODE':
            if len(words) < 3:
                raise Incomplete_SM_Statement(\
                      "%s, line %d"%(filename, addition.line_num()))
            if words[1] in self._codes.keys():
                self._codes[words[1]] = (self._codes[words[1]] +
                                         string.join(words[2:]))
            else:
                self._codes[words[1]] = smg_code(words[1], filename,
                                                 addition.line_num() - 1,
                                                 string.join(words[2:]))
        elif words[0] == SM_Code_Delimiters[0]:
            lines = string.split(addition.contents(), '\n')
            if len(lines) < 2:
                raise Incomplete_SM_Statement(\
                      "%s, line %d"%(filename, addition.line_num()))
            lspacecnt = len(lines[1]) - len(string.lstrip(lines[1]))
            lspace = ' ' * lspacecnt
            if words[1] in self._codes.keys():
                print '!!!!!!!!! CODE %s ALREADY EXISTED !!!!!!!!'%words[1]
                self._codes[words[1]] = (self._codes[words[1]] +
                                         lines[1][lspacecnt:])
            else:
                self._codes[words[1]] = smg_code(words[1], filename,
                                                 addition.line_num() - 1,
                                                 lines[1][lspacecnt:])
            for line in lines[2:]:
                ls = lspacecnt
                if line[:ls] != lspace: ls = 0
                self._codes[words[1]] = self._codes[words[1]] + line[ls:]

        elif words[0] == P_Code_Delimiters[0]:
            lines = string.split(addition.contents(), '\n')
            if len(lines) < 2:
                raise Incomplete_SM_Statement(\
                      "%s, line %d"%(filename, addition.line_num()))
            self._pcodes[words[1]] = smg_code(words[1], filename,
                                              addition.line_num(),
                                              string.join(lines[1:], '\n'))

        else:
            raise Unknown_SM_Statement("%s, line %d"%(filename,
                                                       addition.line_num()))
        return self



    #----------------------------------------------------------------
    #
    def evaluate(self):
        self.status(['Incomplete', 'Unevaluated'],
                    ['Complete', 'Processing' ])

        try:
            # First make sure we have a complete list of states and events
            for trans in self._trans:
                for state in [ trans.from_state(), trans.to_state() ]:
                    if state == '*': continue
                    if state == '--': continue
                    if state not in self._states.keys():
                        self._states[state] = smg_state(state)
                event = trans.event()
                if event not in self._events_names:
                    self._events_names.append(event)
                    self._events.append(smg_event(event))

            for event in self._events:
                for ctag in (event.entry(), event.prep()):
                    if ctag and len(ctag) and ctag != '--':
                        if ctag not in self._codes.keys():
                            raise UnknownCodeTag(\
                                  'Entry "%s" for event %s'%(ctag,
                                                             event.name()))

            for trans in self._trans:
                for code in (trans.pre_code_tag(), trans.post_code_tag()):
                    if code and len(code) and code != '--':
                        if code not in self._codes.keys():
                            raise UnknownCodeTag(
                                  """Code tag %s for trans from state %s """\
                                  """to state %s via event %s"""%(
                                code, trans.from_state(), trans.to_state(),
                                trans.event()))

            # Now, preload the UNDEFINED TRANSITION target state as the default
            for state in self._states.values():
                for event in self._events_names:
                    state.event(event, Undef_Trans,
                                None, Undef_Event_Code)
            errcall = StringIO.StringIO()
            write_sm_error(errcall, 1, self._name)
            self._codes[Undef_Event_Code] = smg_code(
                Undef_Event_Code, "SMG MANAGEMENT CODE", 1, errcall.getvalue())

            # And now load all the defined transitions into the states
            for trans in self._trans:
                pre_group_code = None
                pre_solo_code = None
                post_group_code = None
                post_solo_code = None
                if trans.type() in ('TRANS', 'TRANS='):
                    pre_solo_code = trans.pre_code_tag()
                    post_solo_code = trans.post_code_tag()
                elif trans.type() == 'TRANS+':
                    pre_group_code = trans.pre_code_tag()
                    post_group_code = trans.post_code_tag()
                fstates = trans.from_state()
                if fstates == '*':
                    fstates = self._states.keys()
                else:
                    fstates = [ trans.from_state() ]
                for fstate in fstates:
                    tstates = trans.to_state()
                    if tstates == '*':
                        tstates = []
                        for code in (trans.pre_code_tag(),
                                     trans.post_code_tag()):
                            if not code: continue
                            if code not in self._codes.keys():
                                raise UnknownCodeTag(code)
                            c_tstates = self._codes[code].target_states(
                                self._states.keys())
                            if len(c_tstates):
                                tstates = tstates + c_tstates
                                                                 
                    self._states[fstate].event(trans.event(),
                                               tstates,##s
                                               pre_group_code,
                                               pre_solo_code,
                                               post_group_code,
                                               post_solo_code,
                                               trans.from_state() == '*',
                                               trans.type() == 'TRANS=')
            

            ## Now validate the role for each state in the state machine

            entry_counts = {}

            for state in self._states.values():
                state.role('Terminal')
                for ev in state.event_info():
                    for tgt_state in state.next_states(ev[1]):
                        if not entry_counts.has_key(tgt_state):
                            entry_counts[tgt_state] = 0
                        if tgt_state != state.name():
                            entry_counts[tgt_state] = entry_counts[tgt_state]+1
                        if tgt_state != state.name():
                            state.role('Processing')

            for state in self._states.values():
                if not entry_counts.has_key(state.name()) or \
                   entry_counts[state.name()] == 0 or \
                   (self.init_state and self.init_state == state.name()):
                    if state.role() == 'Terminal':
                        state.role('Orphan')
                    else:
                        state.role('Source')

            orphans = filter(lambda st: st.role() == 'Orphan',
                             self._states.values())
            if len(orphans):
                raise OrphanStates(map(lambda st: st.name(), orphans))

            if self.init_state:
                sources = filter(lambda st,init_state = self.init_state:
                                 st.role()=='Source' and st.name()!=init_state,
                                 self._states.values())
                if len(sources):
                    raise UnreachableSourceStates(map(lambda st: st.name(),
                                                       sources))
        

            # Assign values to the events and states
            # Since events are typically external events, we support the
            # "Bounds_Check" control which tells us to validate the event
            # values to be sure they are legal.  To do this, it's convenient
            # to have all event values sequentially enumerated, but we also
            # have support for some special states.
            #
            # The following code generates state and event values that
            # look like one of the following (selected by the "Nested_Switch"
            # control):
            #
            # All control values:
            #      0 == Init_State (if any)
            #      1 == INVALID_STATE_TRANSITION (if any)
            # No Nested_Switch, no Bounds_Check:
            #      2..n == Event values
            #      m*B == State values (where B is a constant and the smallest
            #                           power of 2 that is greater than the
            #                           largest event value (2^x > n) and
            #                           m starts at 1 and increments for each
            #                           state)
            # No Nested_Switch, Bounds_Check:
            #      2    == lower event value fencepost
            #      3..n == Event values
            #      n+1  == upper event value fencepost
            #      m*B == State values (see above; B > upper fencepost)
            # Nested_Switch, No Bounds_Check:
            #      2..n == Event values
            #      2..m == State values
            # Nested_Switch, Bounds_Check:
            #      2    == lower event value fencepost
            #      3..n == Event values
            #      n+1  == upper event value fencepost
            #      2..m == State values

            sval = 1
            nval = 1

            if check_control("Bounds_Check"):
                sval = 2
                
            for event in self._events:
                sval = sval + nval
                event.numeric_value(sval)
            
            if check_control("Nested_Switch"):
                sval = 1
                nval = 1
            else:
                nval = 1
                while nval <= sval:
                    nval = nval << 1;
                sval = 0
            
            for state in self._states.values():
                if self.init_state and self.init_state == state.name():
                    state.numeric_value(0)
                else:
                    sval = sval + nval
                    state.numeric_value(sval)

        ### Handle Errors
        except 'funky',bar:
            self.status(['Processing'], [ 'BAD!' ])
            print 'SMG Processing Exception (%s)'%(bar)
            raise Parse_Error(bar)
        
        ### Handle Warnings
        except OrphanStates,bar:
            self.status(['Processing'], [ 'Evaluated', 'BAD!' ])
            print 'SMG Processing Exception (%s -- %s)'%(OrphanStates, bar)
        
        except UnreachableSourceStates,bar:
            self.status(['Processing'], [ 'Evaluated', 'BAD!' ])
            print 'SMG Processing Exception (%s -- %s)'%(UnreachableSourceStates, bar)
        
        ### Handle Success
        else:   # Evaluation didn't fail!
            self.status(['Processing' ], ['Evaluated', 'Good'])


    #----------------------------------------------------------------
    #
    def write_C_defs(self, outdesc, use_enums):
        "Write definitions for this state machine to the output descriptor."
        cmntlen=70

        ostring = StringIO.StringIO()
        gen_C_defs_hdr(ostring, cmntlen, self._name, self.info(cmntlen),
                       self._objt, self._evtt,
                       use_enums, check_control("Nested_Switch"),
                       self.init_state)
        cdef_str = ostring.getvalue()
        ostring.close()

        ostring = StringIO.StringIO();
        if check_control("Bounds_Check"):
            if use_enums:
                ostring.write("    %s_EVENT_LOW_FENCEPOST  \t= %4d,\n"%(
                    self.name(), 2))
            else:
                ostring.write("#define %s_EVENT_LOW_FENCEPOST  \t%4d\n"%(
                    self.name(), 2))
        for event in self._events:
            event.write_C_defs(ostring, use_enums)
        if check_control("Bounds_Check"):
            if use_enums:
                ostring.write("    %s_EVENT_HIGH_FENCEPOST  \t= %4d,\n"%(
                    self.name(), len(self._events)+3))
            else:
                ostring.write("#define %s_EVENT_HIGH_FENCEPOST  \t%4d\n"%(
                    self.name(), len(self._events)+3))
        cdef_str = string.replace(cdef_str, '<event_defs>', ostring.getvalue())
        ostring.close()
        
        ostring = StringIO.StringIO()
        for state in self._states.values():
            state.write_C_defs(ostring, use_enums)
        cdef_str = string.replace(cdef_str, '<state_defs>', ostring.getvalue())
        ostring.close()
            
        ostring = StringIO.StringIO()
        for event in self._events:
            entry = event.entry()
            if entry and len(entry) and entry != '--':
                ostring.write("\n\n/** Entry point (%s) for Event %s */\n"%(
                    entry, event.name()))
                try:
                    # Declaration; should always be a string, not a tuple
                    ostring.write(para(
                        "%s;\n"%self._codes[entry].tagged_C_code(self._name),
                        "", "        ", 77))
                except KeyError:
                    raise UnknownCodeTag(\
                          'Entry "%s" for event %s'%(entry, event.name()))
        cdef_str = string.replace(cdef_str, "<entry_defs>", ostring.getvalue())
        ostring.close()

        cdef_str = CXL(cdef_str, self._name)
        outdesc.write(cdef_str)
                

        
    def write_C_code(self, outdesc):
        "Write this state machine code to the specified output descriptor."
        cmntlen = 75

        outdesc.write("\n\n\n\n/*\n")
        outdesc.write(self.info(cmntlen))
        outdesc.write(" */\n\n\n")

        if not self.init_state:
            outdesc.write("void %s_State_Machine_Init(%s %s,\n"%(
                self._name, self._objt, XL("_/OBJ")))
            outdesc.write("%s %s_state_t initial_state)\n{\n"%(" "*26,
                                                               self._name))
            
            if check_control("Trace_Events"):
                outdesc.write('    SM_TRACE_INIT(%s, NULL, %s, initial_state);\n'%(
                    XL("_/OBJ"), self._name))
            outdesc.write("    %s->sm_state = initial_state;\n}\n\n\n"%(
                XL("_/OBJ")))

        if not check_control("Embedded"):
            outdesc.write("char *\n%s_State_Name(%s_state_t state)\n{\n"%(
                self._name, self._name))
            outdesc.write("    switch (state) {\n")
            for state in self._states.values():
                outdesc.write('        case %s: return "%s";\n'%(state.name(),
                                                                 state.name()))
            outdesc.write('    default: return "??unknown??";\n    }\n')
            outdesc.write("}\n\n\n")

            outdesc.write("char *\n%s_State_Desc(%s_state_t state)\n{\n"%(
                self._name, self._name))
            outdesc.write("    switch (state) {\n")
            for state in self._states.values():
                outdesc.write('        case %s: return "%s";\n'%(state.name(),
                                                                 state.desc()))
            outdesc.write('    default: return "??unknown??";\n    }\n')
            outdesc.write("}\n\n\n")


            outdesc.write("char *\n%s_Event_Name(%s_event_t event)\n{\n"%(
                self._name, self._name))
            outdesc.write("    switch (event) {\n")

            for event in self._events:
                outdesc.write('        case %s: return "%s";\n'%(event.name(),
                                                                 event.name()))
            outdesc.write('    default: return "??unknown??";\n    }\n')
            outdesc.write("}\n\n\n")

            outdesc.write("char *\n%s_Event_Desc(%s_event_t event)\n{\n"%(
                self._name, self._name))
            outdesc.write("    switch (event) {\n")
            for event in self._events:
                outdesc.write('        case %s: return "%s";\n'%(event.name(),
                                                                 event.desc()))
            outdesc.write('    default: return "??unknown??";\n    }\n')
            outdesc.write("}\n\n\n")
        

        outdesc.write("void\n%s_State_Machine_Event(\n"%self._name)
        outdesc.write("    %s %s,\n"%(self._objt, XL("_/OBJ")))
        outdesc.write("    %s %s,\n"%(self._evtt, XL("_/EVT")))
        outdesc.write("    %s_event_t event_code\n"%self._name)
        outdesc.write("    )\n{\n")

        if check_control("Trace_Events"):
            outdesc.write('    SM_TRACE_EVENT(%s, %s, %s, event_code);\n\n'%(
                XL("_/OBJ") , XL("_/EVT"), self._name))

        if check_control("Bounds_Check"):
            outdesc.write('    if (event_code <= %s_EVENT_LOW_FENCEPOST ||\n'%(
                self._name))
            outdesc.write('        event_code >= %s_EVENT_HIGH_FENCEPOST)\n'%(
                self._name))
            outdesc.write('        return;\n\n')
            
        if check_control("Nested_Switch"):
            outdesc.write("    switch (%s->sm_state) {\n"%XL("_/OBJ"))
        else:
            outdesc.write("    switch (SM_S_E(%s->sm_state, event_code)) {\n"%(
                XL("_/OBJ")))

        for state in self._states.values():
            state.write_C_code(outdesc, self._name, self._codes)

        outdesc.write('        default:\n');
        if check_control("Nested_Switch"):
            err_id = 2
        else:
            err_id = 3
        write_sm_error(outdesc, err_id, self._name)
        outdesc.write("    }\n")

        if check_control("Trace_Events"):
            outdesc.write('    SM_TRACE_POST_EVENT(%s, %s, %s, event_code);\n\n'%(
                XL("_/OBJ") , XL("_/EVT"), self._name))

        outdesc.write("}\n\n\n")


        for event in self._events:
            entry = event.entry()
            if entry and len(entry) and entry != '--':
                
                outdesc.write("\n\n/*%s\n"%('-' * cmntlen))
                outdesc.write(" - EVENT HANDLER | %s\n"%entry)
                outdesc.write(" -         EVENT | %s\n"%event.name())
                if event.desc():
                    outdesc.write(para(event.desc(),
                                       " -   DESCRIPTION | ",
                                       " -               | ", cmntlen))
                outdesc.write(" %s*/\n\n\n"%('-' * cmntlen))

                ## Entry code; always a string, never a tuple
                outdesc.write(para(
                    "%s\n"%self._codes[entry].tagged_C_code(self._name),
                    "", "                        ", cmntlen))
                outdesc.write("{\n")
                outdesc.write("    %s _sm_obj;\n"%self._objt)
                outdesc.write("    %s _sm_evt;\n\n"%self._evtt)

                prep = event.prep()
                if prep and len(prep) and prep != '--':
                    ## Event entry prep code; always a string, never a tuple
                    outdesc.write(para(
                        "%s\n"%self._codes[prep].tagged_C_code(self._name,
                                                               self._events_names),
                        "    ", "    ", cmntlen))
                    outdesc.write("\n")

                for state in self._states.values():
                    state.write_C_expected(outdesc, self._name,
                                           event.name(), self._codes)
                    
                outdesc.write("    %s_%s(_sm_obj, _sm_evt, %s);\n"%(
                    self._name, "State_Machine_Event", event.name()))
                outdesc.write("}\n")


    def write_P_code(self, outdesc):
        "Write this state machine code to the specified output descriptor."
        cmntlen = 75

        outdesc.write("\n\n\n\n/*\n%s */\n\n\n"%self.info(cmntlen))

        outdesc.write("mtype = {  INITIALIZE_SM, SM_EVENT, %s,\n"%Undef_Trans)

        outdesc.write(para("%s,"%string.join(map(lambda e: e.name(),
                                                 self._events),
                                             ", "),
                           "/*events*/ ",
                           "           ", cmntlen))

        outdesc.write(para(string.join(map(lambda s: s.name(),
                                           self._states.values()), ", "),
                           "/*states*/ ",
                           "           ", cmntlen))
        
        outdesc.write("} /* end mtype */\n\n")

        enames = map(lambda e: e.name(), self._events)
            
        try:
            outdesc.write("""
/** User-defined HEADER **/
%s
/** End of user-defined HEADER **/\n\n"""%(
                self._pcodes['HEADER'].tagged_P_code(self, enames,
                                                     self._pcodes)))
        except KeyError:
            pass    # OK to not have Promela code for HEADER

        outdesc.write("""
proctype %(sm_name)s_SM (chan in_events)
{
     mtype state, op, event;
                      """%{'sm_name':self.name()})

        if self.init_state:
            outdesc.write("""
     state = %(state)s;
     printf("MSC: %(sm_name)s_SM Initialized in state %(state)s\\n");
                """%{'state':self.init_state,
                     'sm_name':self.name()})
        else:
            outdesc.write("""
     in_events?op,event;
     assert(op == INITIALIZE_SM);
     state = event;
     printf("%(sm_name)s_SM Initialized\\n");
                    """%{'sm_name':self.name()})

        try:
            outdesc.write("""
/** User-defined START **/
%s
/** End of user-defined START **/\n\n"""%(
                self._pcodes['START'].tagged_P_code(self, enames,
                                                     self._pcodes)))
        except KeyError:
            pass    # OK to not have Promela code for START

        outdesc.write("""

end: do
            """%{'sm_name':self.name()})

        ##
        ## Output Promela for handling each possible event
        ##

        for event in self._events:
            outdesc.write("""
     :: in_events?SM_EVENT(%(ev_name)s) ->
            """%{'sm_name':self.name(),
                 'ev_name':event.name()})

            try:
                tag = event.prep()
                outdesc.write("""
                  /** Entry: %(tag)s **/
                  %(code)s"""%{'tag':tag,
                                 'ev_name':event.name(),
                                 'code':self._pcodes[tag].tagged_P_code(
                    self, enames, self._pcodes)})
            except KeyError: pass

            outdesc.write("""
                  if
            """%{'sm_name':self.name(),
                 'ev_name':event.name()})

            for state in self._states.values():
                outdesc.write("""
                  :: (state == %(state_name)s) ->
                     printf("%(sm_name)s_SM got %(ev_name)s in %(state_name)s\\n");
                """%{'sm_name':self.name(),
                     'ev_name':event.name(),
                     'state_name':state.name()})

                state.write_P_code(outdesc, self, event, enames, self._pcodes)

            outdesc.write("""
                  :: else ->
                     printf("%(sm_name)s_SM got %(ev_name)s in UNKNOWN STATE: %%d\\n", state);
                     assert(0);  /* event in unknown state */
                  fi;
            """%{'sm_name':self.name(),
                 'ev_name':event.name()})

        outdesc.write("""
     :: in_events?INITIALIZE_SM(event) ->
                  assert(0);  /* attempted re-init of state machine */
                  """)
            
        outdesc.write("""
     od
}


            """)

        try:
            outdesc.write("""
/** User-defined INIT **/
%s
/** End of user-defined INIT **/
            """%(self._pcodes['INIT'].tagged_P_code(self, enames,
                                                    self._pcodes)))
        except KeyError:
            # No user INIT code: generate sample code for user instead
            outdesc.write("""
            init {
                    chan %(sm_name)s_events = [0] of { mtype, mtype };
                    printf("Initiating default test with 3 random events:\\n");
                    run %(sm_name)s_SM(%(sm_name)s_events);
                    """%{'sm_name':self.name()})
            if not self.init_state:
                outdesc.write("""
                    %(sm_name)s_events!INITIALIZE_SM(%(init_state_name)s);"""%{
                    'sm_name':self.name(),
                    'init_state_name':self._states.values()[0].name()})
            import random
            for nrand in range(3):
                outdesc.write("""
                    %(sm_name)s_events!SM_EVENT(%(event)s);"""%{
                    'sm_name':self.name(),
                    'event':random.choice(self._events).name()})
            outdesc.write("""
                    }
                    """)

# }}}



##############################################################################
##############################################################################
# {{{     Class: smg_compiler

#
class smg_compiler:

    """Used to turn an sm_file into C code, including zero or more state
       machine implementations.
    """
    
    #----------------------------------------------------------------
    # Initialization
    #
    def __init__(self, filename=None):
        self._filename = filename
        self._sm_file = None
        self._out_filename = None
        self._def_filename = None
        self._p_filename = None
        self._sm = []

    #----------------------------------------------------------------
    # Low level access routines:
    #    open - opens the input .sm file, verifying access
    #    read - reads the input .sm file to get an sm_file object
    #    write - writes out the .c file containing the created state machines
    #    close - cleans up and terminates processing of .sm/.c file pair
    #
    def open(self, filename=None):
        if filename:
            self._filename = filename
        # Parse filename for extensions
        if self._filename[-3:] == '.sm':
            self._filename = self._filename[:-3]
        elif self._filename[-2] == '.c':
            self._filename = self._filename[:-2]
        self._sm_filename = '%s.sm'%self._filename
        self._out_filename = '%s.c'%self._filename
        self._def_filename = '%s_smdefs.h'%self._filename
        self._p_filename   = '%s.pml'%self._filename
        self._sm_file = smg_file(self._sm_filename)

    def sm_filename(self):
        return self._sm_filename
    
    def read(self):
        if not self._sm_file:
            raise OpenNeeded("reading")
        self._sm_file.read()

    def write_C_defs(self):
        if not self._def_filename:
            raise OpenAndReadNeeded("writing")
        if not self._sm_file:
            raise ReadNeeded("writing")
        outfile = open(self._def_filename, 'w')
        outfile.write(GenFileWarning)
        for sm in self._sm:
            sm.write_C_defs(outfile, check_control("Use_Enums"))
        outfile.close()
        progress('Wrote C Definitions', self._def_filename)

    def write_C_code(self):
        if not self._out_filename:
            raise OpenAndReadNeeded("writing")
        if not self._sm_file:
            raise ReadNeeded("writing")
        outfile = open(self._out_filename, 'w')
        outfile.write(GenFileWarning)

        map(lambda c,o=outfile: c.write_C_code(o),
            filter(lambda p: p.type() == C_code,
                   self._sm_file.phrases()))
##        for phrase in self._sm_file.phrases():
##            if phrase.type() == C_code:
##                phrase.write_C_code(outfile)

        for sm in self._sm:
            sm.write_C_code(outfile)
            progress('%s SM Status'%sm.name(), sm.status())
            
        outfile.close()
        progress('Wrote C Code File', self._out_filename)


    def write_P_code(self):
        if not self._p_filename:
            raise OpenAndReadNeeded("writing")
        if not self._sm_file:
            raise ReadNeeded("writing")
        outfile = open(self._p_filename, 'w')
        outfile.write(GenFileWarning)
        map(lambda sm,o=outfile: sm.write_P_code(o), self._sm)
        outfile.close()
        progress('Wrote Promela Code File', self._p_filename)


    def close(self):
        self.__init__(self._filename)
    
    #----------------------------------------------------------------
    # Internal processing
    #    sm_extract  - obtains list of smg_state_machine objects from smg_file
    #    sm_evaluate - runs evaluation and validation pass on state machines
    #
    def sm_extract(self):
        if not self._sm_file:
            raise ReadNeeded("extracting State Machines")
        sm = None

        phrases = self._sm_file.phrases()
        phrase_index = 0
        
        for phrase in phrases:
            phrase_index = phrase_index + 1
            if phrase.type() == C_code: continue

            words = string.split(phrase.contents())
            if len(words) == 0: continue
            if len(words) < 2:
                raise Incomplete_SM_Statement("not enough words, %s, line %d"%(
                    self._sm_filename, phrase.line_num()))

            if words[0] == SM_Commands[0]:
                if sm: self._sm.append(sm)
                desc=""
                if len(words) > 2: desc = string.join(words[2:])
                sm = smg_state_machine(words[1], desc)
            else:
                try:
                    sm = sm + phrase
                except SM_Include_File, incl_spec:
                    if type(incl_spec) == type( (1,1) ):
                        filename, vers = incl_spec
                    else:
                        filename = incl_spec
                        vers=None
                    for ipath in SM_Include_Paths:
                        ipath_ext = ''
                        if ipath[-1] == '#' and vers:
                            ipath_ext = '-v%s'%vers
                            ipath = ipath[:-1]
                        if ipath[-1] == '*':
                            for ipath2 in os.listdir(ipath[:-1]):
                                sub_sm_fname = os.path.join(ipath[:-1],
                                ipath2+ipath_ext,
                                filename)
                                if os.path.exists(sub_sm_fname): break
                        else:
                            sub_sm_fname = os.path.join(ipath+ipath_ext,
                            filename)
                        if os.path.exists(sub_sm_fname): break
                    sub_sm_file = smg_file(sub_sm_fname)
                    sub_sm_file.read()
                    progress('SM Include File read', sub_sm_fname)
                    sub_phrases = sub_sm_file.phrases()
                    sub_phrases.reverse()
                    discard = map(lambda subphrase, phrases=phrases,
                                  phrase_index=phrase_index:
                                  phrases.insert(phrase_index, subphrase),
                                  sub_phrases)

        if sm:
            self._sm.append(sm)


    def sm_evaluate(self):
        if not self._sm_file:
            raise ReadNeeded("extracting State Machines")
        if len(self._sm) == 0:
            raise ReadNeeded("evaluating State Machines (missing extract?)")
        map(lambda foo: foo.evaluate(), self._sm)
        

    #----------------------------------------------------------------
    # Main access routines:
    #    compile - reads the .sm file, processes the input, writes the .c file
    #    indent  - invokes "indent" on output files; must compile first
    #
    def compile(self, indent=0, viz_output=None):
        self.open()
        self.read()
        progress('SM File read', self._sm_filename)
        self.sm_extract()
        self.sm_evaluate()
        self.write_C_defs()
        self.write_C_code()
        if indent:
            progress('Indenting', '%s and %s'%(self._def_filename,
                                               self._out_filename))
            os.system("indent %s"%self._def_filename)
            os.system("indent %s"%self._out_filename)
        self.write_P_code()
        if viz_output and len(viz_output):
            for sm in self._sm:
                smg_figure(self._filename, viz_output, SMG_FIG_CLEAN, sm)
##                smg_figure(self._filename, viz_output, SMG_FIG_FULL, sm)
                smg_figure(self._filename, viz_output, SMG_FIG_PRIMARY, sm)
        self.close()

# }}}
        

##############################################################################
##############################################################################
# {{{     Main Entry

#

def show_usage():
    print 'Usage: %s [-GMNPTWehilv] filename...      (version %s)'%(
        sys.argv[0], smg_version)
    print '       ____________General operation options___________'
    print '       -h = Show this help and exit'
    print '       -i = Pass C output through "indent"'
    print '       -v = Verbose output'
    print '       ____________C code generation options___________'
    print '       -D = Defer tagged code event generation'
    print '       -N = Nested switch statements for event handling'
    print '       -T = Output SM_TRACE code to trace event occurrences'
    print '       -e = Enum definitions for states and events (single-domain)'
    print '       -l = No #line specifications for .sm file in output file'
    print '       -b = Add bounds checking for incoming event values'
    print '       -E = Embeddable code (no strings, small size, no stdlibs'
    print '       ____________SM Figure generation options________'
    print '       -G = GIF figure output'
    print '       -M = MIF (FrameMaker) figure output'
    print '       -P = Postscript figure output (default)'
    print '       -F = PDF figure output'
    print '       -W = imap (HTML imagemap) figure output'
    print '       ____________SM Input files______________________'
    print '       filename = name of .sm file(s) to process'
    sys.exit(9)

if __name__ == "__main__":

    did_compiles = 0
    
    for arg in sys.argv[1:]:
        if arg[0] == '-':
            for opt in arg[1:]:
                global Verbose;
                if   opt == 'D': adjust_control("Defer_EvGen", 1)
                elif opt == 'G': adjust_control("GViz_Output", "gif")
                elif opt == 'M': adjust_control("GViz_Output", "mif")
                elif opt == 'N': adjust_control("Nested_Switch", 1)
                elif opt == 'P': adjust_control("GViz_Output", "ps")
                elif opt == 'F': adjust_control("GViz_Output", "pdf")
                elif opt == 'T': adjust_control("Trace_Events", 1)
                elif opt == 'W': adjust_control("GViz_Output", "imap")
                elif opt == 'e': adjust_control("Use_Enums", 1)
                elif opt == 'i': adjust_control("Run_Indent", 1)
                elif opt == 'l': adjust_control("Line_Directives", 0)
                elif opt == 'v': adjust_control("Verbose", 1)
                elif opt == 'b': adjust_control("Bounds_Check", 1)
                elif opt == 'E': adjust_control("Embedded", 1)
                elif opt == 'h': show_usage()
                else:
                    print 'Unknown option: %s\n'%opt
                    show_usage()
                    sys.exit(9)
        else:
            sm = smg_compiler(arg)
            sm.compile(check_control("Run_Indent"),
                       check_control("GViz_Output"))
            did_compiles = 1

    if not did_compiles: show_usage()

# }}}

