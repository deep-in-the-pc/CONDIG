rmdir PySERT /S /q
C:\Users\deman\AppData\Local\Programs\Python\Python37-32\Scripts\pyinstaller.exe -n PySERT --onefile --windowed -i C:\Users\deman\PycharmProjects\CONDIG\pyserticon.ico C:\Users\deman\PycharmProjects\CONDIG\main.py
mkdir PySERT
move dist\PySERT.exe PySERT
copy pyserticon.ico PySERT
mkdir PySERT\dados
rmdir __pycache__ /S /q
rmdir build /S /q
rmdir dist /S /q
