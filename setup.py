#!usr/bin/env python

import os,sys,string
from distutils.core import setup

l=open('LICENSE','r').readlines()

setup (name = "SMG",
       version="1.7.5",
       description="State Machine Generator Utility",
       author="Kevin Quick",
       author_email="kquick@users.sourceforge.net",
       url="http://smg.sourceforge.net/",
       license=string.join(l,'\n'),
       long_description="""The SMG is a utility which can scan an input file for specific
  directives that describe a State Machine (States, Events,
  Transitions, and associated Code segments) and generate several
  different outputs: C code to implement that State Machine, Promela
  code to verify the State Machine using \hyperlink{Spin}{Spin}, and a
  graphical representation of that State Machine for analytical
  purposes.  In mechanical terms, the SMG may be thought of as a
  specific-purpose C preprocessor.""",
       platforms='ANY',
       packages= ['smg']
       )

