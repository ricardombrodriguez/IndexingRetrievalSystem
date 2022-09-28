import sys

def dynamically_init_class(module_name, **kwargs):
    class_name = kwargs.pop("class")
    return getattr(sys.modules[module_name], class_name)(**kwargs)