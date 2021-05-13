import sys
if sys.platform == 'win32':
    from .windows import helheim, isChallenge
elif sys.platform == 'linux':
    from .linux import helheim, isChallenge
elif sys.platform == 'darwin':
    from .darwin import helheim, isChallenge
