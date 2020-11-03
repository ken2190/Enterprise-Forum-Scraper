import sys
if sys.platform == 'win32':
    from .windows import helheim
elif sys.platform == 'linux':
    from .linux import helheim
elif sys.platform == 'darwin':
    from .darwin import helheim
