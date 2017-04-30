Requirements

networkx - pip install networkx
https://networkx.github.io/documentation/development/install.html
graphing library used to create CFG of instructions

sympy - pip install sympy
http://docs.sympy.org/latest/install.html#
boolean algebra library used to negate and simply boolean algebra

Usage: psuedo.py [-h] [-k] [-ip] filename

positional arguments:
  filename           psuedocode file to model

optional arguments:
  -h, --help         show this help message and exit
  -k, --keep         keeps the intermediate language file
  -ip, --interPrint  Prints the intermediate python syntax

Above is the basic input format which will attempt to create a model for UCLID and print to that model to the command line