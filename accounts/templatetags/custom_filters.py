# accounts/templatetags/custom_filters.py

from django import template

register = template.Library()

@register.filter
def replace_underscore(value):
    """Replaces underscores with hyphens"""
    if value:
        return str(value).replace('_', '-')
    return value