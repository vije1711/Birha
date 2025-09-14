import sys,re
p='''1.1.0_birha.py'''
start=1464;end=1496
with open(p,'r',encoding='utf-8') as f:
    for i,line in enumerate(f,1):
        if i>=start and i<=end:
            s=line.encode('unicode_escape').decode('ascii')
            print(f"{i:04d}: {s}")
