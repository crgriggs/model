# -*- coding: utf-8 -*-
import re

rflagsDict ={'CF': 'State.rflags # [0:0]', 'PF': 'State.rflags # [1:1]', 'AF': 'State.rflags # [4:4]', 'ZF': 'State.rflags # [6:6]', 'SF': 'State.rflags # [7:7]', 'TF': 'State.rflags # [8:8]', 'IF': 'State.rflags # [9:9]', 'DF': 'State.rflags # [10:10]', 'OF': 'State.rflags # [11:11]', 'IOPL': 'State.rflags # [13:12]', 'NT': 'State.rflags # [14:14]', 'RF': 'State.rflags # [16:16]', 'VM': 'State.rflags # [17:17]', 'AC': 'State.rflags # [18:18]', 'VIF': 'State.rflags # [19:19]', 'VIP': 'State.rflags # [20:20]', 'ID': 'State.rflags # [21:21]'}

class fileConverter():

    def __init__(self, filename):
        self.filename = filename
    
    def convert(self):
        file = self.intermediateConvert(self.filename)
        file = self.indentationConvert(file)
        file = self.conditionalConvert(file)
        return file

    def englishWords(self, line):
        if " and " in line:
            return " and ".join(map(lambda x: self.englishWords(x), line.split(" and ")))
        elif " or " in line:
            return " or ".join(map(lambda x: self.englishWords(x), line.split(" or ")))
        if " & " in line:
            return " & ".join(map(lambda x: self.englishWords(x), line.split(" & ")))
        elif " | " in line:
            return " | ".join(map(lambda x: self.englishWords(x), line.split(" | ")))
        else:
            if "=" not in line and ">" not in line and "<" not in line:
                return line.strip().replace(" ", "_")
            return line


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
            r = re.search(r'\b[0-9A-F_]+H', line)
            line = line.replace(" = ", ' == ')
            if "OperandSize" in line:
                line = line.split('OperandSize == ')[0] + "OperandSize == bits" + line.split('OperandSize == ')[1]
            if "StackAddrSize" in line:
                line = line.split('StackAddrSize == ')[0] + "StackAddrSize == bits" + line.split('StackAddrSize == ')[1]
            line = line.replace("≥", ">=")
            if "VIF" not in line:
                line = line.replace("IF ←", "rflags_if =")
            line = line.replace("←", "=")
            line = line.replace("EFLAGS.", "")
            line = line.replace("≠", "!=")
            line = line.replace("-", "_")
            line = line.replace(";", "")
            line = line.replace("NOT", "~")
            line = line.replace("AND", "&")
            if "IF" in line and "OR" in line:
                line = line.replace("OR", "or")     
            line = line.replace("OR", "|")        
            line = line.replace("ELSE IF", "elif")        
            line = line.replace("IF", "if")        
            line = line.replace("ELSE", "else:")
            line = line.replace("Vif", "VIF")
            line = line.replace("–", "-")
            for var in rflagsDict:
                line = line.replace(var+" " , "rflags_"+var.lower())
                line = line.replace(" " + var , "rflags_"+var.lower())
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
            if len(thenLoc) > 0 and self.findPrecedingNumSpaces(line) < thenLoc[-1]:
                del thenLoc[-1]
            if line.strip() in ["FI", "END", "FI)"]:
                continue 
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
                conditional = " " + self.englishWords(conditional)
                writeFile.write(line + conditional + ":" + comment + "\n")
            else:
                writeFile.write(line)
        return outfile


