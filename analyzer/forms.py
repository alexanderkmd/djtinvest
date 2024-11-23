from django import forms
from .models import TargetPortfolio


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
