# -*- coding: utf-8 -*-
import re
class fileConverter():

    def __init__(self, filename):
        self.filename = filename
    
    def convert(self):
        file = self.intermediateConvert(self.filename)
        file = self.indentationConvert(file)
        file = self.conditionalConvert(file)
        return file

    #basic conversion of keywords such as IF -> if
    def intermediateConvert(self, filename):
        readFile = open(filename)
        outfile = filename.split(".")[0] + "intermediate.txt"
        writeFile = open(outfile, 'w+')
        numSpaces = 0
        for line in readFile:
            #removing the trailing H on Hex number and adding "hex" to the beginning 
            #to bypass python's hate for variables that start with a num
            r = re.search(r'\b[0-9A-F_]+H', line)
            if r != None:
                replace = r.group().replace("H", "")
                line = re.sub(r'\b[0-9A-F_]+H', ("hex"+replace), line)
            if "≥" in line:
                line = line.replace("≥", ">=")
            if "=" in line: 
                line = line.replace(" = ", ' == ')
            if "←" in line:
                line = line.replace("←", "=")
            if "≠" in line:
                line = line.replace("≠", "!=")
            if "-" in line:
                line = line.replace("-", "_")
            if ";" in line:
                line = line.replace(";", "")
            if "NOT" in line:
                line = line.replace("NOT", "~")
            if "AND" in line:
                line = line.replace("AND", "&")
            if "OR" in line:
                line = line.replace("OR", "|")
            if "ELSE IF" in line:
                line = line.replace("ELSE IF", "elif")
            if "IF" in line:
                line = line.replace("IF", "if")
            if "ELSE" in line:
                line = line.replace("ELSE", "else:")
            if "#" in line:
                if "if" in line and "THEN" in line:
                    line = line.split("THEN")
                    writeFile.write(line[0]+"\n")
                    line = "    " + line[1]
                if "THEN" in line:
                    line = line.replace("THEN", "")
                line = line.replace("#", "exitStatus = ").replace("(0)", "")
            if "THEN" in line:
                line = line.split("THEN")
                writeFile.write(line[0] + "THEN\n")
                line = line[0] + "    " + line[1]
            if "*)" in line:
                line = line.replace("(*", "#")
                line = line.replace("*)", "")
            writeFile.write(line)
        return outfile

    #finds the number of spaces before a line
    def findPrecedingNumSpaces(self, line):
        return len(line) - len(line.lstrip())

    #providing the correct indentations
    #key idea here is that the only difference between intel syntax
    #and python is the extra indentation for then
    #so keep a stack of indentations for then occurences
    #every line should be unindented 4*#thens spaces
    #pop a then when we get to a location that has less spaces b4 it  
    def indentationConvert(self, fileName):
        readFile = open(fileName)
        outfile = fileName.split(".")[0] + "indent.txt"
        writeFile = open(outfile, 'w+')
        thenLoc = []
        for line in readFile:
            if line.split("#")[0].strip() == "THEN":
                thenLoc.append(self.findPrecedingNumSpaces(line))
                continue
            if line.strip() == "FI" or line.strip() == "END":
                continue 
            elif len(thenLoc) > 0 and self.findPrecedingNumSpaces(line) < thenLoc[-1]:
                del thenLoc[-1]
            writeFile.write(line[4*len(thenLoc):])
        return outfile

    #handling intel if and elif conditionals
    def conditionalConvert(self, fileName):
        readFile = open(fileName)
        outfile = fileName.split(".")[0] + "inter.txt"
        writeFile = open(outfile, 'w+')
        for line in readFile:
            if "FI" in line:
                line = line.replace("FI", "")
            if line.lstrip().startswith('if') or line.lstrip().startswith('elif'):
                comment = ""
                if "#" in line:
                    comment = "#" + line.split("#")[1].rstrip()
                    line = line.split("#")[0]
                if "elif" in line:
                    conditional = line.split("elif")[1]
                    line = line.split("elif")[0] + "elif"
                else:
                    conditional = line.split("if")[1]
                    line = line.split("if")[0] + "if"
                conditional = conditional.strip()
                if "=" not in conditional:
                    conditional = conditional.replace(" ", "_")
                conditional = " " + conditional
                writeFile.write(line + conditional + ":" + comment + "\n")
            else:
                writeFile.write(line)
        return outfile


