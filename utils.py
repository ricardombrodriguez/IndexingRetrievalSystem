import sys

def dynamically_init_class(module_name, **kwargs):
    """Dynamically initializes a python object based
    on the given class name that resides inside module
    specified by the `module_name`.
    
    The `class` name must be specified as an additional argument,
    this argument will be caught under kwargs variable.
    
    The reason for not directly specifying the class as argument is 
    because `class` is a reserved keyword in python, which may be
    confusing if it is seen as an argument of a function. 
    Additionally, this way the function integrates nicely with the
    `.get_kwargs()` method from the `Param` object.
    Parameters
    ----------
    module_name : str
        the name of the module where the class resides
    kwargs : Dict[str, object]
        python dictionary that holds the variables and their values
        that are used as arguments during the class initialization.
        Note that the variable `class` must be here and that it will
        not be passed as an initialization argument since it is removed
        from this dict.
    
    Returns
        ----------
        object
            python instance
    """

    class_name = kwargs.pop("class")
    return getattr(sys.modules[module_name], class_name)(**kwargs)
