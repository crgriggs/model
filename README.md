Usage: psuedo.py [-h] [-k] [-ap] [-ip] filename

positional arguments:
  filename           psuedocode file to model

optional arguments:
  -h, --help         show this help message and exit
  -k, --keep         keeps the intermediate language file
  -ap, --astPrint    Prints the AST
  -ip, --interPrint  Prints the intermediate python syntax

Above is the basic input format which first will detect if the psuedocode is Intel or AMD based on the assign statments which are unique to the respective psuedocodes, then will create a file instructPython.txt which allows the use of pythons built in AST class to 
