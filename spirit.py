import Exception

class intermediate_obj:
    def __init__(self, value):
        self.value = value
        self.children = ()
    
    def add_child(self, obj):
        self.childen.append(obj)

    def remove_child(self, obj):
        self.children.remove(obj)

class limit_exception(Exception);
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

class constraint:
    def __init__(self, value):
        self.value = value

    def check(self, obj):
        return True

class limit_constraint(constraint):
    def __init__(self, value, max_occurs=None, min_occurs=None):
        super(self, value)
        self.__max_occurs = max_occurs
        self.__min_occurs = min_occurs
        
        if(min_occurs == None && max_occurs = None):
            raise invalid_limit_exception(
                    {"min":"Not set", "max":"Not set"})

        if(min_occurs != None && max_occurs != None):
            if(min_occurs > max_occurs):
                raise invalid_limit_exception(
                        {"min":min_occurs, "max":max_occurs})
    
    def check(self, obj):
        count = 0
        
        for child in obj.children:
            if(child.value == self.value):
                count++
        
        if(self.min_occurs != None && count < self.min_occurs):
            raise too_few_exception(self.value)
        if(self.max_occurs != Nome && count > self.max_occurs):
            raise too_many_exception(self.value)
