This is a fork of SMG (http://smg.sf.net/) with minor improvments and updates.

Changes from SMG-1.7.5 (http://sourceforge.net/projects/smg/files/SMG/SMG%20v1.7.5/SMG-1.7.5.zip):
- Fix warnings generated when compiling generated code
- Update python code to use class based exceptions rather than obsolete string based exceptions
- Add option (-F) to generate PDF state machine figures
- Add old state (the state before the transaction occured) as 5th argument to ```SM_TRACE_EVENT``` and move call to ```SM_TRACE_EVENT``` to end of generated ```<state machine name>_State_Machine_Event``` function definition.
