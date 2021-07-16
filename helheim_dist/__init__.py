import sys
if sys.platform == 'win32':
    from . import windows as helheim
elif sys.platform == 'linux':
    from . import linux as helheim
elif sys.platform == 'darwin':
    from . import darwin as helheim
