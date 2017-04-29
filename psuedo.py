#!/usr/bin/env python
# -*- coding: utf-8 -*-
import ast, argparse, os
import uclidPrint, astTransform, fileConvert
# import matplotlib.pyplot as plt


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('filename',
                    help='psuedocode file to model')
    parser.add_argument("-k", '--keep', action="store_true",
                    help='keeps the intermediate language file')
    parser.add_argument("-ip",'--interPrint', action='store_true',
                    help='Prints the intermediate python syntax')
    args = parser.parse_args()


    fc = fileConvert.fileConverter(filename = args.filename)
    filename = fc.convert()
    f = open(filename, 'r')
    fstr = f.read()
    f.close()
    if args.interPrint:
        print fstr
    v = astTransform.astVisit(ast.parse(fstr, filename=filename))
    writer = uclidPrint.modulePrint(varDict = v.varDict, filename = filename, phi = v.phiDict, CS_SS = v.CS_SS)
    writer.write()
    if not args.keep:
        os.system("rm " + filename)
        filename = filename[:-9] + ".txt"
        os.system("rm " + filename)
        filename = filename.replace("indent", "")
        os.system("rm " + filename)
