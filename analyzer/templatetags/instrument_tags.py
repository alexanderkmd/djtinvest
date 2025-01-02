from django import template
from django.core.cache import cache
from django.template.loader import render_to_string

from analyzer.models import Bank, InstrumentData

register = template.Library()

@register.simple_tag
def instrument_badge(instrumentData: InstrumentData,
                     show_banks=True,
                     use_cache=True):
    cache_key = f"instrumentBadge{instrumentData.pk}{show_banks}"
    html = cache.get(cache_key, None)
    if html is None or not use_cache:
        banks_out = []
        if show_banks:
            banks = Bank.objects.filter(show_link=True)
            for bank in banks:
                banks_out.append({
                    "name": bank.short_name,
                    "icon": bank.icon_url,
                    "instrument_url": instrumentData.instrument_url(bank.alias)
                    })
        context = {
            "instrument": instrumentData,
            "banks": banks_out,
            "show_banks": show_banks
            }
        html = render_to_string(
            "tags/instrument.html",
            context)
        cache.set(cache_key, html, timeout=3600)
    return html
