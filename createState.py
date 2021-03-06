#!/usr/bin/env python
import sys, os


def append_file(f, filename):
    """Writes file "filename" to file descriptor f."""
    f.write("(*----- " + filename + " -----*)\n")
    f.write(open(filename).read())
    f.write('\n')

def findInstrVars(stateVars, gprs, propType):
    for filename in os.listdir("./" + str(propType)):
        reachVars = False
        for line in open("./" + str(propType)+"/"+filename):
            if line.strip() == "VAR":
                reachVars = True
            if line.strip() == "CONST":
                reachVars = False
            if not reachVars:
                continue
            if " : " in line:
                var = line.split(" : ")[0]
                if var in stateVars.keys():
                    stateVars[var].append(filename.replace(".txt", ""))
                if var == "DEST" and "out" not in filename:
                    for gpr in gprs:
                        stateVars["r"+gpr+"x"].append(filename.replace(".txt", ""))



def main():

    if len(sys.argv) == 2:
        propType = sys.argv[1]
    else:
        print "Enter folder that handles current property"
        return -1

    if not os.path.isdir("./" + str(propType)):
        print str(propType) + "is not a folder in the current directory"
        return -1

    f = open("state.ucl", 'w+')
    try:
        #opcode
        #    Go through each modeled instruction find the name of that instruction and add it to opcode
        #        Exception instruction added seperately
        opcodes = []
        for filename in os.listdir("./" + str(propType)):
            opcodes.append(filename.replace(".txt", ""))
        f.write("MODEL StateModel\n")
        f.write("\n")
        f.write("typedef opcodes : enum{" + ", ".join(opcodes) + "};\n")
        f.write("typedef exitCase : enum {GP, UD, Normal};\n")
        f.write("typedef register : enum {a, b, c, d};\n")
        f.write("typedef cacheType : enum {uncacheable, cacheable, writeBack};\n")
        f.write("typedef size : enum {bits64, bits32, bits16};\n")
        f.write("\n")
        f.write("CONST\n")
        f.write("isCanonical : PRED[1]; (* Predicate to decide whether is canonical or not *)\n")
        for filename in os.listdir("./" + str(propType)):
            if filename.endswith(".txt"):
                append_file(f, "./" + str(propType)+"/"+filename)
        stateVars = {'exitStatus' : [], 'rsp' : [],'ss_limit' : [], 'ss_selector' : [],  'rax' : [], 'rbx' : [], 'rcx' : [], 'rdx' : [], 'rflags' : [], 'r11' : [], 'ss_base' : [], 'ss_accessRights' : [], 'EFER' : [], 'cs_base' : [], 'rip' : [], 'cs_selector' : [], 'cs_limit' : [], 'cpl' : [], 'cs_accessRights' : [], 'CR0' : [], 'CR4' : [] }
        gprs = {'a', 'b', 'c', 'd'}
        #as of now an unpriviliged instruction can write to a single gpr during any one execution step
        unpriv = {"mov", 'pop', 'push', 'add', 'adc', 'and', 'dec', 'inc'}
        append_file(f, "state/vars.txt")
        f.write("\n")
        findInstrVars(stateVars, gprs, propType)
        for var in stateVars:
            f.write("\n")
            if var == "exitStatus":
                f.write("\n")
                f.write("init[exceptionThrown] := false;\n")
                f.write("next[exceptionThrown] := case\n")
                for op in stateVars[var]:
                    f.write("    opcode = "+ op + " & " + op + "Instr."  + var + " != Normal : true;\n")
                f.write("    default : exceptionThrown;\n")
                f.write("esac;\n")
                continue
            f.write("init["+var+"] := " + var + "_i;\n")
            if stateVars[var] == []:
                f.write("next["+var+"] := " + var + ";\n")
                f.write("\n")
                continue
            f.write("next["+var+"] := case\n")
            for op in stateVars[var]:
                if op in unpriv and var[1] in gprs:
                    f.write("    ~exceptionThrown & opcode = " + op +" & currentReg = " + var[1] + " : next[" + op + "Instr.DEST];\n")
                else:
                    f.write("    ~exceptionThrown & opcode = " + op +" : next[" + op + "Instr."  + var + "];\n")
            f.write("    default : " + var + ";\n")
            f.write("esac;\n")
            

        f.write("\n")
        f.write("(* ----- CONTROL MODULE ----- *)\n")
        f.write("\n")
        f.write("CONTROL\n")
        f.write("\n")
        f.write("EXTVAR\n")
        f.write("\n")
        f.write("opcode : opcodes := {" + ", ".join(opcodes) + "};\n")
        f.write("\n")
        append_file(f, "state/control.txt")
    except:
        f.close()
        raise

    return 0

if __name__ == "__main__":
    sys.exit(main())
