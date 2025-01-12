from django import template

register = template.Library()


def round_to_base(x, base=5):
    """Округляет до нужного числа 12->10, 13->15

    Args:
        x (_type_): _description_
        base (int, optional): _description_. Defaults to 5.

    Returns:
        _type_: _description_
    """
    return base * round(x/base)


@register.simple_tag
def complete_background_color(complete: int,
                              base_color: str = "bg-green-500",
                              over_color: str = "bg-red-300") -> str:
    complete = round_to_base(complete, 5)
    if complete > 120:
        # если значимое перевыполнение
        base_color = over_color
        complete -= 100

    if complete > 100:
        complete = 100

    return f"{base_color}/{complete}"
