#!/usr/bin/env python
#
# smg_figure - Module to create figures for the State Machine Generator
#
# This module is a subsidiary module to the primary smg.py module.  This
# module is called to produce graphical figures for the state machine(s).
#

# Copyright (c) 2000-2002, Kevin Quick
# All Rights Reserved
# See the LICENSE file for more information.

# Main interfaces:
#
#    smg_figure(basename, output_type, figure_type, smg_state_machine_object)
#
# where:
#    basename is the base name for the output file
#    output_type is a string that is passed to the -T argument for GViz's dot
#    figure_type is one of:
#                 SMG_FIG_FULL         -- all states and transitions, messy
#                 SMG_FIG_PRIMARY      -- only transitions which change state
#                 SMG_FIG_CLEAN        -- use grouping, etc. to cleanup output
#                 SMG_FIG_EVCLEAN      -- CLEAN + PRIMARY, events only (!code)
#    smg_state_machine_object is the SMG state machine object for which the
#                             figure is to be created.


# {{{ Initialization

import sys,os,string,time
from smg_defs import *
from entitle_ps import entitle_ps
import strblock
from graphviz import graphviz, gv_node, gv_edge


if __name__ == "__main__":
    print 'Please run the smg.py utility instead.'
    sys.exit(1)

# }}}


INP_THRESH   = 4
CLUST_THRESH = 3
DIFF_THRESH  = 2


# {{{ write_viz_states

# {{{ class event_dict
class event_dict:

    def __init__(self, events_only=0):
        self.good_ev_dict = {}
        self.bad_ev_dict = {}
        self.events_only = events_only

    def add_event(self, ev_info):
        pre = ''
        for cl in ev_info[0]:
            pre = '%s%s,'%(pre, cl)
        if len(pre):
            pre = '[%s]'%pre[:-1]
        else:
            pre = '-'

        key = None
        
        if pre == '[%s]'%Undef_Event_Code:
            if ev_info[1] not in self.bad_ev_dict.values():
                key = 'Err#%d'%len(self.bad_ev_dict)
                self.bad_ev_dict[key] = ev_info[1]
            else:
                # reverse lookup to get key for this event
                for key in self.bad_ev_dict.keys():
                    if self.bad_ev_dict[key] == ev_info[1]:
                        break
                if self.bad_ev_dict[key] != ev_info[1]:
                    print "Couldn't find event: %s in %s"%(ev_info[1], self.bad_ev_dict.keys())
                    key = 'Err#0'
        else:
            if self.events_only:
                event = ev_info[1]
            else:
                event='%s :: %s'%(ev_info[1], pre)

                post = ''
                for cl in ev_info[2]:
                    post = '%s%s,'%(post, cl)
                if len(post):
                    event='%s-[%s]'%(event, post[:-1])

            if event not in self.good_ev_dict.values():
                num_evs = len(self.good_ev_dict)
                if num_evs > (len(string.uppercase) * len(string.uppercase)-1):
                    raise RuntimeError('Too Many Events!!! ' + num_evs)
                elif num_evs > len(string.uppercase) - 1:
                    key = '%c%c'%(
                        string.uppercase[num_evs / len(string.uppercase)],
                        string.uppercase[num_evs % len(string.uppercase)])
                else:
                    try:
                        key = string.uppercase[num_evs]
                    except IndexError:
                        print 'Bad single digit key: <%s>'%num_evs
                        key = 'FOO'
                self.good_ev_dict[key] = event
            else:
                # reverse lookup to get key for this event
                for key in self.good_ev_dict.keys():
                    if self.good_ev_dict[key] == event:
                        break
                
        return key

    def good_keys(self):
        rk = self.good_ev_dict.keys()
        rk.sort()
        return rk
    
    def error_keys(self):
        rk = map(lambda errkey: int(errkey[4:]), self.bad_ev_dict.keys())
        rk.sort()
        return map(lambda errno: 'Err#%d'%errno, rk)

    def description(self, key):
        try:
            return self.good_ev_dict[key]
        except KeyError:
            return self.bad_ev_dict[key]
# }}}



# }}}



# {{{ write_viz_file
def write_viz_file(viz_filename, figure_type, sm_obj):
        if not viz_filename:
            raise OpenAndReadNeeded("writing")
        outfile = open(viz_filename, 'w')
        outfile.write(GenFileWarning)

        cmntlen = 76;
        outfile.write("/**%s\n"%('*' * cmntlen))
        outfile.write(" **\n")
        outfile.write(" ** GViz dot file commands\n")
        outfile.write(" **\n\n");
        outfile.write(sm_obj.info(cmntlen))
        outfile.write(" **/\n\n\n")

        edict = event_dict(figure_type == SMG_FIG_EVCLEAN)
        g = graphviz(sm_obj.name())
        g.fullpage()
        g.landscape()
        if figure_type in [SMG_FIG_PRIMARY, SMG_FIG_EVCLEAN]:
            g.attr('concentrate', 'true')

        saw_undef_trans = 0
        node_role_dec = { 'Terminal' : ('shape','triangle'),
                          'Source'   : ('shape','invtriangle'),
                          'Orphan'   : ('shape','doublecircle') }
        for state in sm_obj.state_list():
            n = gv_node(state.name())
            if state.role() in node_role_dec.keys():
                n.attr(node_role_dec[state.role()][0],
                       node_role_dec[state.role()][1])
            g.add(n)
            for fromstate,evname,tostate,expected in state.event_info():
                if Undef_Event_Code in fromstate:
                    if figure_type == SMG_FIG_PRIMARY: continue
                    saw_undef_trans = 1
                evlbl = edict.add_event( (fromstate,evname,tostate,expected) )
                for tgt_state in state.next_states(evname):
                    e = gv_edge(state.name(), tgt_state, evlbl)
                    if expected: e.attr('style','bold')
                    g.add(e)

        if saw_undef_trans:
            n = gv_node(Undef_Trans)
            n.attr('shape','doubleoctagon')
            n.color('red')
            n.attr('fontcolor','red')
            g.add(n)

        for nodename,lbl_prefix,lbl_list in [
            ('good_ev', "EVENTS", edict.good_keys()),
            ('bad_ev', "BAD EVENTS", edict.error_keys()) ]:
            if len(lbl_list):
                n = gv_node(nodename)
                n.attr('shape','plaintext')
                n.label('    %s:\\l%s  \\l'%(lbl_prefix, string.join(
                    map(lambda ev,edict=edict: "%s%s = %s"%(
                    " "*10, ev, edict.description(ev)),
                        lbl_list), '\\l')))
                g.add(n)
               
        g.autocluster()
        outfile.write(g.dot())
        outfile.close()
        progress('Wrote GViz figure commands', viz_filename)

# }}}



# {{{ smg_figure

def smg_figure(basename, output_type, figure_type, sm_obj):
#    basename is the base name for the output file
#    output_type is a string that is passed to the -T argument for GViz's dot
#    figure_type is one of:
#                 SMG_FIG_FULL         -- all states and transitions, messy
#                 SMG_FIG_PRIMARY      -- only transitions which change state
#                 SMG_FIG_CLEAN        -- use grouping, etc. to cleanup output
#    sm_obj is the SMG state machine object for which the
#                             figure is to be created.
    viz_filename = '%s%c.dot'%(basename, figure_type[0])
    write_viz_file(viz_filename, figure_type, sm_obj)
    fig_filename = '%s%c.%s'%(basename, figure_type[0], output_type)
    #progress('Generating GViz "dot" %s figure'%string.upper(output_type),
    #         fig_filename)
    os.system("dot -T%s -o %s %s"%(output_type, fig_filename, viz_filename))
    tstr = time.strftime("%d %b %Y %H:%M", time.localtime(time.time()))
    if output_type == "ps":
        entitle_ps(fig_filename,
                   title='%s %s State Diagram'%(sm_obj.name(), figure_type),
                   urtext='SMG %s\n%s'%(smg_version, tstr),
                   ultext='%s DESCRIPTION:%s'%(sm_obj.name(),
                                               sm_obj.description()),
                   lltext=sm_obj.summary())
    else:
        print "Don't know how to add a title to a %s figure..."%output_type
    progress('Wrote %s figure'%string.upper(output_type), fig_filename)
    
# }}}
