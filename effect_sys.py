#!/usr/bin/env python3
"""effect_sys - Algebraic effects with handlers and resumptions."""
import sys, argparse

class Effect:
    def __init__(self, name, value=None): self.name = name; self.value = value
    def __repr__(self): return f"Effect({self.name}, {self.value})"

class Resume(Exception):
    def __init__(self, value=None): self.value = value; super().__init__()

class EffectHandler:
    def __init__(self): self.handlers = {}

    def handle(self, effect_name, handler_fn):
        self.handlers[effect_name] = handler_fn; return self

    def run(self, computation):
        try: return computation(self._perform)
        except Resume as r: return r.value

    def _perform(self, effect):
        if effect.name in self.handlers:
            return self.handlers[effect.name](effect.value, lambda v: v)
        raise RuntimeError(f"Unhandled effect: {effect.name}")

class StatefulHandler(EffectHandler):
    def __init__(self, initial=None):
        super().__init__(); self.state = initial
        self.handle("get", lambda _, k: k(self.state))
        self.handle("put", lambda v, k: self._set(v, k))
    def _set(self, v, k): self.state = v; return k(None)

class LogHandler(EffectHandler):
    def __init__(self):
        super().__init__(); self.logs = []
        self.handle("log", lambda msg, k: self._log(msg, k))
    def _log(self, msg, k): self.logs.append(msg); return k(None)

class ExceptionHandler(EffectHandler):
    def __init__(self):
        super().__init__()
        self.handle("throw", lambda e, k: ("error", e))
        self.handle("try", lambda comp, k: self._try(comp, k))
    def _try(self, comp, k):
        try: return k(comp(self._perform))
        except Exception as e: return ("error", str(e))

def main():
    p = argparse.ArgumentParser(description="Algebraic effect system")
    p.add_argument("--demo", action="store_true")
    args = p.parse_args()
    if args.demo:
        print("=== State Effect ===")
        sh = StatefulHandler(0)
        def counter(perform):
            for i in range(5):
                v = perform(Effect("get"))
                perform(Effect("put", v + 1))
            return perform(Effect("get"))
        print(f"Counter: {sh.run(counter)}")

        print("\n=== Log Effect ===")
        lh = LogHandler()
        def logged(perform):
            perform(Effect("log", "Starting"))
            result = 42
            perform(Effect("log", f"Result: {result}"))
            perform(Effect("log", "Done"))
            return result
        print(f"Result: {lh.run(logged)}")
        print(f"Logs: {lh.logs}")

        print("\n=== Combined ===")
        class Combined(EffectHandler):
            def __init__(self):
                super().__init__()
                self.state = 0; self.logs = []
                self.handle("get", lambda _, k: k(self.state))
                self.handle("put", lambda v, k: self._put(v, k))
                self.handle("log", lambda m, k: self._log(m, k))
            def _put(self, v, k): self.state = v; return k(None)
            def _log(self, m, k): self.logs.append(m); return k(None)

        ch = Combined()
        def combined_comp(perform):
            perform(Effect("log", "init"))
            perform(Effect("put", 10))
            v = perform(Effect("get"))
            perform(Effect("log", f"state={v}"))
            return v
        print(f"Result: {ch.run(combined_comp)}, state={ch.state}, logs={ch.logs}")
    else: p.print_help()

if __name__ == "__main__":
    main()
