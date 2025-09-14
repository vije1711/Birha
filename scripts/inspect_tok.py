import re
p='''1.1.0_birha.py'''
with open(p,'r',encoding='utf-8') as f:
    txt=f.read()
idx=txt.find("s = re.sub(r\"[??]\\\", \"\", s)")
print('found at', idx)
# find the line and print codepoints around the bracket
for line in txt.splitlines():
    if 's = re.sub(r"[' in line:
        if 's = re.sub(r"[??]", "", s)' in line:
            pat=line
            print('LINE:', line)
            # extract between [ and ]
            start=line.find('[')+1
            end=line.find(']')
            chars=line[start:end]
            print('chars:', chars, [hex(ord(c)) for c in chars])
