"""
Zero-dependency mock for ChromaDB.
This file automatically intercepts imports to `chromadb` if it is missing,
allowing CrewAI to start without installing hundreds of megabytes of C++ vector DB dependencies.
"""
import sys

try:
    # Check if the real ChromaDB is installed
    import chromadb.config
except ImportError:
    from types import ModuleType
    from importlib.abc import MetaPathFinder, Loader
    from importlib.machinery import ModuleSpec
    from pydantic_core import core_schema

    class DummyClass:
        """A universal mock class that satisfies Pydantic validation and CrewAI's typing."""
        @classmethod
        def __get_pydantic_core_schema__(cls, source, handler):
            return core_schema.any_schema()

        def __call__(self, *args, **kwargs):
            return self

        def __getitem__(self, item):
            return self

        @classmethod
        def __class_getitem__(cls, item):
            return cls

    class MockChromaLoader(Loader):
        def exec_module(self, module):
            module.__path__ = []
            module.__getattr__ = lambda name: DummyClass

    class MockChromaFinder(MetaPathFinder):
        def find_spec(self, fullname, path, target=None):
            if fullname.startswith('chromadb'):
                return ModuleSpec(fullname, MockChromaLoader(), is_package=True)
            return None

    # Inject the interceptor into Python's import system
    sys.meta_path.insert(0, MockChromaFinder())
