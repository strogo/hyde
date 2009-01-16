from django import template
from django.template import Library

register = Library()

class HydeContextNode(template.Node):
    def __init__(self): pass
    
    def render(self, context):
        return ""
        
@register.tag(name="hyde")
def hyde_context(parser, token):
    return HydeContextNode()

@register.filter
def value_for_key(d, key):
    if not d:
        return ""
    if not d.has_key(key):
        return ""
    return d[key]