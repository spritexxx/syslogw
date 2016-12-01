from cx_Freeze import setup, Executable

includefiles = ['templates/', 'static/']
includes = ['zope.interface', 'service_identity']
excludes = ['Tkinter']

base = None

setup(
    name = 'syslogw',
    version = '0.1',
    description = 'syslog collector & web viewer',
    author = 'Simon Esprit',
    author_email = 'simon.esprit@gmail.com',
    options = {'build_exe': {'excludes':excludes,'include_files':includefiles, 'includes':includes}},
    executables = [Executable('syslogw.py', base=base)]
)