from .. import Plugin

class TTSPlugin(Plugin):
    def __init__(self):
        super().__init__('tts-service')
        self.application = None
    
    def app_before_initialize(self, app):
        self.application = app
