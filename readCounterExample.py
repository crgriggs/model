ready = False
opcodeDict = {0 : "sysret", 1 : "push", 2 : "mov", 3 : "pop", 4 : "syscall"}
exitStatusDict = {0 : "GP", 1 : "UD", 2: "Normal"}
for line in open("counterExample.txt"):
	if line.strip() != "Part 2 : Counter Example Trace":
		ready = True
	if ready:
		if "::" in line:
			print "+---------------------+"
			print line.strip() 
			print "+---------------------+"
		if "State.rcx" in line and "_i" not in line and "evaluating" not in line:
			print "RCX : " + str(int(line.split(":=")[1].strip(), 2))
		if "State.rsp" in line and "_i" not in line and "evaluating" not in line:
			print "RSP : " + str(int(line.split(":=")[1].strip(), 2))
		if "State.cpl" in line and "_i" not in line and "evaluating" not in line and "," not in line:
			print "CPL : " + str(int(line.split(":=")[1].strip(), 2))
		if "opcode:=" in line and "ITE" not in line and "the" not in line:
			print "Opcode : " + opcodeDict[int(line.split(":=")[1].strip(), 2)]
		if "exitStatus" in line and "," not in line and "evaluating" not in line:
			if "sysret" in line:
				print "Sysret Exit Status: "   +  exitStatusDict[int(line.split(":=")[1].strip(), 2)]
			else:
				print "Syscall Exit Status: "   +  exitStatusDict[int(line.split(":=")[1].strip(), 2)]