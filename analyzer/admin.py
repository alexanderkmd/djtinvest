from django.contrib import admin
from django.shortcuts import redirect
from django.urls import path, reverse
# https://docs.djangoproject.com/en/5.1/ref/contrib/admin/#reversing-admin-urls
from django.utils.html import format_html
from .models import (Account, CentrobankRate, Currency, Instrument, InstrumentData,
                     LastPrice, Operation, Position, Split, TargetPortfolio, TargetPortfolioValues)


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ["bank", "name", "type"]


@admin.register(CentrobankRate)
class CBRFRateAdmin(admin.ModelAdmin):
    list_display = ["date", "currency", "rate"]
    list_filter = ["date", "currency"]
    ordering = ["-date", "currency"]


@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    list_display = ["code", "symbol", "name_rus", "name", "auto_rate_preload_toggle", "num", "id"]
    ordering = ["code"]

    def get_urls(self):
        return [
            path(
                "<currency_pk>/toggle_auto_rate_preload",
                self.admin_site.admin_view(currency_toggle_auto_rate_preload),
                name="currency_auto_rate_preload",
            ),
            *super().get_urls(),
        ]

    def auto_rate_preload_toggle(self, obj: Currency) -> str:
        url = reverse("admin:currency_auto_rate_preload", args=[obj.pk])
        icon_url = "/static/admin/img/icon-yes.svg"
        if not obj.auto_rate_preload:
            icon_url = "/static/admin/img/icon-no.svg"
        return format_html(
            f'<img src="{icon_url}" alt="{obj.auto_rate_preload}" id="{obj.pk}"> <a href="{url}">Изменить</a>')

    auto_rate_preload_toggle.short_description = "Подгружать курс"


def currency_toggle_auto_rate_preload(request, currency_pk=0):
    """Переключает метку автозагрузки курса и возвращается в список валюют"""
    tmpCurrency = Currency.objects.get(pk=currency_pk)
    tmpCurrency.auto_rate_preload = not tmpCurrency.auto_rate_preload
    tmpCurrency.save()
    url = reverse("admin:analyzer_currency_changelist", args=[])
    url = f"{url}#{currency_pk}"
    return redirect(url)


@admin.register(Instrument)
class InstrumentAdmin(admin.ModelAdmin):
    list_display = ["idType", "idValue", "instrumentData"]
    ordering = ["instrumentData"]


@admin.register(InstrumentData)
class InstrumentDataAdmin(admin.ModelAdmin):
    list_display = ["icon_img", "ticker_name", "figi", "isin",
                    "instrument_type", "uid", "position_uid", "asset_uid", "updated"]
    ordering = ["ticker"]

    def icon_img(self, obj: InstrumentData) -> str:
        url = reverse("admin:analyzer_instrumentdata_change", args=[obj.pk])
        icon_url = obj.icon_url()
        return format_html(f"""<a href="{url}"><img src="{icon_url}" height="32px"></a>""")

    icon_img.short_description = ""

    def ticker_name(self, obj: InstrumentData) -> str:
        url = reverse("admin:analyzer_instrumentdata_change", args=[obj.pk])
        return format_html(f"""<a href="{url}">{obj.ticker}<br/>{obj.name}</a>""")

    ticker_name.short_description = "Тикер/Название"


@admin.register(LastPrice)
class LastPriceAdmin(admin.ModelAdmin):
    list_display = ["figi", "price", "timestamp", "updated"]


@admin.register(Operation)
class OperationAdmin(admin.ModelAdmin):
    list_display = ["timestamp", "account", "type", "figi"]


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ["account", "figi", "instrument", "quantity", "updated"]


@admin.register(Split)
class SplitAdmin(admin.ModelAdmin):
    list_display = ["date", "ticker", "before", "after"]
    ordering = ["-date"]


class TargetPortfolioValuesInline(admin.TabularInline):
    model = TargetPortfolioValues
    extra = 1
    fields = ["order_number", "instrument", "indexTarget", "coefficient"]


@admin.register(TargetPortfolio)
class TargetPortfolioAdmin(admin.ModelAdmin):
    list_display = ["name", "targetPrice"]
    inlines = [TargetPortfolioValuesInline]
