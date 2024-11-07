import logging

from datetime import datetime, timedelta, timezone

from decimal import Decimal

from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.template import loader
from django.urls import reverse
from django.views import generic

from .models import Account, Operation, Position, PortfolioPosition, TargetPortfolio, TargetPortfolioValues
from .utils import is_htmx, paginate
from . import tasks


def index_view(request):
    template = loader.get_template("analyzer/index.html")
    context = {
        # "latest_question_list": latest_question_list,
    }
    return HttpResponse(template.render(context, request))


class AccountsView(generic.ListView):
    model = Account
    template_name = "analyzer/accounts.html"
    context_object_name = "accounts"


def account_operations_update(request, account_pk: int):
    account = Account.objects.get(pk=account_pk)
    # TODO start date limit
    tasks.get_tinkoff_operations(account.accountId)
    return redirect("analyzer:accounts")


def account_positions_update(request, account_pk: int):
    account = Account.objects.get(pk=account_pk)
    tasks.get_tinkoff_positions(account.accountId)
    return redirect("analyzer:accounts")


def dividends_view(request, account_pk=0):
    template = loader.get_template("analyzer/dividends.html")
    op_types = ["OPERATION_TYPE_DIVIDEND", "OPERATION_TYPE_DIVIDEND_TAX", "OPERATION_TYPE_COUPON"]
    dividend_ops = Operation.objects.filter(type__in=op_types).order_by("-timestamp")
    last_year_salary = 0
    years = {}
    salary_year_start = datetime.now(timezone.utc)-timedelta(days=365)
    for op in dividend_ops:
        year = op.timestamp.year.__str__()
        if year not in years:
            years[year] = {"dividend": 0, "coupon": 0, "tax": 0, "count": 0}
        years[year]["count"] += 1
        if op.type == "OPERATION_TYPE_DIVIDEND":
            years[year]["dividend"] += abs(op.payment_rub())
        elif op.type == "OPERATION_TYPE_COUPON":
            years[year]["coupon"] += abs(op.payment_rub())
        elif op.type == "OPERATION_TYPE_DIVIDEND_TAX":
            years[year]["tax"] += abs(op.payment_rub())

        if op.timestamp > salary_year_start:
            last_year_salary += op.payment_rub()
    context = {
        "operations":  dividend_ops,
        "years": years,
        "last_year_salary": last_year_salary,
        "last_year_monthly_salary": last_year_salary/12
    }
    return HttpResponse(template.render(context, request))


def devidends_for_year_list(request, year, account_pk=0):
    template = loader.get_template("analyzer/dividends_year_list.html")
    op_types = ["OPERATION_TYPE_DIVIDEND", "OPERATION_TYPE_DIVIDEND_TAX", "OPERATION_TYPE_COUPON"]
    dividend_ops = Operation.objects.filter(type__in=op_types, timestamp__year=year).order_by("-timestamp")
    context = {
        "operations":  dividend_ops,
        "year": year
    }
    return HttpResponse(template.render(context, request))


def operations_list(request):
    operations = paginate(request, Operation.objects.order_by("-timestamp").all().prefetch_related("instrument"),
                          limit=50)
    context = {
        "operations": operations
    }
    if is_htmx(request):
        return render(request, "analyzer/operations_list.html", context)
    return render(request, "analyzer/operations.html", context)


class OperationsView(generic.ListView):
    model = Operation
    template_name = "analyzer/operations.html"
    context_object_name = "operations"

    def get_queryset(self):
        """Return operations"""
        return Operation.objects.order_by("-timestamp").prefetch_related("instrument")  # [:20]


class PositionsView(generic.ListView):
    model = Position
    template_name = "analyzer/positions.html"
    context_object_name = "positions"

    ordering = []

    def get_queryset(self):
        """Return positions"""
        return Position.objects.order_by("-instrument__instrument_type", "instrument__name")  # [:20]


def PositionDetailView(request, figi: str):
    template = loader.get_template("analyzer/position.html")
    position = PortfolioPosition(figi)

    context = {
        "position": position
    }
    return HttpResponse(template.render(context, request))


def TargetsView(request):
    template = loader.get_template("analyzer/targets.html")

    targetPortfolios = TargetPortfolio.objects.all()
    context = {
        "portfolios": targetPortfolios,
        }

    return HttpResponse(template.render(context, request))


def TargetsDetailView(request, portfolio_pk):
    template = loader.get_template("analyzer/targets_detail.html")
    tasks.target_portfolio_preload_last_prices(portfolio_pk)

    targetPortfolio = TargetPortfolio.objects.get(pk=portfolio_pk)
    context = {
        "portfolio": targetPortfolio,
        }

    return HttpResponse(template.render(context, request))


def TargetPortfolioPositions(request, portfolio_pk):
    template = loader.get_template("analyzer/targets_positions_list.html")

    targetPortfolio = TargetPortfolio.objects.get(pk=portfolio_pk)
    targetPositions = TargetPortfolioValues.objects.filter(
        targetPortfolio__pk=portfolio_pk
        ).select_related("targetPortfolio"
        ).prefetch_related("instrument")

    # запрос текущих цен бумаг одним запросом
    tasks.target_portfolio_preload_last_prices(portfolio_pk)

    context = {
        "portfolio": targetPortfolio,
        "positions": targetPositions,
        }

    return HttpResponse(template.render(context, request))


def TargetPositionSetCoefficient(request, position_pk:int):
    logging.info(request.POST.keys())
    new_coeff = request.POST.get("coefficient", "1.0")
    position = TargetPortfolioValues.objects.get(pk=position_pk)
    position.coefficient = Decimal(new_coeff.replace(",", "."))
    logging.info(f"{new_coeff}, {position.coefficient}, {new_coeff.replace('',', ''.')}")
    position.save()
    return redirect(reverse("analyzer:targetPositions", kwargs={"portfolio_pk": position.targetPortfolio.pk}))
