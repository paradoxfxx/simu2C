# simu2C
Translate a Simulink block diagram into C-code, without using Simulink Coder or Embedded Coder from Mathworks

The main goal is to translate a Simulink Block diagram into C-code, starting from the XML description.
The XML code will be first translate into a netlist (similar to a PSPICE netlist), and then it is possible to generate C-code from this list using a generator similar to the one in the pysimCoder repository.

A subset of blocks of Simulink should be available

The folder "Example" contains a python script that generate the code of a simple discrete integrator with sampling time 1''s.
The generated code will be stored into the folder "testIntg_gen".

Simply launch "python test_Intg.py". The code requires the python control system toolbox for the dss block.

The generated C-code call the functions of the files "print.c", "dss.c" and "step.c"
