from django import template

register = template.Library()

@register.filter
def get_applicator_carline(terminal_data, applicator):
    for terminal, months in terminal_data.items():
        for month, items in months.items():
            for item in items:
                if isinstance(item, dict) and item.get("name") == applicator:
                    return item.get("carline", "")
    return ""


@register.filter
def dict_get(d, key):
    if d and key in d:
        return d.get(key)
    return ''

@register.filter
def dict_get(dictionary, key):
    try:
        return dictionary[key]
    except KeyError:
        return None

@register.filter
def get_item(dictionary, key):
    if dictionary:
        return dictionary.get(key)
    return None

@register.filter
def get_item_by_month(value, month):
    for item in value:
        if item.month == month:
            return item
    return None

@register.filter
def deep_get(data, path):
    try:
        for key in path:
            data = data[key]
        return data
    except (KeyError, TypeError):
        return None