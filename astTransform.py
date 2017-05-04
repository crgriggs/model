#!/usr/bin/env python
# -*- coding: utf-8 -*-
import ast, re
import networkx as nx
# import matplotlib.pyplot as plt
from sympy.abc import *
from sympy.logic import simplify_logic
from sympy import SOPform, bool_map, Or, And, Not, Xor
from ast import *

#Dictionary of what variables are tracked by state and how many bits they use
#Dictionaries that translate psuedocode into uclid mode, not sure if this is going to be human readabale
stateVars = {'rsp': '64', 'R11': '64', 'CR0' : '64', 'CS': '64', 'SS': '64', 'cs_selector': '16', 'cs_base': '32', 'cs_limit': '20', 'cs_accessRights': '12', 'CPL': '2', 'ss_selector': '16', 'ss_base': '32', 'ss_limit': '20', 'ss_accessRights': '12', 'EFER': '64', 'CR4': '64', 'rflags': '64', 'RCX': '64', 'RIP': '64'}
rflagsDict ={'CF': 'State.rflags # [0:0]', 'PF': 'State.rflags # [1:1]', 'AF': 'State.rflags # [4:4]', 'ZF': 'State.rflags # [6:6]', 'SF': 'State.rflags # [7:7]', 'TF': 'State.rflags # [8:8]', 'IF': 'State.rflags # [9:9]', 'DF': 'State.rflags # [10:10]', 'OF': 'State.rflags # [11:11]', 'IOPL': 'State.rflags # [13:12]', 'NT': 'State.rflags # [14:14]', 'RF': 'State.rflags # [16:16]', 'VM': 'State.rflags # [17:17]', 'AC': 'State.rflags # [18:18]', 'VIF': 'State.rflags # [19:19]', 'VIP': 'State.rflags # [20:20]', 'ID': 'State.rflags # [21:21]'}
CR0Dict = {'PE': 'State.CR0 # [0:0]', 'MP': 'State.CR0 # [1:1]', 'EM': 'State.CR0 # [2:2]', 'TS': 'State.CR0 # [3:3]', 'ET': 'State.CR0 # [4:4]', 'NE': 'State.CR0 # [5:5]', 'WP': 'State.CR0 # [16:16]', 'AM': 'State.CR0 # [18:18]','NW': 'State.CR0 # [29:29]', 'CD': 'State.CR0 # [30:30]', 'PG': 'State.CR0 # [31:31]'}
CR4Dict = {'VME': 'State.CR4 # [0:0]', 'PVI': 'State.CR4 # [1:1]', 'TSD': 'State.CR4 # [2:2]', 'DE': 'State.CR4 # [3:3]', 'PSE': 'State.CR4 # [4:4]', 'PAE': 'State.CR4 # [5:5]', 'MCE': 'State.CR4 # [6:6]', 'PGE': 'State.CR4 # [7:7]','PCE': 'State.CR4 # [8:8]', 'OSFXSR': 'State.CR4 # [9:9]', 'OSXMMEXCPT': 'State.CR4 # [10:10]', 'VMXE': 'State.CR4 # [13:13]', 'SMXE': 'State.CR4 # [14:14]', 'FSGSBASE': 'State.CR4 # [16:16]', 'PCIDE': 'State.CR4 # [17:17]', 'OSXSAVE': 'State.CR4 # [18:18]', 'SMEP': 'State.CR4 # [20:20]', 'SMAP': 'State.CR4 # [21:21]', 'PKE': 'State.CR4 # [22:22]'}
EFERDict = {'SCE': 'State.EFER # [0:0]', 'LME': 'State.EFER # [8:8]', 'LMA': 'State.EFER # [10:10]', 'NXE': 'State.EFER # [11:11]', 'SVME': 'State.EFER # [12:12]', 'LMSLE': 'State.EFER # [13:13]', 'FFXSR': 'State.EFER # [14:14]', 'TCE': 'State.EFER # [15:15]'}
cs_accessRightsDict = {'Type': 'State.cs_accessRights # [11:8]', 'S': 'State.cs_accessRights # [7:7]', 'DPL': 'State.cs_accessRights # [6:5]', 'P': 'State.cs_accessRights # [4:4]', 'AVL': 'State.cs_accessRights # [3:3]', 'L': 'State.cs_accessRights # [2:2]', 'D': 'State.cs_accessRights # [1:1]', 'B': 'State.cs_accessRights # [1:1]', 'G': 'State.cs_accessRights # [0:0]'}#, "SELECTOR": "State.cs_selector", "BASE": "State.cs_base", "LIMIT": "State.cs_limit"}
ss_accessRightsDict = {'Type': 'State.ss_accessRights # [11:8]', 'S': 'State.ss_accessRights # [7:7]', 'DPL': 'State.ss_accessRights # [6:5]', 'P': 'State.ss_accessRights # [4:4]', 'AVL': 'State.ss_accessRights # [3:3]', 'L': 'State.ss_accessRights # [2:2]', 'D': 'State.ss_accessRights # [1:1]', 'B': 'State.ss_accessRights # [1:1]', 'G': 'State.ss_accessRights # [0:0]'}#, "SELECTOR": "State.ss_selector", "BASE": "State.ss_base", "LIMIT": "State.ss_limit"}


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
        self.CS_SS = []
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
        rflags = False
        for var in self.varDict:

            if "CS." in var:
                cs = True
            elif "SS." in var:
                ss = True
            elif "rflags_" in var:
                rflags = True
        if cs:
                self.varDict["cs_accessRights0"] = [["( CS.Type ) @ ( CS.S ) @ ( CS.DPL ) @ ( CS.P ) @ ( CS.AVL ) @ ( CS.L ) @ ( CS.D ) @ ( CS.B ) @ ( CS.G )", None, self.currentNode]]
                if "cs_accessRights" in self.assignedToNode:
                    self.assignedToNode["cs_accessRights"].append(self.currentNode)
                else:
                    self.assignedToNode["cs_accessRights"] = [self.currentNode]
                self.assigned["cs_accessRights"] = 2
                for var in self.varDict:
                    if var[:3] == "CS." and var[3:] in cs_accessRightsDict:
                        self.assignedToNode[var[:-1]].append(self.currentNode)
        if ss:
                self.varDict["ss_accessRights0"] = [["( SS.Type ) @ ( SS.S ) @ ( SS.DPL ) @ ( SS.P ) @ ( SS.AVL ) @ ( SS.L ) @ ( SS.D ) @ ( SS.B ) @ ( SS.G )", None, self.currentNode]]
                if "ss_accessRights" in self.assignedToNode:
                    self.assignedToNode["ss_accessRights"].append(self.currentNode)
                else:
                    self.assignedToNode["ss_accessRights"] = [self.currentNode]
                self.assigned["ss_accessRights"] = 2
                for var in self.varDict:
                    if var[:3] == "SS." and var[3:] in cs_accessRightsDict:
                        self.assignedToNode[var[:-1]].append(self.currentNode)
        if rflags:
                self.varDict["rflags0"] = [["( 0 # [41:0] ) @ ( rflags_id ) @ ( rflags_vip ) @ ( rflags_vif ) @ ( rflags_ac ) @ ( rflags_vm ) @ ( rflags_rf ) @ ( b0 ) @ ( rflags_iopl ) @ ( rflags_of ) @ ( rflags_df ) @ ( rflags_if ) @ ( rflags_tf ) @ ( rflags_sf ) @ ( rflags_zf ) @ ( b0 ) @ ( rflags_af )@ ( b0 ) @ ( rflags_pf ) @ ( b0 ) @ ( rflags_cf )", None, self.currentNode]]
                self.assigned["rflags"] = 2
                if "rflags" in self.assignedToNode:
                    self.assignedToNode["rflags"].append(self.currentNode)
                else:
                    self.assignedToNode["rflags"] = [self.currentNode]
                self.assigned["rflags"] = 2
                for var in self.varDict:
                    if var[:-1] in rflagsDict:
                        self.assignedToNode[var[:-1]].append(self.currentNode)

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

    def visit_BinOp(self, node, condition = None):
        op = self.visit(node.op)
        left = self.visit(node.left)
        right = self.visit(node.right)
        return str(left) + " " + str(op) + " " + str(right)

    def visit_BoolOp(self, node, condition = None):
        op = []
        for value in node.values:
            op.append(self.visit(value))
        return str(" " +self.visit(node.op)+ " ").join(op)

    def visit_Attribute(self, node):
        return self.visit(node.value) + "." + node.attr

    def negate(self, comp):
        if len(comp.split()) < 4:
            if "== 1" in comp and "CPL" not in comp and "IOPL" not in comp:
                return comp.replace(" == 1", " == 0")
            if "== 0" in comp and "CPL" not in comp and "IOPL" not in comp:
                return comp.replace(" == 0", " == 1")
            if " > "  in comp:
                return comp.replace(" > ", " <= ")
            if " < "  in comp:
                return comp.replace(" < ", " >= ")
            if " = "  in comp:
                return comp.replace(" = ", " != ")
            if " >= "  in comp:
                return comp.replace(" >= ", " < ")
            if " <= "  in comp:
                return comp.replace(" <= ", " > ")
            if "==" in comp:
                return comp.replace(" == ", " != ")
            if "== 3" in comp and ("CPL" in comp or "IOPL" in comp):
                return comp.replace("==", "<")
        return comp
       
    def printBool(self, boo):
        parenCount = index = 0
        lis = []
        op = ""
        if boo.startswith("And"):
            op = " & "
            index = 4
        elif boo.startswith("Or"):
            op = " | "
            index = 3
        for runner in range(0, len(boo)):
            if "And" not in boo[index:] and "Or" not in boo[index:] and index <= 4:
                return op.join(boo[index:].replace("(", "").replace(")", "").replace(",", "").split())
            elif "And" not in boo[index:] and "Or" not in boo[index:]:
                lis.append(boo[index:].replace("(", "").replace(")", "").replace(",", ""))
                break
            elif boo[runner] == "(":

                parenCount += 1
            elif boo[runner] == ")":

                parenCount -= 1
            elif boo[runner] == "," and parenCount == 1:
                lis.append(self.printBool(boo[index:runner]))
                index = runner + 2
        return op.join(lis)        

    #negates boolean algebra
    def negateBool(self, comp):
        regex = r"([A-Za-z_])* [=<>!]* ([0-9A-Za-z_]*)*|[_A-Za-z]+"
        matches = re.finditer(regex, comp)
        matchDict = {}
        negDict = {}
        matchNum = 65
        for match in matches:
            if match.group()[:-2].rstrip() in negDict:
                if match.group()[-2:].lstrip() != negDict[match.group()[:-2].rstrip()][0]:
                    matchDict[match.group()] = "~" + negDict[match.group()[:-2].rstrip()][1]
            else:
                negDict[match.group()[:-2].rstrip()] = [match.group()[-2:].lstrip(), chr(matchNum)]
            if match.group() not in matchDict:
                matchDict[match.group()] = chr(matchNum)
                matchNum = matchNum + 1
        dictMatch = {}
        # print comp
        for var in matchDict:
            comp = comp.replace(var, matchDict[var])
            dictMatch[matchDict[var]] = var
        # print comp
        print self.printBool(str(simplify_logic(comp)))
        boo =  simplify_logic("~(" + comp + ")")
        neg = self.printBool(str(boo)) +  " "
        # print neg
        # print dictMatch
        for var in dictMatch:
            neg  = neg.replace("NotNot" + var + " ", var + " ")
            neg  = neg.replace("Not" + var + " ", self.negate(dictMatch[var]) + " ")
        # print neg
        # print
        return neg[:-1]

    #elif clauses don’t have a special representation in the AST, but rather appear as 
    #extra If nodes within the orelse section of the previous one.
    def visit_If(self, node, condition = None):
        parent = self.currentNode
        comparison = self.visit(node.test, condition)
        comparison = comparison.replace("StackAddrSize ==", "StackAddrSize =").replace("OperandSize ==", "OperandSize =")
        copy = comparison
        
        if condition != None:
            # print condition, comparison
            comparison = comparison + " & " + condition
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
            # print comparison, condition, self.negateBool(comparison)
            comparison = self.negateBool(copy) +" & (" + condition + ")"

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
            # print node.comparators
            comparison += " " + str(self.visit(node.comparators[i]))
        return comparison

    def visit_Num(self, node):
        return node.__dict__['n']

    def visit_Str(self, node):
        return node.s

    def visit_Assign(self, node, condition = None):
        lhs = str(self.visit(node.targets[0]))
        lhs = re.sub(r'Memory\[(.)*\]', "memory", lhs)
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
        
    def visit_Expr(self, node, conditional = None):
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
            if var == 'cs_accessRights':
                for var2 in cs_accessRightsDict:
                    var2 = "CS." + var2
                    if var2 in self.assignedToNode:
                        for n in self.assignedToNode[var2]:
                            WorkList.add(n)
            if var == 'ss_accessRights':
                for var3 in ss_accessRightsDict:
                    var3 = "SS." + var3
                    if var3 in self.assignedToNode:
                        for n in self.assignedToNode[var3]:
                            WorkList.add(n)
            #try to add to n by looking at where flags are assinged
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
        # print phiWithInput
        return phiWithInput

        #[lhs : [rhs, condtion, nodeWrittenTo]]

    def inSomeDict(self, word):
        temp = word
        if "." in word:
            word = word.split(".")[1]
            if word.upper() in rflagsDict:
                return True
            if word.upper() in CR0Dict:
                return True
            if word.upper() in CR4Dict:
                return True
            if word.upper() in EFERDict:
                return True
            if word in cs_accessRightsDict or word[3:] in cs_accessRightsDict:
                return True      
        return False

    def unSSA(self):
        phi = self.phiInput()
        newVD = {}
        phiDict = {}
        #creating a dict without the ssa encodings
        for var in self.varDict:
            if var.startswith("rflags_"):
                continue
            if var[-3:-1].lower() == "sp" and var[0].lower() != "r":
                continue
            if var[0:-1] in newVD:
                newVD[var[0:-1]].append(self.varDict[var][0][:])
            else:
                newVD[var[0:-1]] = self.varDict[var][:]
        #setting up the defines 
        #fragile to multiple phi functions
        #probably going to break
        #@todo make this more robust
        #maybe somehow use the descendants
        for var in self.varDict:
            if var[:-1] in phi and (self.varDict[var][0][2] in phi[var[:-1]][0][1]):            
                if var[0:-1] in phiDict:
                    phiDict[var[0:-1]][0].append(self.varDict[var][0])
                else:
                    phiDict[var[0:-1]] = [[self.varDict[var][0]]]
                #delete data in vardict
                if var[:-1] in newVD:
                    for i in range(0, len(newVD[var[:-1]])):
                        if self.varDict[var][0] == newVD[var[:-1]][i]:
                            wt = self.varDict[var][0][2]
                            newVD[var[:-1]].pop(i)
                            if newVD[var[:-1]] == []:
                                del newVD[var[0:-1]]
                                newVD[var[0:-1]] = [[var[:-1]+"_n", None, wt]]
                            break
            if self.inSomeDict(var[:-1]):
                if self.varDict[var][0][1] == None:
                    self.CS_SS.append(var[:-1] + " := " + self.varDict[var][0][0])
                if var[:-1] in newVD:
                    del newVD[var[:-1]]
        #changes the assigns to reference the new defines
        for var in newVD:
            for newVar in phiDict:
                newVD[var][0][0] = newVD[var][0][0].replace(newVar + " ", newVar + "_n ")
        self.varDict = newVD.copy()
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


