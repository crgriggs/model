# -*- coding: utf-8 -*-
import re

stateVars = {'R11': '64', 'CR0' : '64', 'CS': '64', 'SS': '64', 'cs_selector': '16', 'cs_base': '32', 'cs_limit': '20', 'cs_accessRights': '12', 'CPL': '2', 'ss_selector': '16', 'ss_base': '32', 'ss_limit': '20', 'ss_accessRights': '12', 'EFER': '64', 'CR4': '64', 'rflags': '64', 'RCX': '64', 'RIP': '64'}
rflagsDict ={'CF': 'State.rflags # [0:0]', 'PF': 'State.rflags # [1:1]', 'AF': 'State.rflags # [4:4]', 'ZF': 'State.rflags # [6:6]', 'SF': 'State.rflags # [7:7]', 'TF': 'State.rflags # [8:8]', 'IF': 'State.rflags # [9:9]', 'DF': 'State.rflags # [10:10]', 'OF': 'State.rflags # [11:11]', 'IOPL': 'State.rflags # [13:12]', 'NT': 'State.rflags # [14:14]', 'RF': 'State.rflags # [16:16]', 'VM': 'State.rflags # [17:17]', 'AC': 'State.rflags # [18:18]', 'VIF': 'State.rflags # [19:19]', 'VIP': 'State.rflags # [20:20]', 'ID': 'State.rflags # [21:21]'}
CR0Dict = {'PE': 'State.CR0 # [0:0]', 'MP': 'State.CR0 # [1:1]', 'EM': 'State.CR0 # [2:2]', 'TS': 'State.CR0 # [3:3]', 'ET': 'State.CR0 # [4:4]', 'NE': 'State.CR0 # [5:5]', 'WP': 'State.CR0 # [16:16]', 'AM': 'State.CR0 # [18:18]','NW': 'State.CR0 # [29:29]', 'CD': 'State.CR0 # [30:30]', 'PG': 'State.CR0 # [31:31]'}
CR4Dict = {'VME': 'State.CR4 # [0:0]', 'PVI': 'State.CR4 # [1:1]', 'TSD': 'State.CR4 # [2:2]', 'DE': 'State.CR4 # [3:3]', 'PSE': 'State.CR4 # [4:4]', 'PAE': 'State.CR4 # [5:5]', 'MCE': 'State.CR4 # [6:6]', 'PGE': 'State.CR4 # [7:7]','PCE': 'State.CR4 # [8:8]', 'OSFXSR': 'State.CR4 # [9:9]', 'OSXMMEXCPT': 'State.CR4 # [10:10]', 'VMXE': 'State.CR4 # [13:13]', 'SMXE': 'State.CR4 # [14:14]', 'FSGSBASE': 'State.CR4 # [16:16]', 'PCIDE': 'State.CR4 # [17:17]', 'OSXSAVE': 'State.CR4 # [18:18]', 'SMEP': 'State.CR4 # [20:20]', 'SMAP': 'State.CR4 # [21:21]', 'PKE': 'State.CR4 # [22:22]'}
EFERDict = {'SCE': 'State.EFER # [0:0]', 'LME': 'State.EFER # [8:8]', 'LMA': 'State.EFER # [10:10]', 'NXE': 'State.EFER # [11:11]', 'SVME': 'State.EFER # [12:12]', 'LMSLE': 'State.EFER # [13:13]', 'FFXSR': 'State.EFER # [14:14]', 'TCE': 'State.EFER # [15:15]'}
cs_accessRightsDict = {'Type': 'State.cs_accessRights # [11:8]', 'S': 'State.cs_accessRights # [7:7]', 'DPL': 'State.cs_accessRights # [6:5]', 'P': 'State.cs_accessRights # [4:4]', 'AVL': 'State.cs_accessRights # [3:3]', 'L': 'State.cs_accessRights # [2:2]', 'D': 'State.cs_accessRights # [1:1]', 'B': 'State.cs_accessRights # [1:1]', 'G': 'State.cs_accessRights # [0:0]'}#, "SELECTOR": "State.cs_selector", "BASE": "State.cs_base", "LIMIT": "State.cs_limit"}
ss_accessRightsDict = {'Type': 'State.ss_accessRights # [11:8]', 'S': 'State.ss_accessRights # [7:7]', 'DPL': 'State.ss_accessRights # [6:5]', 'P': 'State.ss_accessRights # [4:4]', 'AVL': 'State.ss_accessRights # [3:3]', 'L': 'State.ss_accessRights # [2:2]', 'D': 'State.ss_accessRights # [1:1]', 'B': 'State.ss_accessRights # [1:1]', 'G': 'State.ss_accessRights # [0:0]'}#, "SELECTOR": "State.ss_selector", "BASE": "State.ss_base", "LIMIT": "State.ss_limit"}
           
class modulePrint():

    def __init__(self, filename, varDict, phi, CS_SS):
        self.filename = filename
        self.inputs = set()
        self.constants = set()
        self.defines = set()
        self.cvd = varDict
        self.phi = phi
        self.CS_SS = CS_SS
    
    def findInputs(self):
        file = open(self.filename)
        self.defines.add("b0 := 0x0 # [0:0];")
        self.defines.add("b1 := 0x1 # [0:0];")
        for line in file:
            # print line
            line = re.sub(r'\b[0-9]+', "", line)
            line = re.sub(r'hex?([0-9]*[A-F]*)*', "", line)
            line = line.replace("exitStatus", "")
            line = line.replace("GP", "")
            line = line.replace("!", "")
            line = line.replace("-", "")
            line = line.replace("&", "")
            line = line.replace("~", "")
            line = line.replace("UD", "")
            line = line.replace("else", "")
            line = line.replace(":", "")
            line = line.replace("elif(", "")
            line = line.replace(" and ", " ")
            line = line.replace(" or ", " ")
            line = line.replace(")", (" "))
            line = line.replace("if(", "")
            line = line.replace("if (", "")
            line = line.replace("(", " ")
            line = line.replace(")", (" "))
            line = line.replace("<", (" "))
            line = line.replace("=", (" "))
            line = line.replace(">", (" "))
            line = line.replace("|", " ")
            line = line.replace("+", (" "))
            line = line.replace("[]", "")
            line = line.replace(" if ", "")
            if line.lstrip()[:3] == "if ":
                line = line.replace("if", "")
            if "#" in line:
                line = line.split("#")[0]
            for word in line.split():
                word = word.strip()
                if word[7:].upper() in rflagsDict:
                    self.inputs.add("rflags")
                    self.defines.add(word + " := " + rflagsDict[word[7:].upper()])
                elif "EFER" in word or word in EFERDict:
                    self.inputs.add("EFER")
                    self.defines.add(word + " := " + EFERDict[word.replace("EFER", "").replace("IA32_.", "")])
                elif word.startswith("cs_") or word.startswith("CS.") or word in cs_accessRightsDict:
                    #removing the cs_ or CS. and capitilizing the rest
                    if word not in cs_accessRightsDict:
                        word = word[3:].upper()
                    self.inputs.add("cs_selector")
                    self.inputs.add("cs_base")
                    self.inputs.add("cs_limit")
                    self.inputs.add("cs_accessRights")
                elif word.startswith("ss_") or word.startswith("SS.") or word in ss_accessRightsDict:
                    #removing the ss_ or SS. and capitilizing the rest
                    if word not in ss_accessRightsDict:
                        word = word[3:].upper()
                    self.inputs.add("ss_selector")
                    self.inputs.add("ss_base")
                    self.inputs.add("ss_limit")
                    self.inputs.add("ss_accessRights")
                elif word in CR0Dict or "CR0" in word:
                    self.inputs.add("CR0")
                    self.defines.add(word + " := " + CR0Dict[word.replace("CR0.", "")])
                elif word in CR4Dict or "CR4" in word:
                    self.inputs.add("CR4")
                    self.defines.add(word + " := " + CR4Dict[word.replace("CR4.", "")])
                elif word.upper() in stateVars:
                    self.inputs.add(word.upper())
                elif word.lower() in stateVars:
                    self.inputs.add(word.lower())
                      #Handling the register bitpacking
                elif len(word) == 3 and "X" == word[2]:
                    self.defines.add(word + " := State.R" + word[1:] + " # [31:0];" )
                elif len(word) == 2 and "X" == word[1]:
                    self.defines.add(word + " := State.R" + word[1:] + " # [15:0];" )
                else:
                    self.constants.add(word)

    def printInput(self):
        print
        print "INPUT"
        print
        for key in self.inputs:
            print "State." + str(key) + " : BITVEC[" + str(stateVars[key]) +"];"

    def printDefine(self):
        print
        print "DEFINE"
        print 
        for define in self.defines:
            print define
        for define in self.CS_SS:
            print define
        print
        #{var : [[phiVar, inputVar, inputVar...]+]}
        #var -> [rhs, condtion, nodeWrittenTo]]

        for var in self.phi:
            count = 0
            groupCount = 0
            for group in self.phi[var]:
                # print "group: " + str(group)
                temp = ""
                for inputs in group:
                    # print "input: " + str(inputs)
                    #the first needs to set up the case statement
                    if inputs == [group][groupCount][0]:
                        print var + str(count) + " := case"
                        print "    " + inputs[1] + " : " + inputs[0] + ";"
                    #the last needs to close the case state
                    elif inputs == [group][groupCount][-1]:
                        print "    " + inputs[1] + " : " + inputs[0] + ";"
                        if self.inSomeDict(var) != var:
                            print "    default : " + self.inSomeDict(var)
                        else:
                            if var != "exitStatus":
                                print "    default : State." + var.lower().replace(".", "_")
                            else:
                                print "    default : Normal;"
                        print "esac;"
                    #regular part of the case
                    else:
                        print "    " + inputs[1] + " : " + inputs[0] + ";" 
                print
                #if it's the last time we will call it var_n so the assign section can reference
                #otherwise it's just given a number
                if group == self.phi[var][-1]:
                    print var + "_n := " + var + str(groupCount) + ";"
                    print
                else:
                    print var + str(count+1)+  " := "+ var + str(groupCount) +  ";"
                    print
                    count += 2
            groupCount += 1

    def printConsts(self):
        print
        print "CONST"
        for con in self.constants:
            if "_is_" in con:
                 print con + ": BITVEC[1];"
            else:
                print con + ": BITVEC[64];"

    def printVar(self):
        rflags = True
        cs = True
        ss = True
        print
        print "VAR"
        for var in self.cvd:
            if "SS" in var:
                var = var.replace(".", "_").lower()
                if var[3:] in ss_accessRightsDict:
                    if ss:
                        ss = False
                        print "ss_accessRights : [12];"
                        continue
            if "CS" in var:
                var = var.replace(".", "_").lower()
                if var[3:] in cs_accessRightsDict:
                    if cs:
                        cs = False
                        print "cs_accessRights : [12];"
                        continue 
            if var == 'exitStatus':
                continue
            elif var == 'DEST':
                print "DEST : [64];" 
            elif var.upper().startswith("RFLAGS") or var in rflagsDict:
                if rflags:
                    rflags = False
                    print "rflags : [64];"
            else:
                print str(var) + " : [" + str(stateVars[var]) + "];"

    def inSomeDict(self, word):
        temp = word
        if "." in word:
            word = word.split(".")[1]
            if word.upper() in rflagsDict:
                return rflagsDict[word.upper()]
            if word.upper() in CR0Dict:
                return CR0Dict[word.upper()]
            if word.upper() in CR4Dict:
                return CR4Dict[word.upper()]
            if word.upper() in EFERDict:
                return EFERDict[word.upper()]
            if word.upper() in cs_accessRightsDict:
                return cs_accessRightsDict[word.upper()]
            if word.upper() in ss_accessRightsDict:
                return ss_accessRightsDict[word.upper()]
        return temp

    #[lhs : [rhs, condtion, nodeWrittenTo]]
    def printAssign(self):
        print
        print "ASSIGN"
        print
        for var in self.cvd:
            lhs = var
            rhsCond = self.cvd[lhs]
            #handling the cs. or ss.
            if "." in lhs:
                lhs = lhs.lower().replace(".", "_")
            if var == "exitStatus":
                default = "normal" 
                init = "normal"
            else:
                init = "0"
                default = "State." + lhs
            #unconditionally assigning a value aka no condition
            if len(rhsCond) == 1 and rhsCond[0][1] == None:
                print "init[" + lhs + "] := "+ init + ";"
                print "next[" + lhs + "] := " + str(rhsCond[0][0]) + ";"
                print
            #otherwise there must at least one condition/rhs combo
            else:
                print "init[" + lhs + "] := 0;"
                print "next[" + lhs + "] := case"
                for rhsCondCombo in rhsCond:
                    # rhsCondCombo = self.connectState(rhsCondCombo)
                    print "    " + rhsCondCombo[1] + " : " + rhsCondCombo[0].replace("hex", "") + ";"
                print "    " + "default : " + default + ";"
                print "esac;"
                print

    def write(self):
        if "/" in self.filename:
            filename = self.filename.split("/")[-1]
        else:
            filename = self.filename
        print "MODULE "+ filename.replace("intermediateindentinter.txt", "")
        self.findInputs()
        self.printInput()
        self.printVar()
        self.printConsts()
        self.printDefine()
        self.printAssign()