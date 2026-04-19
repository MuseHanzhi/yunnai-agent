from src.types.lfecycle_hooks import Hooks
from .plugin import IPCTiming

class HookRegistry:
    def hook(self, hook_name: Hooks, timing: IPCTiming):
        def decorator(func):
            setattr(func, "_hook_name", hook_name)
            setattr(func, "_hook_timing", timing)
            return func
        return decorator
    
    def on_app_before_initialize(self, timing: IPCTiming = "before"):
        return self.hook("on_app_before_initialize", timing)
    
    def on_app_after_initialized(self, timing: IPCTiming = "before"):
        return self.hook("on_app_after_initialized", timing)
    
    def on_app_will_close(self, timing: IPCTiming = "before"):
        return self.hook("on_app_will_close", timing)
    
    def on_ready(self, timing: IPCTiming = "before"):
        return self.hook("on_ready", timing)

    def on_llm_response(self, timing: IPCTiming = "before"):
        return self.hook("on_llm_response", timing)
    
    def on_message_after_sended(self, timing: IPCTiming = "before"):
        return self.hook("on_message_after_sended", timing)
    
    def on_message_before_send(self, timing: IPCTiming = "before"):
        return self.hook("on_message_before_send", timing)

registry = HookRegistry()
