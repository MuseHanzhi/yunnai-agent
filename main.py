from plugins import (
    LogPlugin,
    ToolsPlugin,
    TTSPlugin
)
from src.application import Application
import sys

def main():
    main_app.add_plugin(
        LogPlugin(),
        ToolsPlugin(),
        TTSPlugin()
    )
    main_app.app_init()
    main_app.run()

main_app = Application(sys.argv)

if __name__ == '__main__':
    main()
