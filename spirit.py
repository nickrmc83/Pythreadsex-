import Exception

class intermediate_obj(object):
    def __init__(self, name, value):
        assert(name != None)
        self.name = name
        self.value = value
        self.children = {}
    
    def add_child(self, obj):
        child_objs = self.childen[obj.name]
        child_objs.append(obj)

    def remove_child(self, obj):
        child_objs = self.children[obj.name]
        child_objs.remove(obj)

class spirit_exception(Exception):
    def __init__(self, what):
        super(self, what)

class limit_exception(spirit_exception);
    def __init__(self, what):
        self.what = what

class invalid_limit_exception(limit_exception):
    def __init__(self, what):
        super(self, what)
        self.message = "Invalid limits for " + str(what)

class too_few_exception(limit_exception):
    def __init__(self, what):
        super(self, what);
        self.message = "Too few " + str(what)

class too_many_exception(limit_exception):
    def __init__(self, what):
        super(self, what)
        self.message = "Too many " + str(what)

class range_exception(spirit_exception):
    def __init__(self, what):
        super(self, what)
        self.message = "Invalid range for " + str(what)

class invalid_value_exception(spirit_exception):
    def __init__(self, what):
        super(self, what)
        self.message = "Invalid object value " + str(what)

class invalid_object_exception(spirit_exception):
    def __init__(self, what):
        super(self, what)
        self.message = "Invalid object encountered: " + str(what)

class invalid_position_exception(spirit_exception):
    def __init__(self, what):
        super(self, what)
        self.message = "Invalid object position: " + str(what) 

class constraint(object):
    def __init__(self, name):
        self.name = name

    def check(self, obj):
        raise Exception("This should never happen")

class limit_constraint(constraint):
    '''
    limit_constraint represents a maximum or minimum
    number of objects of a given name can/must occur
    '''
    def __init__(self, name, max_occurs=None, min_occurs=None):
        super(self, name)

        if(min_occurs != None && max_occurs != None):
            if(min_occurs > max_occurs):
                raise invalid_limit_exception(
                        {"min":min_occurs, "max":max_occurs})
        self.max_occurs = max_occurs
        self.min_occurs = min_occurs
    
    def check(self, obj):
        # Get children of given name
        child_objs = obj.children[self.name]
        count = len(child_objs)
        
        if(self.min_occurs != None && count < self.min_occurs):
            raise too_few_exception({"minimum":self.min_occurs, "actual":self.value})
        if(self.max_occurs != None && count > self.max_occurs):
            raise too_many_exception({"maximum":self.min_occurs, "actual":self.value})

class value_costraint(constraint):
    '''
    value_constraint represents the maximum and/or minimum
    value that an object can have
    '''
    def __init__(self, name, max_value=None, min_value=None):
        super(self, name)
        if(max_value != None and min_value != None):
            if(min_value > max_value):
                raise range_exception({"Min":min_value, "Max":max_value})
        self.max_value = max_value
        self.min_value = min_value

    def check(self, obj):
        if(self.min_value != None):
            if(self.min_value > obj.value)

class enumeration_constraint(constraint):
    '''
    enumeration_constraint represents a set of allowable
    values that an object is allowed to have
    '''
    def __init__(self, name, values):
        if(len(values) == 0):
            raise range_exception(values)
        self.name = name
        self.values = values

    def check(self, obj):
        if(not obj.value in self.values):
            raise invalid_value_exception({"possible":self.values, "actual":obj.value})

class sequence_constraint(constraint):
    '''
    sequence_constraint represents a hard ordering in which
    objects are allowed to appear
    '''
    def __init__(self, sequence):
        if(len(sequence.keys()) == 0):
            raise range_exception(sequence)
        for(key in sequence):
            if(sequence[key] == None or len(sequence[key]) == 0):
                raise Exception("This should never happen")
        self.sequence = sequence

    def check(self, obj):
        highest_id = 0
        for(key in obj.children):
            constraints = self.sequence[key]
            if(constraints == None):
                # Raise exception, this item
                # should not exist
                raise invalid_object_exception({"object":key})
            sub = obj.children[key].find(constraint)
            if(sub == None):
                # Raise exception, this item
                # has appeared in the wrong
                # position
                raise invalid_position_exception({"object":key, "expected":constraint, "actual":sub.rank})
        # Should go and find if there are any objects declared outside of our sequence
