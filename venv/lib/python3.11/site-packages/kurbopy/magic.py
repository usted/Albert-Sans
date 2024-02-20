
# This is dirty
def get_magic_name(obj):
    cls = obj.__class__
    if hasattr(cls, "__name__"):
        return cls.__name__
    print(str(obj))
    sys.exit(1)


def magic_mul(self, rhs):
    other_type = get_magic_name(rhs)
    mytype = get_magic_name(self)
    if hasattr(self, "_mul_" + other_type):
        return getattr(self, "_mul_" + other_type)(rhs)
    raise TypeError("Cannot multiply %s by %s" % (mytype, other_type))


def magic_sub(self, rhs):
    other_type = get_magic_name(rhs.__class__)
    if hasattr(self, "_sub_" + other_type):
        return getattr(self, "_sub_" + other_type)(rhs)
    raise TypeError("Cannot subtract %s from %s" % (other_type, mytype))

def magic_isub(self, rhs):
    other_type = get_magic_name(rhs.__class__)
    if hasattr(self, "_isub_" + other_type):
        return getattr(self, "_isub_" + other_type)(rhs)
    raise TypeError("Cannot subtract %s from %s" % (other_type, mytype))

def magic_add(self, rhs):
    other_type = get_magic_name(rhs.__class__)
    if hasattr(self, "_add_" + other_type):
        return getattr(self, "_add_" + other_type)(rhs)
    raise TypeError("Cannot add %s to %s" % (other_type, mytype))

def magic_iadd(self, rhs):
    other_type = get_magic_name(rhs.__class__)
    if hasattr(self, "_iadd_" + other_type):
        return getattr(self, "_iadd_" + other_type)(rhs)
    raise TypeError("Cannot add %s to %s" % (other_type, mytype))
