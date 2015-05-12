This is a fork of SMG (http://smg.sf.net/) with minor improvments and updates.

Changes from SMG-1.7.5 (http://sourceforge.net/projects/smg/files/SMG/SMG%20v1.7.5/SMG-1.7.5.zip):
- Fix warnings generated when compiling generated code
- Update python code to use class based exceptions rather than obsolete string based exceptions
- Add option (-F) to generate PDF state machine figures
- Add an additional trace function ```SM_TRACE_POST_EVENT``` that is called at the end of a transaction
- Add option (-p) to locate state and event names and descriptions in program space for use with AVR libc
