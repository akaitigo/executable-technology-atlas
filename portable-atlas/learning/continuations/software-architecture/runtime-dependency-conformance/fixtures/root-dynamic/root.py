import importlib
import core
def run():
    selected = importlib.import_module('adapter')
    port = selected.Adapter()
    return core.perform(port)
