from django import template
import decimal

register = template.Library()


# кастомный фильтр, который "срезает" лишние нули после запятой
@register.filter
def dynamic_float(value):
    try:
        if isinstance(value, decimal.Decimal):
            if value == value.to_integral_value():
                return f"{value:.0f}"
            return f"{value:.4f}".rstrip('0').rstrip('.')

        elif isinstance(value, float):
            value = decimal.Decimal(value)
            if value == value.to_integral_value():
                return f"{value:.0f}"
            return f"{value:.4f}".rstrip('0').rstrip('.')

        elif isinstance(value, int):
            return f"{value:.0f}"

        elif isinstance(value, str):
            try:
                value = decimal.Decimal(value)
                return dynamic_float(value)
            except decimal.InvalidOperation:
                return "Invalid value"

        return value
    except (ValueError, TypeError, decimal.InvalidOperation):
        return "Invalid value"


#чтобы можно было сделать вычитание в html
@register.filter
def subtract(value, arg):
    return value - arg