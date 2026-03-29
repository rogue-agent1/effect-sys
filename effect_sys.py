#!/usr/bin/env python3
"""effect_sys - Algebraic effect system with handlers."""
import sys

class Effect:
    def __init__(self, name, *args):
        self.name = name
        self.args = args
    def __repr__(self):
        return f"Effect({self.name}, {self.args})"

class Handler:
    def __init__(self):
        self.handlers = {}

    def on(self, effect_name, fn):
        self.handlers[effect_name] = fn
        return self

    def handle(self, effect):
        if effect.name in self.handlers:
            return self.handlers[effect.name](*effect.args)
        raise ValueError(f"Unhandled effect: {effect.name}")

class EffectRunner:
    def __init__(self):
        self.handler_stack = []

    def push_handler(self, handler):
        self.handler_stack.append(handler)
        return self

    def pop_handler(self):
        return self.handler_stack.pop()

    def perform(self, effect):
        for handler in reversed(self.handler_stack):
            if effect.name in handler.handlers:
                return handler.handle(effect)
        raise ValueError(f"No handler for effect: {effect.name}")

    def run(self, fn):
        return fn(self)

def test():
    log = []
    h = Handler()
    h.on("log", lambda msg: log.append(msg))
    h.on("read", lambda key: {"name": "Alice", "age": "30"}.get(key, ""))

    runner = EffectRunner()
    runner.push_handler(h)
    runner.perform(Effect("log", "hello"))
    runner.perform(Effect("log", "world"))
    assert log == ["hello", "world"]
    name = runner.perform(Effect("read", "name"))
    assert name == "Alice"
    inner_h = Handler()
    inner_h.on("log", lambda msg: log.append(f"[INNER] {msg}"))
    runner.push_handler(inner_h)
    runner.perform(Effect("log", "test"))
    assert log[-1] == "[INNER] test"
    val = runner.perform(Effect("read", "age"))
    assert val == "30"
    runner.pop_handler()
    runner.perform(Effect("log", "outer"))
    assert log[-1] == "outer"
    state = [0]
    state_h = Handler()
    state_h.on("get", lambda: state[0])
    state_h.on("set", lambda v: state.__setitem__(0, v))
    runner2 = EffectRunner()
    runner2.push_handler(state_h)
    assert runner2.perform(Effect("get")) == 0
    runner2.perform(Effect("set", 42))
    assert runner2.perform(Effect("get")) == 42
    print("All tests passed!")

if __name__ == "__main__":
    test() if "--test" in sys.argv else print("effect_sys: Algebraic effects. Use --test")
