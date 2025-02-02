import logging

from datetime import datetime, timedelta, timezone

from decimal import Decimal

from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect, HttpRequest
from django.shortcuts import render, redirect
from django.template import loader
from django.urls import reverse
from django.views import generic

from .forms import (SberbankReportUploadForm, TargetPortfolioForm,
                    TargetPortfolioIndexSelectionForm, TargetPortfolioAddPositionForm)
from .models import Account, Instrument, Operation, Position, PortfolioPosition, TargetPortfolio, TargetPortfolioValues
from .utils import is_htmx, paginate
from . import tasks

from .enums import comission_operations_name, tax_operations_name


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
    first_operation = (Operation.objects.order_by("-timestamp").
                       exclude(type__in=tax_operations_name).exclude(type__in=comission_operations_name).
                       first())
    context = {}

    if first_operation is None:
        context['operations_is_empty'] = True
    else:
        context["first_operation_date"] = first_operation.timestamp

    return render(request, "analyzer/operations.html", context)


def operations_list_old(request):
    """Устаревшая - использовался пагинатор по количеству, не по дате"""
    operations = paginate(request,
                          Operation.objects.order_by("-timestamp").
                          exclude(type__in=tax_operations_name).exclude(type__in=comission_operations_name).
                          all().prefetch_related("instrument"),
                          limit=50)
    context = {
        "operations": operations,
        "has_next": operations.has_next,
        "next_page_number": operations.next_page_number,
    }
    if is_htmx(request):
        return render(request, "analyzer/operations_list.html", context)
    return render(request, "analyzer/operations.html", context)


class OperationsByDateView(generic.DayArchiveView):
    """Список операций по дате, сразу исключает налоги и комиссии по операциям.
    Последние отображаются как поля в соответствующих операциях.

    Args:
        year, month, day (int): элементы даты для предоставления

    """
    date_field = "timestamp"
    allow_future = False
    allow_empty = False
    month_format = "%m"
    template_name = "analyzer/operations_list_date.html"
    context_object_name = "operations"

    def get_queryset(self):
        queryset = (Operation.objects.order_by("-timestamp").
                    exclude(type__in=tax_operations_name).exclude(type__in=comission_operations_name).
                    all().prefetch_related("instrument"))
        return queryset


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

    for portfolio in targetPortfolios:
        tasks.target_portfolio_preload_last_prices(portfolio.pk)

    context = {
        "portfolios": targetPortfolios,
        }

    return HttpResponse(template.render(context, request))


def TargetsDetailView(request, portfolio_pk):
    template = loader.get_template("analyzer/targets_detail.html")
    tasks.target_portfolio_preload_last_prices(portfolio_pk)

    targetPortfolio = TargetPortfolio.objects.get(pk=portfolio_pk)
    targetPortfolioConfigform = TargetPortfolioForm(instance=targetPortfolio)

    portfolioIndexForm = TargetPortfolioIndexSelectionForm()
    portfolioIndexForm.fields['targetPortfolioPk'].initial = portfolio_pk

    positionAddForm = TargetPortfolioAddPositionForm()
    positionAddForm.fields['targetPortfolioPk'].initial = portfolio_pk

    context = {
        "portfolio": targetPortfolio,
        "portfolioConfigForm": targetPortfolioConfigform,
        "portfolioIndexForm": portfolioIndexForm,
        "positionAddForm": positionAddForm,
        }

    return HttpResponse(template.render(context, request))


def TargetPortfolioEditView(request, portfolio_pk):
    targetPortfolio = TargetPortfolio.objects.get(pk=portfolio_pk)

    form = TargetPortfolioForm(request.POST or None, instance=targetPortfolio)

    if form.is_valid():
        form.save()

    return HttpResponseRedirect(reverse("analyzer:targetDetails",
                                        kwargs={"portfolio_pk": portfolio_pk}))


def TargetPortfolioToBuy(request: HttpRequest, portfolio_pk: int = 0,
                         cash_sum: int = 0,
                         calculateMethod: str = "simple"):
    if request.method == "POST":
        print(request.POST)
        portfolio_pk = int(request.POST.get("portfolio_pk", 0))
        cash_sum = int(request.POST.get("cash_sum", 0))
        calculateMethod = request.POST.get("calculateMethod", "simple")

    target_portfolio = TargetPortfolio.objects.get(pk=portfolio_pk)

    out = []
    if calculateMethod == "simple":
        out = tasks.target_portfolio_to_buy_simple(portfolio_pk, cash_sum)

    context = {
        "portfolio": target_portfolio,
        "items": out,
        "calculateMethod": calculateMethod,
    }
    template = loader.get_template("analyzer/targets_to_buy.html")
    return HttpResponse(template.render(context, request))


def TargetPortfolioUpdateIndex(request, portfolio_pk):
    """Обновляет состав индекса для целевого портфеля
    Пока - только часть индексов из MOEX.

    Args:
        portfolio_pk (int): pk целевого портфеля

    Returns:
        редирект на обновление страницы
    """
    form = TargetPortfolioIndexSelectionForm(request.POST or None)

    if form.is_valid():
        tasks.update_index_positions_in_target(portfolio_pk, form.cleaned_data['indexName'])

    return HttpResponseRedirect(reverse("analyzer:targetDetails",
                                        kwargs={"portfolio_pk": portfolio_pk}))


def TargetPortfolioPositions(request, portfolio_pk):
    template = loader.get_template("analyzer/targets_positions_list.html")

    targetPortfolio = TargetPortfolio.objects.get(pk=portfolio_pk)
    targetPositions = TargetPortfolioValues.objects.filter(
        targetPortfolio__pk=portfolio_pk
        ).select_related(
            "targetPortfolio"
        ).prefetch_related("instrument").order_by("order_number")

    # запрос текущих цен бумаг одним запросом
    tasks.target_portfolio_preload_last_prices(portfolio_pk)

    context = {
        "portfolio": targetPortfolio,
        "positions": targetPositions,
        }

    return HttpResponse(template.render(context, request))


def TargetPortfolioPositionItem(request, position_pk: int, toggle_update=False):
    """Рендерит ряд с позицией Целевого портфеля

    Args:
        position_pk (int): pk позиции
        toggle_update (bool, optional): Отправлять ли запрос на обновление всей таблицы. Defaults to False.

    Обновление всей таблицы требуется, например, при пересчете весов или изменения размера портфеля.
    """
    template = loader.get_template("analyzer/targets_position_item.html")

    targetPosition = TargetPortfolioValues.objects.filter(
        pk=position_pk
        ).select_related(
            "targetPortfolio"
        ).prefetch_related("instrument")[0]

    # запрос текущих цен бумаг одним запросом
    tasks.target_portfolio_preload_last_prices(targetPosition.targetPortfolio.pk)

    context = {
        "position": targetPosition,
        }

    response = HttpResponse(template.render(context, request))
    if toggle_update:
        response['HX-Trigger'] = "tableReload"
    return response


def TargetPortfolioPositionItemMove(request, position_pk: int, dir: str):
    """Moves TargetPositionValue in personal order list

    Args:
        position_pk (int): pk of TargetPositionValue
        dir (str): direction of movement (up/down)

    Returns:
        HttpResponse: code 200
    """
    targetPosition = TargetPortfolioValues.objects.get(pk=position_pk)
    movement = 1
    if dir == "up":
        movement = -1
    targetPosition.order_number += movement
    if targetPosition.order_number == 0:
        logging.info("Позиция и так на самом верху - двигать некуда!")
        return HttpResponse()
    other_positions = TargetPortfolioValues.objects.filter(
        targetPortfolio=targetPosition.targetPortfolio,
        order_number__gte=targetPosition.order_number
    ).order_by("order_number").all()
    counter = targetPosition.order_number
    for item in other_positions:
        if item.order_number == targetPosition.order_number and dir != "up":
            item.order_number += -1
            item.save()
            continue
        counter += 1
        item.order_number = counter
        item.save()
    targetPosition.save()
    logging.debug(f"Item new order position: {targetPosition.order_number}")
    return HttpResponse()


def TargetPortfolioPositionAdd(request):
    form = TargetPortfolioAddPositionForm(request.POST or None)
    if form.is_valid():
        instrumentCode = form.data['instrumentCode']
        if instrumentCode == "":
            instrumentCode = form.data['instruments']
        instrument = Instrument.get_instrument(instrumentCode)
        targetPortfolio = TargetPortfolio.objects.get(pk=form.data['targetPortfolioPk'])
        # TODO: проверка на ошибку в инструменте - что такой добавить нельзя, вывести сообщением
        TargetPortfolioValues.objects.get_or_create(
            targetPortfolio=targetPortfolio,
            instrument=instrument,
            defaults={
                "order_number": targetPortfolio.values_count()+1,
                "indexTarget": Decimal(0),
            }
        )
    return redirect(reverse("analyzer:targetDetails", kwargs={"portfolio_pk": targetPortfolio.pk}))


def TargetPositionSetCoefficient(request, position_pk: int):
    logging.info(request.POST.keys())
    new_coeff = request.POST.get("coefficient", "1.0")
    position = TargetPortfolioValues.objects.get(pk=position_pk)
    position.coefficient = Decimal(new_coeff.replace(",", "."))
    logging.info(f"{new_coeff}, {position.coefficient}, {new_coeff.replace('',', ''.')}")
    position.save()
    # Пересчет общего веса целевого портфеля
    tasks.target_portfolio_total_weight(position.targetPortfolio.pk, False)
    return redirect(reverse("analyzer:targetPositionItem", kwargs={"position_pk": position.pk,
                                                                   "toggle_update": 1}))


def TargetPositionDelete(request, position_pk: int):

    try:
        position = TargetPortfolioValues.objects.get(pk=position_pk)
        position.delete()
    except Exception as e:
        logging.error(f"Error deleting target position {position_pk}: {e}")
        return HttpResponse(status=500)

    response = HttpResponse(status=204)
    return response


def UploadSberbankReport(request):
    logging.info("Request for SberBankUpload Form")
    if request.method == "POST":
        logging.info("POST Request for SberBankUpload Form")
        form = SberbankReportUploadForm(request.POST, request.FILES)
        print(form.non_field_errors())
        print(request.FILES)
        if form.is_valid():
            message, error = tasks.process_sberbank_report_upload(request.FILES["reportFile"])
            if error:
                messages.error(request, message)
            else:
                messages.success(request, message)
            return redirect("analyzer:accounts", permanent=False)
    else:
        form = SberbankReportUploadForm()
    return render(request, "analyzer/sberbankUploadForm.html",
                  context={"form": form})

