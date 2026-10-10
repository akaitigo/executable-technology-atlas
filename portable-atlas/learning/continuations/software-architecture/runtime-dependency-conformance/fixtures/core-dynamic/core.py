import importlib
def perform():
    selected = importlib.import_module('adapter')
    port = selected.Adapter()
    return port.add(2, 3)
