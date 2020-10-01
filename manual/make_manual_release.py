import sys

from pypocquant.manual import build_manual, build_quickstart

if __name__ == "__main__":
    build_manual()
    build_quickstart()

    sys.exit(0)