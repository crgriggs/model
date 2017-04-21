#!/usr/bin/env python
# -*- coding: utf-8 -*-
import ast, sys, tokenize, argparse, os, re
import networkx as nx
import matplotlib.pyplot as plt
from ast import *

#Dictionary of what variables are tracked by state and how many bits they use
#Dictionaries that translate psuedocode into uclid mode, not sure if this is going to be human readabale
inputs = set()
stateVars = {'R11': '64', 'CR0' : '64', 'CS': '64', 'SS': '64', 'cs_selector': '16', 'cs_base': '32', 'cs_limit': '20', 'cs_accessRights': '12', 'CPL': '2', 'ss_selector': '16', 'ss_base': '32', 'ss_limit': '20', 'ss_accessRights': '12', 'EFER': '64', 'CR4': '64', 'rflags': '64', 'RCX': '64', 'RIP': '64'}
rflagsDict ={'CF': 'State.rflags # [0:0]', 'PF': 'State.rflags # [1:1]', 'AF': 'State.rflags # [4:4]', 'ZF': 'State.rflags # [6:6]', 'SF': 'State.rflags # [7:7]', 'TF': 'State.rflags # [8:8]', 'IF': 'State.rflags # [9:9]', 'DF': 'State.rflags # [10:10]', 'OF': 'State.rflags # [11:11]', 'IOPL': 'State.rflags # [13:12]', 'NT': 'State.rflags # [14:14]', 'RF': 'State.rflags # [16:16]', 'VM': 'State.rflags # [17:17]', 'AC': 'State.rflags # [18:18]', 'VIF': 'State.rflags # [19:19]', 'VIP': 'State.rflags # [20:20]', 'ID': 'State.rflags # [21:21]'}
CR0Dict = {'PE': 'State.CR0 # [0:0]', 'MP': 'State.CR0 # [1:1]', 'EM': 'State.CR0 # [2:2]', 'TS': 'State.CR0 # [3:3]', 'ET': 'State.CR0 # [4:4]', 'NE': 'State.CR0 # [5:5]', 'WP': 'State.CR0 # [16:16]', 'AM': 'State.CR0 # [18:18]','NW': 'State.CR0 # [29:29]', 'CD': 'State.CR0 # [30:30]', 'PG': 'State.CR0 # [31:31]'}
CR4Dict = {'VME': 'State.CR4 # [0:0]', 'PVI': 'State.CR4 # [1:1]', 'TSD': 'State.CR4 # [2:2]', 'DE': 'State.CR4 # [3:3]', 'PSE': 'State.CR4 # [4:4]', 'PAE': 'State.CR4 # [5:5]', 'MCE': 'State.CR4 # [6:6]', 'PGE': 'State.CR4 # [7:7]','PCE': 'State.CR4 # [8:8]', 'OSFXSR': 'State.CR4 # [9:9]', 'OSXMMEXCPT': 'State.CR4 # [10:10]', 'VMXE': 'State.CR4 # [13:13]', 'SMXE': 'State.CR4 # [14:14]', 'FSGSBASE': 'State.CR4 # [16:16]', 'PCIDE': 'State.CR4 # [17:17]', 'OSXSAVE': 'State.CR4 # [18:18]', 'SMEP': 'State.CR4 # [20:20]', 'SMAP': 'State.CR4 # [21:21]', 'PKE': 'State.CR4 # [22:22]'}
EFERDict = {'SCE': 'State.EFER # [0:0]', 'LME': 'State.EFER # [8:8]', 'LMA': 'State.EFER # [10:10]', 'NXE': 'State.EFER # [11:11]', 'SVME': 'State.EFER # [12:12]', 'LMSLE': 'State.EFER # [13:13]', 'FFXSR': 'State.EFER # [14:14]', 'TCE': 'State.EFER # [15:15]'}
cs_accessRightsDict = {'Type': 'State.cs_accessRights # [11:8]', 'S': 'State.cs_accessRights # [7:7]', 'DPL': 'State.cs_accessRights # [6:5]', 'P': 'State.cs_accessRights # [4:4]', 'AVL': 'State.cs_accessRights # [3:3]', 'L': 'State.cs_accessRights # [2:2]', 'D': 'State.cs_accessRights # [1:1]', 'B': 'State.cs_accessRights # [1:1]', 'G': 'State.cs_accessRights # [0:0]'}#, "SELECTOR": "State.cs_selector", "BASE": "State.cs_base", "LIMIT": "State.cs_limit"}
ss_accessRightsDict = {'Type': 'State.ss_accessRights # [11:8]', 'S': 'State.ss_accessRights # [7:7]', 'DPL': 'State.ss_accessRights # [6:5]', 'P': 'State.ss_accessRights # [4:4]', 'AVL': 'State.ss_accessRights # [3:3]', 'L': 'State.ss_accessRights # [2:2]', 'D': 'State.ss_accessRights # [1:1]', 'B': 'State.ss_accessRights # [1:1]', 'G': 'State.ss_accessRights # [0:0]'}#, "SELECTOR": "State.ss_selector", "BASE": "State.ss_base", "LIMIT": "State.ss_limit"}
AMDDict = {'REAL_MODE': 'PE == 0', 'PROTECTED_MODE': '((PE == 1) && (VM == 0))','VIRTUAL_MODE': '((PE == 1) && (VM == 1))', 'LEGACY_MODE': '(LMA == 0)', 'LONG_MODE': '(LMA == 1)', '64BIT_MODE': '((LMA==1) && (cs_L == 1) && (cs_D == 0))','COMPATIBILITY_MODE': '(LMA == 1) && (cs_L == 0)', 'PAGING_ENABLED': '(PG == 1)', 'ALIGNMENT_CHECK_ENABLED': '((AM == 1) && (AC == 1) && (CPL == 3))'}
AMDrflagsDict ={'RFLAGS.CF': 'State.rflags # [0:0]', 'RFLAGS.PF': 'State.rflags # [1:1]', 'RFLAGS.AF': 'State.rflags # [4:4]', 'RFLAGS.ZF': 'State.rflags # [6:6]', 'RFLAGS.SF': 'State.rflags # [7:7]', 'RFLAGS.TF': 'State.rflags # [8:8]', 'RFLAGS.IF': 'State.rflags # [9:9]', 'RFLAGS.DF': 'State.rflags # [10:10]', 'RFLAGS.OF': 'State.rflags # [11:11]', 'RFLAGS.IOPL': 'State.rflags # [13:12]', 'RFLAGS.NT': 'State.rflags # [14:14]', 'RFLAGS.RF': 'State.rflags # [16:16]', 'RFLAGS.VM': 'State.rflags # [17:17]', 'RFLAGS.AC': 'State.rflags # [18:18]', 'RFLAGS.VIF': 'State.rflags # [19:19]', 'RFLAGS.VIP': 'State.rflags # [20:20]', 'RFLAGS.ID': 'State.rflags # [21:21]'}
accessRights = set(["ss_type", "ss_s", "ss_dpl", "ss_p", "ss_avl", "ss_g", "ss_l", "ss_d","ss_b", "cs_type", "cs_s", "cs_dpl", "cs_p", "cs_avl", "cs_g", "cs_l", "cs_d","cs_b"])

class fileConverter():

    def __init__(self, filename):
        self.filename = filename
    
    def convert(self):
        file = self.convertIntel(self.filename)
        return self.filename.split(".")[0] + "Python.txt"

    #converts intel psuedocode into python-esque syntax
    def convertIntel(self, filename):
        readFile = open(filename)
        outfile = filename.split(".")[0] + "Python.txt"
        writeFile = open(outfile, 'w+')
        numSpaces = 0
        for line in readFile:
            line = line.lstrip()
            #removing the trailing H on Hex number and adding "hex" to the beginning 
            #to bypass python's hate for variables that start with a num
            r = re.search(r'\b[0-9A-F]+H', line)
            if r != None:
                replace = r.group().replace("H", "")
                line = re.sub(r'\b[0-9A-F]+H', ("hex"+replace), line)
            if "≥" in line:
                line = line.replace("≥", ">=")
            if "=" in line: 
                line = line.replace(" = ", ' == ')
            if "←" in line:
                line = line.replace("←", "=")
            if "≠" in line:
                line = line.replace("≠", "!=")
            if ";" in line:
                line = line.replace(";", "")
            if " 1 " in line:
                line = line.replace(" 1 ", " b1 ")
            if " 0 " in line:
                line = line.replace(" 0 ", " b0 ")
            # if " 3 " in line:
            #     line = line.replace(" 3 ", " b1@b1 ")
            if "NOT" in line:
                line = line.replace("NOT", "~")
            if "AND" in line:
                line = line.replace("AND", "&")
            if "OR" in line:
                line = line.replace("OR", "|")
            if "operand size is 64-bit" in line:
                line = line.replace("operand size is 64-bit", "op64 == 1")
            if "RCX is not canonical" in line:
                line = line.replace("RCX is not canonical", "canon == 1")
            if "IF" in line and "THEN" in line:
                newLine = line.split("THEN")
                writeFile.write(" "*numSpaces + newLine[0].strip().replace("IF", "if") + ":\n")
                numSpaces += 4
                line = newLine[1].lstrip()
            if "#" in line:
                if "THEN" in line:
                    line = line.replace("THEN", "")
                line = "exitStatus = " + line.lstrip().replace("#", "").replace("(0)", "")
            if "*)" in line:
                line = line.replace("(*", "#")
                line = line.replace("*)", "")
            if line.lstrip().startswith("IF") and " = " not in line:

                if "#" in line:
                    newLine = line.split(" #")
                    writeFile.write(" "*numSpaces + newLine[0].strip().replace("IF", "if") + ": #" + newLine[1])
                else:
                    writeFile.write(" "*numSpaces + line.strip().replace("IF", "if") + ":\n")
                numSpaces += 4
            elif line.split(" #") == "THEN" or line.lstrip().startswith("END"):
                pass
            elif line.lstrip().startswith("THEN"):
                if "#" in line:
                    newLine = line.split(" #")
                    writeFile.write(" "*(numSpaces) + newLine[0].strip().replace("THEN", "#")  + newLine[1])
                else:
                    writeFile.write(" "*(numSpaces) + line.strip().replace("THEN", "") + "\n")
            elif line.lstrip().startswith("ELSE"):
                if "#" in line:
                    newLine = line.split(" #")
                    writeFile.write(" "*(numSpaces-4) + "else: #" + newLine[1])
                    newline = newLine[0].replace('ELSE', "")
                    if newline != "":
                        writeFile.write(" "*(numSpaces) + newline)
                else:
                    writeFile.write(" "*(numSpaces-4) + "else:\n")
                    newline = line.replace('ELSE', "").strip()
                    if newline != "":
                        writeFile.write(" "*(numSpaces) + newline +"\n")
            elif line.lstrip().startswith("FI"):
                numSpaces -= 4
            else:
                endFI = False
                if "FI" in line:
                    line  = line.replace("FI", "")
                    endFI = True
                writeFile.write(" "*numSpaces + line.lstrip())
                if endFI:
                    numSpaces -= 4
        return outfile

    #removes AMD's shorthand
    def AMDshorthand(self, line):
        newLine = ''
        i = 0
        while line[i] == " " or line[i] ==["\t"]:
            newLine += line[i]
            i += 1
        for word in line.split():
            # if word in AMDDict:
            #     word = AMDDict[word]
            newLine += word
        return newLine

    #AMD sometimes seperates conditionals across two lines
    #but if it does there are unmatching parens e.g. ((( ))
    #lparens += 1 & rparens -= 1
    def hasOddParens(self, line):
        parens = 0
        for char in line:
            if char == "(":
                parens += 1
            if char == ")":
                parens -= 1
        if parens > 0:
            return True
        return False

    #converts AMD's psuedocode into python-esque syntax
    def convertAMD(self, filename):
        readFile = open(filename)
        outfile = filename.split(".")[0] + "Python.txt"
        writeFile = open(outfile, 'w+')
        numSpaces = 0
        doubleLine = ""
        comment = ""
        for line in readFile:
            if doubleLine != "":
                line = doubleLine + line
                if comment != "":
                    line += ": " + comment
                    comment = ""
                else:
                    line +=":"
                doubleLine = ""

          

            if "(" in line:
                line = line.replace("(", "( ")
                line = line.replace(")", " )")
            line = AMDshorthand(line)
            if "ELSE" in line:
                line = line.replace("ELSE", "else")
                line += ":"
            if "&&" in line:
                line = line.replace("&&", "and")
            if "||" in line:
                line = line.replace("||", "or")
            if "{" in line or "}" in line or line.strip() == "\n":
                continue
            if "EXCEPTION[" in line:
                line = line.replace("EXCEPTION[#", "exitStatus = ")
                line = line.replace("(0)]", "")
            if "ELSIF" in line:
                line = line.replace("ELSIF", "elif")
                if hasOddParens(line):
                    if "//" in line:
                        line = line.split("//")
                        comment += "#" + line[1]
                        line = line[0]
                    doubleLine += line
                    continue
                else:
                    line += ":"
            if line.lstrip().startswith("IF"):
                line = line.replace("IF", "if")
                if hasOddParens(line):
                    if "//" in line:
                        line = line.split("//")
                        comment += "#" + line[1]
                        line = line[0]
                    doubleLine += line
                    continue
                else:
                    line += ":"
            if line == "":
                continue
            writeFile.write(line+"\n")
        return outfile

#traverses the ast pushing all the vars into varDict in the 
#form key -> var = next[var] value -> case
class astVisit(ast.NodeVisitor):

    def __init__(self, node):
        self.varDict = {}
        self.numAssignInBlock = 0
        self.cfg = nx.DiGraph()
        self.cfg.add_node(0)
        self.currentNode = 0
        self.exitPointNodes = {}
        self.assigned = {}
        self.phiDict = {}
        self.assignedToNode = {}
        self.visit(node)
        self.selectorHandle()
        self.unSSA()
        self.addingExitPoints()

    #if any part of the cs/ss selector is changed, then
    #we only want one assign instead of multiple for 
    #each part, so we add an assign for those values at the last node
    def selectorHandle(self):
        cs = False
        ss = False
        for var in self.varDict:
            if "CS." in var:
                cs = True
            elif "SS." in var:
                ss = True
        if cs:
                self.varDict["cs_accessRights0"] = [["(CS.TYPE) @ (CS.S) @ (CS.DPL) @ (CS.P) @ (CS.AVL) @ (CS.L) @ (CS.D) @ (CS.B) @ (CS.G)", None, self.currentNode]]
                self.assignedToNode["cs_accessRights"] = [self.currentNode]
                self.assigned["cs_accessRights"] = 2
        if ss:
                self.varDict["ss_accessRights0"] = [["(SS.TYPE) @ (SS.S) @ (SS.DPL) @ (SS.P) @ (SS.AVL) @ (SS.L) @ (SS.D) @ (SS.B) @ (SS.G)", None, self.currentNode]]
                self.assignedToNode["ss_accessRights"] = [self.currentNode]
                self.assigned["ss_accessRights"] = 2

    def visit(self, node, conditional = None):
        """Visit a node."""
        method = 'visit_' + node.__class__.__name__
        visitor = getattr(self, method, self.generic_visit)
        if conditional != None:
            return visitor(node, conditional)
        return visitor(node)


    def generic_visit(self, node, conditional = None):
        if conditional == None:
            ast.NodeVisitor.generic_visit(self, node)
        else:
            ast.NodeVisitor.generic_visit(self, node, conditional)

    #basic terminals
    def visit_Name(self, node):
        return str(node.id)

    def visit_Eq(self, node):
        return "=="

    def visit_NotEq(self, node):
        return "!="

    def visit_Lt(self, node):
        return "<"

    def visit_LtE(self, node):
        return "<="

    def visit_Gt(self, node):
        return ">"

    def visit_GtE(self, node):
        return ">="

    def visit_Is(self, node):
        return ""

    def visit_IsNot(self, node):
        return ""

    def visit_In(self, node):
        return ""

    def visit_NotIn(self, node):
        return ""

    def visit_And(self, node):
        return "&"

    def visit_Or(self, node):
        return "|"
    
    def visit_Add(self, node):
       return "+"

    def visit_Sub(self, node):
       return "-"

    def visit_Mul(self, node):
       return "*"
    
    def visit_Div(self, node):
       return "/"

    def visit_BitAnd(self, node):
        return "&&"

    def visit_BitOr(self, node):
        return "||"

    def visit_Invert(self, node):
        return "!!"

    def visit_Slice(self, node):
        return "[" + str(self.visit(node.lower)) + ':' + str(self.visit(node.upper)) + "]"

    def visit_Index(self, node):
        return "[" + str(self.visit(node.value)) + "]"

    def visit_Subscript(self, node):
        return str(self.visit(node.value) + self.visit(node.slice))

    def visit_UnaryOp(self, node):
        return str(self.visit(node.op)) + str(self.visit(node.operand))

    def visit_BinOp(self, node):
        op = self.visit(node.op)
        left = self.visit(node.left)
        right = self.visit(node.right)
        return str(left) + " " + str(op) + " " + str(right)

    def visit_BoolOp(self, node, condition = None):
        op = []
        for value in node.values:
            op.append(self.visit(value))
        return "( " + str(" " +self.visit(node.op)+ " ").join(op) + " )"

    def negateBool(expr):
        expr = expr.strip()
        if "and" in expr:
            exprs = expr.split
        if ">" in expr:
            if "=" in expr:
                expr = expr.split(">=")



    def visit_Attribute(self, node):
        return self.visit(node.value) + "." + node.attr
    #def If(test, body, orelse)
    #An if statement. test holds a single node, such as a Compare node. body and orelse 
    #each hold a list of nodes.

    def negate(self, comp):
        if len(comp.split()) < 4:

            if "== 1" in comp and "CPL" not in comp:
                return comp.replace("== 1", "== 0")
            if "== 0" in comp and "CPL" not in comp:
                return comp.replace("== 0", "== 1")
            if ">"  in comp:
                return comp.replace(">", "<=")
            if "<"  in comp:
                return comp.replace("<", ">=")
            if ">="  in comp:
                return comp.replace(">=", "<")
            if "<="  in comp:
                return comp.replace("<=", ">")
        return comp

    #elif clauses don’t have a special representation in the AST, but rather appear as 
    #extra If nodes within the orelse section of the previous one.
    def visit_If(self, node, condition = None):
        parent = self.currentNode
        comparison = self.visit(node.test, condition)
        copy = comparison
        if condition != None:
            # print condition, comparison
            comparison = comparison + " && " + condition
            # print condition, comparison
        #pushes the condition down the true part of the if block

        self.cfg.add_node(self.currentNode + 1)
        self.cfg.add_edge(self.currentNode, self.currentNode + 1)
        self.currentNode += 1
        ifNode = self.currentNode
        self.numAssignInBlock = 0
        for nodes in node.body:
            self.visit(nodes, comparison)
        #pushes the negation of the condition down the else/elif of the if block
        if condition != None:
            # print condition, comparison
            comparison = "!!(" + comparison +" && " + copy + ")"
            # print condition, comparison

        if len(node.orelse) > 0:
            self.currentNode += 1
            elseNode = self.currentNode
            self.cfg.add_node(elseNode)
            self.numAssignInBlock = 0
            self.cfg.add_edge(parent, elseNode)
            for nodes in node.orelse:
                self.visit(nodes, self.negate(comparison))
            self.currentNode += 1
            self.cfg.add_node(self.currentNode)
            self.cfg.add_edge(ifNode, self.currentNode)
            self.cfg.add_edge(elseNode, self.currentNode)
            self.numAssignInBlock = 0
        else:
            self.currentNode += 1
            self.cfg.add_node(self.currentNode)
            self.cfg.add_edge(ifNode, self.currentNode)
            self.cfg.add_edge(parent, self.currentNode)


    def visit_Compare(self, node, conditional = None):
        comparison = ''
        comparison += str(self.visit(node.left))
        for i in range(0, len(node.ops)):
            comparison += " " + self.visit(node.ops[i])
            comparison += " " + str(self.visit(node.comparators[i]))
        return comparison


    def visit_Num(self, node):
        return node.__dict__['n']

    def visit_Str(self, node):
        return node.s

    def visit_Assign(self, node, condition = None):
        lhs = str(self.visit(node.targets[0]))
        if lhs in self.assignedToNode:
            self.assignedToNode[lhs].append(self.currentNode)
        else:
            self.assignedToNode[lhs] = [self.currentNode]
        rhs =  str(self.visit(node.value))
        if lhs == "exitStatus":
            self.exitPointNodes[self.currentNode] = rhs
        if lhs in self.assigned:
            lhs += str(self.assigned[lhs])
            self.assigned[lhs[0:-1]] = self.assigned[lhs[0:-1]] + 1
        else:
            lhs += "0"
            self.assigned[lhs[0:-1]] = 1
        if lhs in self.varDict:
            self.varDict[lhs].append([rhs, condition, self.currentNode])
        else:
            self.varDict[lhs] = [[rhs, condition, self.currentNode]]
        self.cfg.node[self.currentNode][self.numAssignInBlock] = lhs + " = " + rhs
        self.numAssignInBlock += 1
        return lhs + " = " + rhs
        
    def visit_Expr(self, node):

        ast.NodeVisitor.generic_visit(self, node)

    def dominates(self, a, b):
        for path in nx.all_simple_paths(self.cfg, source=0, target=b):
            if b not in path:
                return False
        return True

    def findIdom(self, v):
        if v == 0:
            return 0
        if len(self.cfg.predecessors(v)) > 1:
            for p in self.cfg.predecessors(v):
                return self.findIdom(p)
        if self.cfg.predecessors(v) != []:
            return self.cfg.predecessors(v)[0]
        return []

    def strictlyDominates(self, a, b):
        if a == b:
            return False
        for path in nx.all_simple_paths(self.cfg, source=0, target=b):
            if b not in path:
                return False
        return True

    def dominanceFrontier(self):
        df = {}
        for node in self.cfg:
            if len(self.cfg.predecessors(node)) > 1:
                for pred in self.cfg.predecessors(node):
                    runner = pred
                    while runner != self.findIdom(node):
                        if runner in df:
                            df[runner].add(node)
                        else:
                            df[runner] = {node}
                        runner = self.findIdom(runner)

        return df

    def phi(self):
        DF = self.dominanceFrontier()
        print DF

        phi = {}
        for var in self.varDict:
            if self.assigned[var[0:-1]] < 2:
                continue
            #removiing the ssa index
            #assumes no more than 10 writes
            var = var[0:-1]
            WorkList = set()
            EverOnWorkList = set()
            AlreadyHasPhiFunc = set()
            for n in self.assignedToNode[var]:
                WorkList.add(n)
            EverOnWorkList = WorkList.copy()
            while WorkList:
                n = WorkList.pop()               
                if n not in DF:
                    continue
                for d in DF[n]:
                    if d not in AlreadyHasPhiFunc:
                        #print var, d
                        if var in phi:
                            if d not in phi[var]:
                                phi[var].append(d)
                        else:
                            phi[var] = [d]
                        AlreadyHasPhiFunc.add(d)
                        if d not in EverOnWorkList:
                            if d in DF:
                                WorkList.add(d)
                            EverOnWorkList.add(d)

        return phi
         
    #finds the node where var was last written
    #assumes var has been written before
    def findAncestorWrite(self, node, var):
        if node in self.assignedToNode[var]:
            return node
        else:
            for pred in self.cfg.predecessors(node):
                return self.findAncestorWrite(pred, var)

    def phiInput(self):
        phi = self.phi()
        phiWithInput = {}
        for var in phi:
            inputs = set()
            for node in phi[var]:
                for pred in self.cfg.predecessors(node):
                    inputs.add(self.findAncestorWrite(pred, var))
                if var in phiWithInput:
                    if None in inputs:
                        inputs.remove(None)
                    phiWithInput[var].append([node, inputs])
                else:
                    if None in inputs:
                        inputs.remove(None)
                    phiWithInput[var] = [[node, inputs]]
        return phiWithInput

        #[lhs : [rhs, condtion, nodeWrittenTo]]

    def unSSA(self):
        phi = self.phiInput()
        newVD = {}
        phiDict = {}
        for var in self.varDict:
            #if the var is in the right hand side and after the phi function for this var
            if (var[0:-1] + " ") in self.varDict[var][0][0] and var[0:-1] in phi and self.varDict[var][0][2] >= phi[var[0:-1]][0][0]:
                #need to loop through newVD to find the assigns that determine the phi function
                write = self.varDict[var][0][2]
                inputs = self.varDict[var]
                inputLoc = phi[var[0:-1]]
                for i in range(0, len(newVD[var[0:-1]])):
                    if newVD[var[0:-1]][i][2] in inputLoc[0][1]:
                        inputs.append(newVD[var[0:-1]][i])
                if var[0:-1] in phiDict:
                    phiDict[var[0:-1]].append(inputs)
                else:
                    phiDict[var[0:-1]] = [inputs]
                #delete data in vardict
                del newVD[var[0:-1]]
                # add new data
                newVD[var[0:-1]] = [[var[0:-1]+"_n", None, write]]
            elif var[3:-1] in cs_accessRightsDict or var[3:-1] in ss_accessRightsDict:
                continue
            elif var[0:-1] in newVD:
                newVD[var[0:-1]].append(self.varDict[var][0])
            else:
                newVD[var[0:-1]] = self.varDict[var]
        self.varDict = newVD
        self.phiDict = phiDict

    def addingExitPoints(self):
        for exitNode in self.exitPointNodes:
            descendant = nx.descendants(self.cfg, exitNode)
            for var in self.varDict:
                for define in self.varDict[var]:
                    if define[2] in descendant:
                        if define[1] == None:
                            define[1] = "next[exitStatus] != " + self.exitPointNodes[exitNode] 
                        else:
                            define[1] = define[1] + " & next[exitStatus] != " + self.exitPointNodes[exitNode] 


                
class modulePrint():

    def __init__(self, filename, varDict, phi):
        self.filename = filename
        self.inputs = set()
        self.constants = set()
        self.defines = set()
        self.cvd = varDict
        self.phi = phi
    
    def findInputs(self):
        file = open(self.filename)
        self.defines.add("b0 := 0x0 # [0:0];")
        self.defines.add("b1 := 0x1 # [0:0];")
        for line in file:
            line = re.sub(r'\b[0-9]+', "", line)
            line = re.sub(r'\b[A-F]+H', "", line)
            line = line.replace("exitStatus", "")
            line = line.replace("GP", "")
            line = line.replace("!", "")
            line = line.replace("&", "")
            line = line.replace("~", "")
            line = line.replace("UD", "")
            line = line.replace("else", "")
            line = line.replace(":", "")
            line = line.replace("elif(", "")
            line = line.replace("and", " ")
            line = line.replace(" or ", " ")
            line = line.replace(")", (" "))
            line = line.replace("if(", "")
            line = line.replace("(", " ")
            line = line.replace(")", (" "))
            line = line.replace("<", (" "))
            line = line.replace("=", (" "))
            line = line.replace(">", (" "))
            line = line.replace("+", (" "))
            line = line.replace("[]", "")
            if "#" in line:
                line = line.split("#")[0]
            # if "=" in line:
            #     line = line.split("=")[1]
            for word in line.split():
                word = word.strip()
                if word in AMDDict:
                    self.defines.add(word + " := " + AMDDict[word])
                elif word.upper() in rflagsDict:
                    self.inputs.add("rflags")
                    self.defines.add(word + " := " + rflagsDict[word.upper()])
                elif word in AMDrflagsDict:
                    self.inputs.add("rflags")
                    self.defines.add(word + " := " + AMDrflagsDict[word])
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
        #{var : [[phiVar, inputVar, inputVar...]+]}
        #var -> [rhs, condtion, nodeWrittenTo]]
        for var in self.phi:
            count = 0
            groupCount = 0
            for group in self.phi[var]:
                temp = ""
                for inputs in group:
                    #need to save the first as it needs to be printed after
                    if inputs == [group][groupCount][0]:
                        temp = [group][groupCount][0]
                    #the first needs to set up the case statement
                    elif inputs == [group][groupCount][1]:
                        print var + str(count) + " := case"
                        print "    " + [group][groupCount][1][1] + " : " + [group][groupCount][1][0] + ";"
                    #the last needs to close the case state
                    elif inputs == [group][groupCount][-1]:
                        print "    " + [group][groupCount][-1][1] + " : " + [group][groupCount][-1][0] + ";"
                        print "    default : State." + var
                        print "esac;"
                    #regular part of the case
                    else:
                        print "    " + inputs[1] + " : " + inputs[0] + ";" 
                print
                #if it's the last time we will call it var_n so the assign section can reference
                #otherwise it's just given a number
                if group == self.phi[var][-1]:
                    print var + "_n := " + temp[0].replace(var, var + str(count)) + ";"
                    print
                else:
                    print var + str(count+1)+  " := " +temp[0].replace(var, var + str(count)) + ";"
                    print
                    count += 2
            groupCount += 1
        for define in self.defines:
            print define

    def printConsts(self):
        print
        print "CONST"
        for con in self.constants:
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
                if var in accessRights:
                    if ss:
                        ss = False
                        print "ss_accessRights : [12];"
                    continue
            elif "CS" in var:
                var = var.replace(".", "_").lower()
                if var in accessRights:
                    if cs:
                        cs = False
                        print "cs_accessRights : [12];"
                    continue 
            elif var == 'exitStatus':
                continue
            elif var == 'DEST':
                print "DEST : [64];" 
            elif var.startswith("RFLAGS") or var in rflagsDict:
                if rflags:
                    rflags = False
                    print "rflags : [64];"
            else:
                print str(var) + " : [" + str(stateVars[var]) + "];"

    def printCS(self, cs):
        B = True
        csDict = {'TYPE': '(State.cs_accessRights # [11:8])', 'S': '(State.cs_accessRights # [7:7])', 'DPL': '(State.cs_accessRights # [6:5])', 'P': '(State.cs_accessRights # [4:4])', 'AVL': '(State.cs_accessRights # [3:3])', 'L': '(State.cs_accessRights # [2:2])', 'D': '(State.cs_accessRights # [1:1])', 'B': '(State.cs_accessRights # [1:1])', 'G': '(State.cs_accessRights # [0:0])'}
        for assign in cs:
            if assign[0][3:] == "D":
                B = False
            csDict[assign[0][3:].upper()] = "(next[" + assign[0] + "])"
        if B:
            sentence = str(csDict['TYPE']) + " @ " +  str(csDict['S']) + " @ " + str(csDict['DPL']) + " @ " + str(csDict['P']) + " @ " + str(csDict['AVL']) + " @ " + str(csDict['L']) + " @ " + str(csDict['B']) + " @ " + str(csDict['G']) + ";"
        else:
            sentence = str(csDict['TYPE']) + " @ " +  str(csDict['S']) + " @ " + str(csDict['DPL']) + " @ " + str(csDict['P']) + " @ " + str(csDict['AVL']) + " @ " + str(csDict['L']) + " @ " + str(csDict['D']) + " @ " + str(csDict['G']) + ";"
        print "init[cs_accessRights] := 0;"
        print "next[cs_accessRights] := " + sentence;

    def printSS(self, ss):
        B = True
        ssDict = {'TYPE': '(State.ss_accessRights # [11:8])', 'S': '(State.ss_accessRights # [7:7])', 'DPL': '(State.ss_accessRights # [6:5])', 'P': '(State.ss_accessRights # [4:4])', 'AVL': '(State.ss_accessRights # [3:3])', 'L': '(State.ss_accessRights # [2:2])', 'D': '(State.ss_accessRights # [1:1])', 'B': '(State.ss_accessRights # [1:1])', 'G': '(State.ss_accessRights # [0:0])'}
        for assign in ss:
            if assign[0][3:] == "D":
                B = False
            ssDict[assign[0][3:].upper()] = "(next[" + assign[0] + "])"
        if B:
            sentence = str(ssDict['TYPE']) + " @ " +  str(ssDict['S']) + " @ " + str(ssDict['DPL']) + " @ " + str(ssDict['P']) + " @ " + str(ssDict['AVL']) + " @ " + str(ssDict['L']) + " @ " + str(ssDict['B']) + " @ " + str(ssDict['G']) + ";"
        else:
            sentence = str(ssDict['TYPE']) + " @ " +  str(ssDict['S']) + " @ " + str(ssDict['DPL']) + " @ " + str(ssDict['P']) + " @ " + str(ssDict['AVL']) + " @ " + str(ssDict['L']) + " @ " + str(ssDict['D']) + " @ " + str(ssDict['G']) + ";"
        print "init[ss_accessRights] := 0;"
        print "next[ss_accessRights] := " + sentence;

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

    def connectState(self, rhsCombo):
        # print var
        rhs = rhsCombo[0]
        cond = rhsCombo[1]
        temp = []
        for token in rhs.split(" "):
            if token in stateVars:
                temp.append("State." + token)
            else:
                temp.append(self.inSomeDict(token))
            rhs = (" ".join(temp))
        if cond != None:
            temp = []
            for token in cond.split(" "):
                if token in stateVars:
                    temp.append("State." + token)
                else:
                    temp.append(self.inSomeDict(token))
            cond = (" ".join(temp))
        
        # print var[0], var1, var2
        return [rhs, cond]

   

    #[lhs : [rhs, condtion, nodeWrittenTo]]
    def printAssign(self):
        printed = set()
        ss = []
        cs = []
        print
        tab = "    "
        print "ASSIGN"
        print
        for var in self.cvd:
            if(var in printed):
                continue
            else:
                printed.add(var)
            lhs = var
            rhsCond = self.cvd[lhs]
            if var == "exitStatus":
                default = "normal" 
                init = "normal"
            else:
                init = 0
                default = "State." + var
            # var = self.connectState(var)
            if var.lower() in accessRights:
                if "cs" in var[:3].lower():
                    cs.append(var)
                else:
                    ss.append(var)
            #unconditionally assigning a value aka no condition
            if len(rhsCond) == 1 and rhsCond[0][1] == None and exit == False:
                print "init[" + var + "] := 0;"
                print "next[" + var + "] := " + str(rhsCond[0][0]) + ";"
                print
            #otherwise there must at least one condition/rhs combo
            else:
                print "init[" + var + "] := 0;"
                print "next[" + var + "] := case"
                for rhsCondCombo in rhsCond:
                    # rhsCondCombo = self.connectState(rhsCondCombo)
                    print tab + rhsCondCombo[1] + " : " + rhsCondCombo[0].replace(" 3", " b1@b1").replace("hex", "") + ";"
                print tab + "default : " + default + ";"
                print "esac;"
                print

        if cs != []:
            print "uyaausd"
            self.printCS(cs)
            print
        if ss != []:
            self.printSS(ss)

    def write(self):
        if "/" in self.filename:
            filename = self.filename.split("/")[-1]
        else:
            filename = self.filename
        print "MODULE "+ filename.replace("Python.txt", "")
        self.findInputs()
        self.printInput()
        self.printVar()
        self.printConsts()
        self.printDefine()
        self.printAssign()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('filename',
                    help='psuedocode file to model')
    parser.add_argument("-k", '--keep', action="store_true",
                    help='keeps the intermediate language file')
    parser.add_argument("-ip",'--interPrint', action='store_true',
                    help='Prints the intermediate python syntax')
    args = parser.parse_args()


    fc = fileConverter(filename = args.filename)
    #fc = fileConverter(filename = "psuedocode/sysret.txt")
    filename = fc.convert()
    print filename
    f = open(filename, 'r')
    fstr = f.read()
    f.close()
    if args.interPrint:
        print fstr
    v = astVisit(parse(fstr, filename=filename))

    # print list(v.cfg.predecessors(7))

    # nx.draw_shell(nx.convert_node_labels_to_integers(v.cfg),  with_labels=True)
    # plt.show()
    # writer = modulePrint(varDict = v.varDict, filename = filename, phi = v.phiDict)
    # writer.write()
    if not args.keep:
        os.system("rm " + filename)
   
