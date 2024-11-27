from django import forms
from .models import InstrumentData, TargetPortfolio

from typing import List


class TargetPortfolioForm(forms.ModelForm):

    class Meta:
        model = TargetPortfolio
        fields = ["name", "targetPrice", "accounts"]

        widgets = {
            "accounts": forms.widgets.CheckboxSelectMultiple()
        }


class TargetPortfolioIndexSelectionForm(forms.Form):
    targetPortfolioPk = forms.CharField(widget=forms.HiddenInput)
    indexName = forms.ChoiceField(
        label="Индекс",
        choices=(
            ("IMOEX", "Индекс МосБиржи"),
            ("IMOEX2", "Индекс МосБиржи (все сессии)"),
            ("MOEXBC", "Индекс голубых фишек МосБиржи"),
            ("RTSI", "Индекс РТС")
        )
    )

    class Meta:
        pass


def populateInstrumentChoices() -> List[tuple[str, str]]:
    instruments = InstrumentData.objects.all().order_by("name")

    out = list()
    for instrument in instruments:
        name = f"{instrument.name} ({instrument.ticker})"
        figi = instrument.figi
        out.append((figi, name))

    return out


class TargetPortfolioAddPositionForm(forms.Form):

    targetPortfolioPk = forms.CharField(widget=forms.HiddenInput)
    instrumentCode = forms.CharField(label="Ticker/Figi/ISIN", max_length=14, required=False)
    instruments = forms.ChoiceField(
        label="Инструменты",
        choices=populateInstrumentChoices(),
    )

    class Meta:
        pass
