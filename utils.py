
# Effetti per il terminale
BOLD = '\x1b[1m'
BLUE = '\x1b[34m'
CYAN = '\x1b[36m'
OFF = '\x1b[0m'
DEF_FOREGROUND = '\x1b[39m'


def blue(string: str) -> str:
    return f"{BLUE}{string}{DEF_FOREGROUND}"


def bold(string: str) -> str:
    return f"{BOLD}{string}{OFF}"


def cyan(string: str) -> str:
    return f"{CYAN}{string}{DEF_FOREGROUND}"
