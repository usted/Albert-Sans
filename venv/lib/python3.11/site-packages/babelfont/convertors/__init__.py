import os
import sys
import pkgutil
import inspect
import importlib
from babelfont import Font

class BaseConvertor:
    suffix = ".XXX"

    @classmethod
    def can_load(self, other, **kwargs):
        return other.filename.endswith(self.suffix)

    @classmethod
    def can_save(self, other, **kwargs):
        return other.filename.endswith(self.suffix)

    @classmethod
    def load(cls, convertor):
        self = cls()
        self.font = Font()
        # Pass on information to child
        self.filename = convertor.filename
        self.scratch = convertor.scratch
        return self._load()

    @classmethod
    def save(cls, obj, convertor, **kwargs):
        self = cls()
        self.font = obj
        # Pass on information to child
        self.filename = convertor.filename
        self.scratch = convertor.scratch
        return self._save()

class Convert:
    convertors = []

    @classmethod
    def _load_convertors(cls):
        if cls.convertors:
            return
        convertorpath = os.path.join(
            os.path.dirname(sys.modules[cls.__module__].__file__)
        )
        # Additional plugin path here?
        loaders = pkgutil.iter_modules([convertorpath])
        for loader, module_name, is_pkg in loaders:
            if is_pkg:
                continue
            spec = loader.find_spec(module_name)
            _module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(_module)
            classes = [
                x[1]
                for x in inspect.getmembers(_module, inspect.isclass)
                if issubclass(x[1], BaseConvertor)
            ]
            cls.convertors.extend(classes)

    def __init__(self, filename):
        self._load_convertors()
        self.filename = filename
        self.scratch = {}

    def load(self, **kwargs):
        for c in self.convertors:
            if c.can_load(self, **kwargs):
                return c.load(self, **kwargs)
        raise NotImplementedError

    def save(self, obj, **kwargs):
        for c in self.convertors:
            if c.can_save(self, **kwargs):
                return c.save(obj, self, **kwargs)
        raise NotImplementedError
