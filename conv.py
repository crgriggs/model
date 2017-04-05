stateVars = {'CRO' : '64', 'EFER': '64','CS': '64', 'SS': '64', 'cs_selector': '16', 'cs_base': '32', 'cs_limit': '20', 'cs_accessRights': '12', 'cpl': '2', 'ss_selector': '16', 'ss_base': '32', 'ss_limit': '20', 'ss_accessRights': '12', 'EFER': '64', 'CR4': '64', 'rflags': '64', 'rcx': '64', 'rip': '64'}
CR0Dict = {'PE': 'State.CR0 # [0:0]', 'MP': 'State.CR0 # [1:1]', 'EM': 'State.CR0 # [2:2]', 'TS': 'State.CR0 # [3:3]', 'ET': 'State.CR0 # [4:4]', 'NE': 'State.CR0 # [5:5]', 'WP': 'State.CR0 # [16:16]', 'AM': 'State.CR0 # [18:18]','NW': 'State.CR0 # [29:29]', 'CD': 'State.CR0 # [30:30]', 'PG': 'State.CR0 # [31:31]'}
CR4Dict = {'VME': 'State.CR4 # [0:0]', 'PVI': 'State.CR4 # [1:1]', 'TSD': 'State.CR4 # [2:2]', 'DE': 'State.CR4 # [3:3]', 'PSE': 'State.CR4 # [4:4]', 'PAE': 'State.CR4 # [5:5]', 'MCE': 'State.CR4 # [6:6]', 'PGE': 'State.CR4 # [7:7]','PCE': 'State.CR4 # [8:8]', 'OSFXSR': 'State.CR4 # [9:9]', 'OSXMMEXCPT': 'State.CR4 # [10:10]', 'VMXE': 'State.CR4 # [13:13]', 'SMXE': 'State.CR4 # [14:14]', 'FSGSBASE': 'State.CR4 # [16:16]', 'PCIDE': 'State.CR4 # [17:17]', 'OSXSAVE': 'State.CR4 # [18:18]', 'SMEP': 'State.CR4 # [20:20]', 'SMAP': 'State.CR4 # [21:21]', 'PKE': 'State.CR4 # [22:22]'}
EFERDict = {'SCE': 'State.EFER # [0:0]', 'LME': 'State.EFER # [8:8]', 'LMA': 'State.EFER # [10:10]', 'NXE': 'State.EFER # [11:11]', 'SVME': 'State.EFER # [12:12]', 'LMSLE': 'State.EFER # [13:13]', 'FFXSR': 'State.EFER # [14:14]', 'TCE': 'State.EFER # [15:15]'}
cs_accessRightsDict = {'TYPE': 'State.cs_accessRights # [11:8]', 'S': 'State.cs_accessRights # [7:7]', 'DPL': 'State.cs_accessRights # [6:5]', 'P': 'State.cs_accessRights # [4:4]', 'AVL': 'State.cs_accessRights # [3:3]', 'L': 'State.cs_accessRights # [2:2]', 'D': 'State.cs_accessRights # [1:1]', 'B': 'State.cs_accessRights # [1:1]', 'G''D': 'State.cs_accessRights # [0:0]'}
inputs = set()
consts = []
cs = """State.cs_selector : BITVEC[16];
State.cs_base : BITVEC[32];
State.cs_limit : BITVEC[20];
(*Access Rights Makeup*)
(*type -> [11:8], s -> [7:7], dpl -> [6:5], p -> [4:4], avl -> [3:3], l -> [2:2], db -> [1:1], g -> [0:0]*)
State.cs_accessRights : BITVEC[12];"""

ss = """State.ss_selector : BITVEC[16];
State.ss_base : BITVEC[32];
State.ss_limit : BITVEC[20];
(*Access Rights Makeup*)
(*type -> [11:8], s -> [7:7], dpl -> [6:5], p -> [4:4], avl -> [3:3], l -> [2:2], db -> [1:1], g -> [0:0]*)
State.ss_accessRights : BITVEC[12];"""

def processDefine(line):
		endParens = False
		i = 0
		while line[i] == "\t":
			print("\t"),
			i += 1
		for word in line.split():
			if word[0] == '(':
				word = word[1:]
				print("("),
			if word[-1] == ')':
				word = word.replace(")", "")
				endParens = True
			if word.startswith("IA32_EFER"):
				word = word[9:]
			if word.startswith("cs_"):
				word = word[3:].upper()
			if word in CR0Dict:
				word = CR0Dict[word]
			if word in CR4Dict:
				word = CR4Dict[word]
			if word in EFERDict:
				word = EFERDict[word]
			if word in cs_accessRightsDict:
				word = cs_accessRightsDict[word]
			print(word),
			if endParens:
				print(")"),
				endParens = False
		print

def processConst(line):

	newLine = line.split()
	if newLine == []:
		return
	word = newLine[0]
	#Use initialize constants from state if possible 
	if word[-2:] == "_I":
		word = word.replace("_I", "")
	#Use the efer special register
	# if word[5:8] == "EFER"
	# 	word = 'EFER'
	if word in stateVars:
		inputs.add(word)
	elif word in CR0Dict:
		inputs.add("CRO")
	elif word in CR4Dict:
		inputs.add("CR4")
	elif word in EFERDict:
		inputs.add("EFER")
	else:
		consts.append([word, newLine[2]])

def printConsts():
	print "CONST"
	for pair in consts:
		print str(pair[0]) + " : " + str(pair[1]) 

def printInputs():
	print "INPUT"
	for key in inputs:
		print "State." + str(key) + " : BITVEC[" + str(stateVars[key]) +"];"

def processVar(line):
	if line.startswith("cs"):
		print cs
	elif line.startswith("ss"):
		print ss
	else:
		print line

def processAssign(line):
	word = ''
	i = 0
	if line.startswith("init[") or line.startswith("next["):
		i = 5
		while line[i] != "]":
			word += line[i]
			i += 1
		if line.startswith("init["):
			if word == "exitStatus":
				print "init[" + str(word)  + "] : normal;"
			else:
				print "init[" + str(word)  + "] : 0x0;"
	elif line.startswith("\tdefault"):
		newLine = line.split()
		if newLine[2].rstrip(";") in stateVars:
			print "\t" + newLine[0] + " : State." + newLine[2]
	else:
		print line

def processFile(filename):
	const = False
	var = False
	define = False
	assign = False
	file = open(filename)
	for line in file:
		if line.startswith("CONST"):
			const = True
			continue
		elif line.startswith("(*** MODULE ***)"):
			const = False
			continue
		elif line.startswith("MODULE"):
			print line
			const = False
			printInputs()
			printConsts()
			continue
		elif line.startswith("VAR"):
			print line
			var = True
			continue
		elif line.startswith("DEFINE"):
			const = False
			print line
			var = False
			define = True
			continue
		elif line.startswith("ASSIGN"):
			print line
			define = False
			assign = True
			continue
		elif line.startswith("(*** CONTROL ***)"):
			quit()
		if const:
			processConst(line)
		if var:
			processVar(line)
		if define:
			processDefine(line)
		if assign:
			processAssign(line)

processFile('ex.txt')
