import os

os.system("python psuedo.py psuedocode/mov.txt > models/mov.txt")
os.system("python psuedo.py psuedocode/push.txt > models/push.txt")
os.system("python psuedo.py psuedocode/pop.txt > models/pop.txt")
os.system("python psuedo.py psuedocode/sysret.txt > models/sysret.txt")
os.system("python psuedo.py psuedocode/syscall.txt > models/syscall.txt")
os.system("python createState.py models/")