from plugins import LogPlugin
from src.application import Application
import sys

def main():
    main_app\
        .add_plugin(LogPlugin())\
        .run()

main_app = Application(sys.argv)

if __name__ == '__main__':
    main()
