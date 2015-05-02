#!/usr/bin/env python

# graphviz -- Python interface to the GraphViz graphing utility.
#
# Copyright 2002 by Kevin Quick <quick@null.net>.  All rights reserved.

import string

       #  #  ###  ###  #     ###  ###  #   #        ###   ###  #  #   ###      
       #  #   #    #   #      #    #    # #         #  #   #   ## #  #         
 ####  #  #   #    #   #      #    #     #          ###    #   ####   ##   ####
       #  #   #    #   #      #    #     #          # #    #   # ##     #      
        ##    #   ###  ####  ###   #     #          #  #   #   #  #  ###       


mlabelsep = '|'

def dictstr(label, the_dict, sep=',', pfx='', sfx=''):
    "Generates 'key=value;\n...' list from input dict; no = if value is array"
    astr = []
    if label and len(label):
        if 'shape' in the_dict.keys() and the_dict['shape'] == 'record':
            astr.append('label="%s"'%label)
        else:
            lbls = string.split(label, mlabelsep)
            if len(lbls) == 1:
                astr.append('label="%s"'%label)
            else:
                bstr = ''
                cstr = []
                for dstr in lbls:
                    if len(bstr) <= 8:
                        if len(bstr) == 0:
                            bstr = dstr
                        else:
                            bstr = '%s%s%s'%(bstr, mlabelsep, dstr)
                    else:
                        cstr.append(bstr)
                        bstr = dstr
                cstr.append(bstr)
                astr.append('label="%s"'%string.join(cstr,'%s\\n'%mlabelsep))
    for key in the_dict.keys():
        if the_dict[key][0] == '[':
            astr.append('%s %s'%(key, the_dict[key]))
        else:
            astr.append('%s=%s'%(key, the_dict[key]))
    if len(astr):
        return '%s%s%s'%(pfx, string.join(astr, sep), sfx)
    else:
        return ''

def attrstr(label, attrdict):
    "Generates bracketed 'key=value,...' list from input dictionary"
    return dictstr(label, attrdict, ',', '[ ', ' ]')
    
    
def stmtstr(label, stmtdict):
    "Generates 'key=value;\n...' list from input dict; no = if value is array"
    return dictstr(label, stmtdict, ';\n', '', ';\n')


def dictadd(dict1, dict2):
    "Adds two dictionaries together; result is elements from both"
    rdict = dict1
    for key in dict2.keys():
        rdict[key] = dict2[key]
    return rdict

def is_safechar(c):
    return c in string.ascii_letters

def label_elem_id(elemname, elemnum, pfx=''):
    if not elemname or not len(elemname): return ''
    id = string.join(filter(is_safechar, elemname),'')
    if not len(id): return '%s%d'%(pfx, elemnum)
    return id

def record_port(record_ast, recordname, elemname, pfx='L'):
    "For a record (AST), return the portname edge target for elemname"
    r = []
    print 'record_port(..., %s, %s)'%(elemname, pfx)
    for e in record_ast:
        if type(e) == type((1,2)) or type(e) == type([1,2]):
            p = record_port(e, recordname, elemname, '%sL'%pfx)
            if p != recordname: return p
            r.append('NOTINTHISSUBELEM')
            continue
        elif type(e) == type('string'):
            s = e
        else:
            s = str(e)
        print '    s: %s'%s
        if s == elemname:
            return '%s:%s'%(recordname, label_elem_id(s, len(r), pfx))
        r.append(s)
    return recordname  # No port, just point to record in general

def seq_to_recordlabel(seq, pfx='L'):
    r = []
    for e in seq:
        if type(e) == type((1,2)) or type(e) == type([1,2]):
            r.append('{%s}'%seq_to_recordlabel(e,'%sL'%pfx))
            continue
        elif type(e) == type('string'):
            s = e
        else:
            s = str(e)
        l = label_elem_id(s,len(r),pfx)
        if len(l):
            r.append('<%s>%s'%(l,s))
        else:
            r.append(s)
    return string.join(r,'|')


        ###    ##    ###  ####         ###  #      ##    ###   ###      
        #  #  #  #  #     #           #     #     #  #  #     #         
  ####  ###   ####   ##   ###         #     #     ####   ##    ##   ####
        #  #  #  #     #  #           #     #     #  #     #     #      
        ###   #  #  ###   ####         ###  ####  #  #  ###   ###       

class gv_base:
    def __init__(self, name, type):
        namec = filter(lambda c: c in string.ascii_letters + string.digits + '_', name)
        self._name = ''.join(namec)
        self._type = type
        self._label = name
        self._attrs = {}
    def __str__(self):
        return '%s %s "%s" <%s> %s'%(self._type, self._name,
                                     self._dotcmd(),
                                     self._label, self._attrs)
    def __repr__(self): return '%s(%s)'%(self._type, self._name)
    def name(self): return self._name
    def type(self): return self._type
    def label(self, newlabel=None):
        if newlabel:
            if type(newlabel) == type('string'):
                self._label = newlabel
            elif type(newlabel) == type([0,1]) or \
                 type(newlabel) == type((0,1)) :
                self._label = seq_to_recordlabel(newlabel)
                self.attr('shape','record')
            else:
                self._label = str(newlabel)
        if not self._label: return self._name
        return self._label
    def color(self, newcolorname=None):
        if newcolorname: self._attrs['color'] = newcolorname
        return self._attrs['color']
    def attr(self, attrname, attrvalue=''):
        if attrvalue: self._attrs[attrname] = attrvalue
        try:
            return self._attrs[attrname]
        except KeyError: return None
    def dot(self):
        return '%s %s;\n'%(self._dotcmd(),
                           attrstr(self._label, self._attrs))
    def _dotcmd(self): return self._name
    

              ####  #     ####  #   #  ####  #  #  ###   ###            
              #     #     #     ## ##  #     ## #   #   #               
  ####  ####  ###   #     ###   # # #  ###   ####   #    ##   ####  ####
              #     #     #     #   #  #     # ##   #      #            
              ####  ####  ####  #   #  ####  #  #   #   ###             


class gv_node (gv_base):
    def __init__(self, name):
        gv_base.__init__(self, name, 'NODE')

#kwqkwqKWQkwqKWQkwqKWQ: if node name is an array (or nest of arrays) node type is record and arrays describe vert/hor/vert/hor nesting of record points.  Do anything for ease of port specification on vectors?
#kwqKWQkwqKWQ: nesting of clusters?

class gv_edge (gv_base):
    def __init__(self, from_node, to_node,label=''):
        if isinstance(from_node, gv_node): from_node = from_node.name()
        if isinstance(to_node, gv_node): to_node = to_node.name()
        gv_base.__init__(self, '%s->%s'%(from_node, to_node), 'EDGE')
        self._fnode = from_node
        self._tnode = to_node
        if label: self.label(label)
        else: self.label(' ')
    def _dotcmd(self): return '%s -> %s'%(self._fnode, self._tnode)
    

class gv_cluster (gv_base):
    StdColors = [ 'grey90', 'yellow', 'cyan', 'orchid', 'lawngreen',
                  'orange', 'tan', 'lavender', 'gray80' ]
    def __init__(self, cname):
        gv_base.__init__(self, cname, 'CLUS')
        self._statements  = {}
        self._subelements = {}  # Key is name, element is gv_node
        self._visible = 1
    def invisible(self): self._visible = 0
    def visible(self):   self._visible = 1
    def name(self):
        if self._visible: return 'cluster_%s'%self._name
        return self._name
    def color(self, colorname=''):
        if colorname:
            if colorname == 'auto':
                colorname = self.StdColors[hash(self)%len(self.StdColors)]
            self._statements['color'] = colorname
        self._statements['style'] = 'filled'
        self._statements['node']  = '[style=filled,color=white]'
        return self._statements['color']
    def dot(self):
        return 'subgraph %s {\n%s%s}\n'%(
            self.name(),
            stmtstr(self._label, self._statements),
            string.join(map(lambda x: x.dot(),
                            self._subelements.values()), ''))
    def __str__(self):
        return '%s {\n%s%s}\n'%(gv_base.__str__(self),
                                self._statements,
                                map(str, self._subelements))
    def add(self, node):
        self._subelements[node.name()] = node
    def as_node(self):
        node = gv_node('CL_%s'%self.name())
        node.label('%s'%self.label())
        if 'color' in self._statements.keys():
            node.color(self._statements['color'])
            node.attr('style', 'filled')
        return node
                                                 


         ###  ###    ##   ###   #  #         ###  #      ##    ###   ###      
        #     #  #  #  #  #  #  #  #        #     #     #  #  #     #         
  ####  # ##  ###   ####  ###   ####        #     #     ####   ##    ##   ####
        #  #  # #   #  #  #     #  #        #     #     #  #     #     #      
         ###  #  #  #  #  #     #  #         ###  ####  #  #  ###   ###       

class graphviz:
    def __init__(self, name):
        self._elements = {}   # Key is name, element is gv_{node|edge|cluster}
        self._statements = {}
        self._name = name
    # Specify various attributes controlling the graph's parameters
    _std_fullpage = { 'ratio':'fill', 'center':'1', 'shape':'ellipse',
                      'style':'solid',
                      'arrowhead':'normal', 'arrowtail':'none'
                      }
    _landscape = { 'size':'"10,7"', 'page':'"8.5,11"', 'rotate':'90' }
    _portrait  = { 'size':'"7,10"', 'page':'"11,8.5"', 'rotate':'0' }
    def fullpage(self):
        self._statements = dictadd(self._statements, self._std_fullpage)
    def landscape(self):
        self._statements = dictadd(self._statements, self._landscape)
    def portrait(self):
        self._statements = dictadd(self._statements, self._portrait)
    def attr(self, attrname, attrvalue=''):
        if attrvalue: self._statements[attrname] = attrvalue
        return self._statements[attrname]
    # Input Handling
    def add(self, element):
        "Add a node, edge, or cluster to this graph"
        name = element.name()
        if name not in self._elements.keys():
            self._elements[name] = element
            return element
        if element.label() in string.split(self._elements[name].label(),
                                           mlabelsep):
            return self._elements[name]
        self._elements[name].label('%s%s%s'%(
            self._elements[name].label(), mlabelsep, element.label()))
        for akey in element._attrs.keys():
            self._elements[name].attr(akey, element._attrs[akey])
        return element
    # Return only elements of this graph of the specified type
    def _of_type(self, of_type):
        return filter(lambda x,of_type=of_type: x.type() == of_type,
                      self._elements.values())
    def nodes(self): return self._of_type('NODE')
    def edges(self): return self._of_type('EDGE')
    def clusters(self): return self._of_type('CLUS')
    # Output Preparation
    def __str__(self):
        return 'GRPH {%s} <%s>'%(stmtstr('', self._statements),
                                 string.join(map(str, self._elements.values()),'\n'))
    def dot(self):
        "Return the GraphViz dot notation for this graph"
        return 'digraph %s {%s%s}\n'%(
            self._name,
            stmtstr('', self._statements),
            string.join(
            reduce(lambda x,y: x+y,
                   map(lambda type:
                       map(lambda x: x.dot(), self._of_type(type)),
                       [ 'CLUS', 'NODE', 'EDGE' ])),
            '')
            )
    # Manipulation and Massaging
    def autocluster(self, min_nodes=3):
        "Automatically make a cluster/clusternode to eliminate similar edges"
        pcl = {}
        for n in self.nodes():
            # find all edges terminating on the test node
            srcs = filter(lambda e,n=n: e._tnode == n.name(), self.edges())
            # make a dictionary: key is edge label, values are all
            # above edges with this label
            lsrcs = {}
            for e in srcs:
                key = e.label()
                if e.attr('style') == 'bold': key = "%s bOlD"%key
                if key in lsrcs.keys():
                    lsrcs[key].append(e)
                else:
                    lsrcs[key] = [e]
            # Now remember all arrays of edges greater than the minimum
            clsrcs = filter(lambda lsrc:len(lsrc) >= min_nodes, lsrcs.values())
            # Store each array in our possible cluster dictionary, key
            # is len of array
            for clsrc in clsrcs:
                if len(clsrc) in pcl.keys():
                    pcl[len(clsrc)].append( (n,clsrc) )
                else:
                    pcl[len(clsrc)] = [ (n,clsrc) ]
        # Now process each possible cluster, from the most entries to the least
        pcllens = pcl.keys()
        pcllens.sort()
        pcllens.reverse()
        clnum = 1
        usednodes = []
        for pcllen in pcllens:
            for tgtnode,tgtedges in pcl[pcllen]:
                # Get all source nodes for this potential cluster
                srcnodes = map(lambda edge: edge._fnode, tgtedges)
                # If any nodes are already used in a cluster, skip
                # this one since a node can only be a part of one
                # cluster at a time
                if len(filter(lambda n, usednodes=usednodes: n in usednodes,
                              srcnodes)):
                    continue
                # Make a cluster!
                cl = gv_cluster('%d'%clnum)
                cl.label('Cluster %d'%clnum)
                cl.color('auto')
                self.add(cl)
                clnum = clnum + 1
                # Add all source nodes for this collection to the cluster,
                # removing those source nodes from the top-level list of
                # nodes and also removing all associated edges
                for srcnode in srcnodes:
                    try:
                        cl.add(self._elements[srcnode])
                        del self._elements[srcnode]
                    except KeyError:
                        print 'NO KEY "%s" IN'%srcnode, str(self._elements)
                        print '-'*40
                for tgtedge in tgtedges:
                    del self._elements[tgtedge.name()]
                # Now create the node representing the cluster and an edge
                # linking that new node to the target node
                clnd = cl.as_node()
                self.add(clnd)
                e = gv_edge(clnd.name(), tgtnode.name())
                e.label(tgtedges[0].label())
                self.add(e)
                usednodes = usednodes + srcnodes



              #   #   ##   ###  #  #       ###  ####   ###  ###            
              ## ##  #  #   #   ## #    #   #   #     #      #             
  ####  ####  # # #  ####   #   ####   #    #   ###    ##    #   ####  ####
              #   #  #  #   #   # ##  #     #   #        #   #             
              #   #  #  #  ###  #  #        #   ####  ###    #             

if __name__ == "__main__":
    # Generate test graphs
    testgraphs = { 'testgr.1' : [gv_node('A'), gv_node('B'), gv_edge('A','B')],
                   'testgr.2' : [gv_node('A'), gv_node('B'),
                                 gv_node('C'), gv_node('D'),
                                 gv_edge('A','B'),
                                 gv_edge('B','C'),
                                 gv_edge('C','D'),
                                 gv_edge('D','A')],
                   'testgr.3' : [ gv_node('Terminating'),
                                  gv_node('Uninitialized') ],
                   'testgr.4' : [ gv_node('Terminating'),
                                  gv_node('Uninitialized'),
                                  gv_node('Initing'),
                                  gv_node('Disconnected'),
                                  gv_node('Serving'),
                                  gv_node('Ready'),
                                  gv_edge('Initing','Initing','A|C|F|G'),
                                  gv_edge('Ready','Disconnected','M'),
                                  gv_edge('Serving','Serving','A|I|C|K|L|F|G'),
                                  gv_edge('Initing', 'Uninitialized','B'),
                                  gv_edge('Uninitialized', 'Uninitialized',
                                          'I|C|K|L|F|G|R'),
                                  gv_edge('Terminating', 'Terminating',
                                          'A|I|C|K|L|P|G|H'),
                                  gv_edge('Initing', 'Terminating', 'H'),
                                  gv_edge('Disconnected', 'Terminating', 'H'),
                                  gv_edge('Serving', 'Terminating', 'H'),
                                  gv_edge('Ready', 'Terminating', 'H'),
                                  ],
                   }
    fntrans = string.maketrans(string.letters+string.digits,
                               string.letters+string.digits)
    for testg in testgraphs.keys():
        f = open(testg,'w')
        g = graphviz(string.translate(testg,fntrans,string.punctuation))
        g.fullpage()
        map(g.add, testgraphs[testg])

        if testg == 'testgr.3':
            c = gv_cluster('1')
            c.label('Cluster 1')
            c.color('auto')
            n = gv_node('Initing')
            c.add(n)
            n = gv_node('Disconnected')
            c.add(n)
            n = gv_node('Serving')
            c.add(n)
            n = gv_node('Ready')
            c.add(n)
            g.add(c)
            e = gv_edge('Initing','Initing')
            e.label('A| C| F| G')
            g.add(e)
            e = gv_edge('Initing', 'Disconnected')
            e.label('E')
            e.attr('style','bold')
            g.add(e)
            e = gv_edge('Disconnected', 'Ready')
            e.label('O')
            e.attr('style','bold')
            g.add(e)
            e = gv_edge('Ready', 'Disconnected')
            e.label('M')
            g.add(e)
            e = gv_edge('Ready', 'Ready')
            e.label('A| I| J| K|L|G')
            e.attr('style','bold')
            g.add(e)
            e = gv_edge('Initing', 'Serving')
            e.label('D')
            e.attr('style','bold')
            g.add(e)
            e = gv_edge('Serving', 'Serving')
            e.label('A|I|C|K|L|F|G')
            g.add(e)
            e = gv_edge('Initing', 'Uninitialized')
            e.label('B')
            g.add(e)
            e = gv_edge('Uninitialized', 'Initing')
            e.label('Q')
            e.attr('style','bold')
            g.add(e)
            e = gv_edge('Uninitialized', 'Uninitialized')
            e.label('I|C|K|L|F|G|R')
            g.add(e)
            e = gv_edge('Terminating', 'Terminating')
            e.label('A|I|C|K|L|P|G|H')
            g.add(e)
            cn = c.as_node()
            g.add(cn)
            e = gv_edge(cn.name(), 'Terminating')
            e.label('H')
            g.add(e)

        if testg == 'testgr.4':
            e = gv_edge('Initing', 'Disconnected','E')
            e.attr('style','bold')
            g.add(e)
            e = gv_edge('Disconnected', 'Ready','O')
            e.attr('style','bold')
            g.add(e)
            e = gv_edge('Ready', 'Ready','A| I| J| K|L|G')
            e.attr('style','bold')
            g.add(e)
            e = gv_edge('Initing', 'Serving','D')
            e.attr('style','bold')
            g.add(e)
            e = gv_edge('Uninitialized', 'Initing', 'Q')
            e.attr('style','bold')
            g.add(e)
            g.autocluster()
            
        f.write(g.dot())
        f.close()
        print 'Wrote Test:',testg
    print 'End Tests'

#TODO:
#  Records
#  Subgraph extraction
#  Output order should be edges, clusters, nodes?
