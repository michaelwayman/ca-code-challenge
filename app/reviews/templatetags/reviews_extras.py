from django import template

register = template.Library()


@register.inclusion_tag("reviews/_stars.html")
def stars(rating):
    value = float(rating or 0)
    full = int(round(value))
    return {
        "full": range(full),
        "empty": range(5 - full),
        "value": "" if rating is None else f"{value:.1f}".rstrip("0").rstrip("."),
    }
