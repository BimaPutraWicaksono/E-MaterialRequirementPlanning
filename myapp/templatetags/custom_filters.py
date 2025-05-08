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
