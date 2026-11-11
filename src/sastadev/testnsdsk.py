import os


chapathname = r'D:\Dropbox\jodijk\Utrecht\Projects\SASTADATA\NSDSK\indata'
xmlpathname = r'D:\Dropbox\jodijk\Utrecht\Projects\SASTADATA\NSDSK\intreebanks'


chafilenames = os.listdir(chapathname)
xmlfilenames = os.listdir(xmlpathname)

chabasefilenames = [fn[:-3].lower() for fn in chafilenames]
xmlbasefilenames = [fn[:-3].lower() for fn in xmlfilenames]

for chabasefilename in chabasefilenames:
    if chabasefilename not in xmlbasefilenames:
        print(f'Missing xml file: {chabasefilename}')

for xmlbasefilename in xmlbasefilenames:
    if xmlbasefilename not in chabasefilenames:
        print(f'Missing cha file: {xmlbasefilename}')