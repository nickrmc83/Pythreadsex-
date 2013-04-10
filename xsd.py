from default import *
from argparse import ArgumentParser
import os
from xml.etree.ElementTree import ElementTree, Element

class constraint(object):
    pass

class limit_constraint(constraint):
    def __init__(self, what, max_occurs, min_occurs):
        self.what = what
        self.max_occurs = max_occurs
        self.min_occurs = min_occurs

class enumeration_constraint(constraint):
    def __init__(self, allowable_values):
        self.allowable_values = allowable_values

class range_constraint(constraint):
    def __init__(self, max_value, min_value):
        self.max_value = max_value
        self.min_value = min_value

class order_constraint(constraint):
    def __init__(self, obj_order):
        self.obj_order = obj_order

class il_object(object):
    def __init__(self, obj, type):
        assert(obj != None)
        self.name = obj.attrib["name"]
        self.type = type
        # create an empty list of constraints
        # which must be satisfied.
        self.contraints = []

class string_type_handler(il_object):
    def __init__(self, obj):
        super(string_type_handler, self).__init__(obj, str)

class integer_type_handler(il_object):
    def __init__(self, obj):
        super(integer_type_handler, self).__init__(obj, int)

class double_type_handler(il_object):
    def __init__(self, obj):
        super(double_type_handler, self).__init__(obj, float)

class simple_type_handler(il_object):
    def __init__(self, obj):
        super(simple_type_handler, self).__init__(obj, str)
    
class xsd_gen_exception(Exception):
    pass

class unknown_type_exception(xsd_gen_exception):
    def __init__(self, tag):
        self.tag = tag
    
    def __str__(self):
        return "Unknown type %s" % self.tag

class unknown_namespace_exception(xsd_gen_exception):
    def __init__(self, ns):
        self.ns = ns

    def __str__(self):
        return "Unknown namespace %s" % self.ns

xsd_type_handlers = {}

def xsd_type_handler(uri):
    '''
    All handlers shoudl register themselves via decoration
    '''
    assert(uri != None)
    assert(isinstance(uri, str))

    def __internal(obj):
        global xsd_type_handlers
        # If a handler for this namesace has already been
        # installed then throw an exception
        if(uri in xsd_type_handlers):
            raise Exception("Two or more handlers declared for namespace %s" % uri)
        # Add handler to our list
        xsd_type_handlers[uri] = obj
        print(xsd_type_handlers)
        return obj
    return __internal

@xsd_type_handler("http://SomeUrl")
class xsd_types(object):
    xsd_handler_uri = "http://SomeUrl"
    
    def is_xsd(self, obj):
        obj_ns, obj_tag = decode_string_xmlns(obj.tag)
        if(obj_ns != xsd_types.xsd_handler_uri):
            raise unknown_namespace_exception(obj_ns)
        if(obj_tag != "schema"):
            raise unknown_type_exception(obj_tag)

    def parse(self, tag, obj):
        if(tag == "string"):
            return string_type_handler(obj)
        if(tag == "integer"):
            return integer_type_handler(obj)
        if(tag == "double"):
            return double_type_handler(obj)
        if(tag == "simpletype"):
            return simple_type_handler(obj)
        raise unknown_type_exception(tag)

def decode_string_xmlns(val):
    if(val[0] == "{"):
        return val[1:].split("}")
    return ("", val) # empty namespace and value


class xsd_gen(object):
    # URI identifier for xsd types
    default_handler_uri = ""

    def __init__(self, data):
        self.xsd = data
        # Build a vtable map of namepscaes and types to handlers
        self.type_handlers = {
                xsd_gen.default_handler_uri : None, # default namespace
                xsd_types.xsd_handler_uri : xsd_types()# xsd namespace
                }

    def compile_il(self):
        # Check this is an xsd object
        self.type_handlers[xsd_types.xsd_handler_uri].is_xsd(self.xsd)

        # dictionary which represents the internal type representations
        result = {}
        # iterate through items
        for child in iter(self.xsd):
            for c in child.iter():
                # Find handler for type based on namespace.
                # If we don't know about the namespace raise
                # an unknown namespace_exception
                ns, tag = decode_string_xmlns(c.tag)
                ns_handler = self.type_handlers[ns]
                if(ns_handler == None):
                    raise unknown_namespace_exception(ns)
                v = ns_handler.parse(tag, c)
                result[c.tag] = v
        return result

if __name__ == "__main__":
    # Load, parse and obtain root element of xsd
    parser = ArgumentParser(description="xsd to code generator", 
            version="1.0.0.0", 
            add_help=True)
    parser.add_argument("filename", 
            metavar="filename", 
            type=str, 
            help="The name of the xsd file to genarate from")
    parser.add_argument("--language",
            metavar="language",
            choices=["python"],
            default="python",
            type=str,
            help="The output language to generate. Python by default.")
    
    args = parser.parse_args()
    
    if(not os.path.exists(args.filename)):
        raise Exception("The source xsd does not exist: %s" % args.filename) 
    try:
        root = ElementTree(file=args.filename).getroot()
        print("Compiling il for %s" % args.filename)
        il = xsd_gen(root).compile_il();
        print("Generated il %s" % il)
        
        print("Generating code for %s." % args.language)
        if(args.language == "python"):
            pass
        if(args.language == "c++"):
            pass
        if(args.language == "c#"):
            pass
        if(args.language =="java"):
            pass

        print("Completed code generation from %s for language %s" % (args.filename, args.language))
    except unknown_type_exception, e:
        print("Unknown type in xsd, <%s/>" % e.tag)
