import os

os.system("python psuedo.py psuedocode/mov.txt > models/mov.txt")
os.system("python psuedo.py psuedocode/add.txt > models/add.txt")
os.system("python psuedo.py psuedocode/adc.txt > models/adc.txt")
os.system("python psuedo.py psuedocode/dec.txt > models/dec.txt")
os.system("python psuedo.py psuedocode/out.txt > models/out.txt")
os.system("python psuedo.py psuedocode/and.txt > models/and.txt")
os.system("python psuedo.py psuedocode/inc.txt > models/inc.txt")
os.system("python psuedo.py psuedocode/wrmsr.txt > models/wrmsr.txt")
os.system("python psuedo.py psuedocode/push.txt > models/push.txt")
os.system("python psuedo.py psuedocode/pop.txt > models/pop.txt")
os.system("python psuedo.py psuedocode/sysret.txt > models/sysret.txt")
os.system("python psuedo.py psuedocode/syscall.txt > models/syscall.txt")
os.system("python createState.py models/")
os.system("/home/rhett/Documents/uclid/bin/uclid state.ucl > counterExample.txt")
os.system("python readCounterExample.py")