import glob
import importlib.util
import sys
import os
from .easyapi import api, logScript

extension_folder = os.path.dirname(os.path.realpath(__file__))

NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}

pyPath = os.path.join(extension_folder, 'easyapi')
sys.path.append(extension_folder)

logScript.log_wrap()
api.init()


def loadCustomNodes():
    files = glob.glob(os.path.join(pyPath, "*Node.py"), recursive=True)
    for file in files:
        name = os.path.splitext(file)[0]
        spec = importlib.util.spec_from_file_location(name, file)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
        if hasattr(module, "NODE_CLASS_MAPPINGS") and getattr(module, "NODE_CLASS_MAPPINGS") is not None:
            NODE_CLASS_MAPPINGS.update(module.NODE_CLASS_MAPPINGS)
            if hasattr(module, "NODE_DISPLAY_NAME_MAPPINGS") and getattr(module, "NODE_DISPLAY_NAME_MAPPINGS") is not None:
                NODE_DISPLAY_NAME_MAPPINGS.update(module.NODE_DISPLAY_NAME_MAPPINGS)


loadCustomNodes()

WEB_DIRECTORY = "./static"

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']
