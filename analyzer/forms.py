from django import forms
from .models import TargetPortfolio


class TargetPortfolioForm(forms.ModelForm):

    class Meta:
        model = TargetPortfolio
        fields = ["name", "targetPrice", "accounts"]

        widgets = {
            "accounts": forms.widgets.CheckboxSelectMultiple()
        }
