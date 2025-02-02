from django.urls import path

from . import views

app_name = "analyzer"
urlpatterns = [
    path("", views.index_view, name="index"),
    path("account/update_operations/<int:account_pk>",
         views.account_operations_update, name="account_operations_update"),
    path("account/update_positions/<int:account_pk>",
         views.account_positions_update, name="account_positions_update"),
    path("accounts", views.AccountsView.as_view(), name="accounts"),

    path("dividends", views.dividends_view, name="dividends"),
    path("dividends/year/<int:year>", views.devidends_for_year_list, name="dividends-year"),

    path("operations", views.operations_list, name="operations"),
    path("operations/<int:year>/<int:month>/<int:day>/", views.OperationsByDateView.as_view(), name="operations"),

    path("positions", views.PositionsView.as_view(), name="positions"),
    path("position/<str:figi>", views.PositionDetailView, name="positionDetail"),
    path("position/", views.PositionDetailView, name="positionDetail"),

    path("targets", views.TargetsView, name="targets"),
    path("targets/<int:portfolio_pk>", views.TargetsDetailView, name="targetDetails"),
    path("target/edit/<int:portfolio_pk>", views.TargetPortfolioEditView, name="targetEdit"),

    path("target/tobuy/", views.TargetPortfolioToBuy, name="targetIndexToBuy"),
    path("target/tobuy/<int:portfolio_pk>/<int:cash_sum>/<str:calculateMethod>", views.TargetPortfolioToBuy,
         name="targetIndexToBuy"),

    path("target/updateIndex/<int:portfolio_pk>", views.TargetPortfolioUpdateIndex, name="targetIndexUpdate"),
    path("target/positions/<int:portfolio_pk>", views.TargetPortfolioPositions, name="targetPositions"),
    path("target/position/<int:position_pk>", views.TargetPortfolioPositionItem,
         name="targetPositionItem"),
    path("target/position/<int:position_pk>/<int:toggle_update>", views.TargetPortfolioPositionItem,
         name="targetPositionItem"),
    path("target/position/<int:position_pk>/set_coefficient", views.TargetPositionSetCoefficient,
         name="positionCoefficientSet"),
    path("target/position/add", views.TargetPortfolioPositionAdd,
         name="positionAdd"),
    path("target/position/delete/<int:position_pk>", views.TargetPositionDelete,
         name="positionDelete"),
    path("target/position/move/<int:position_pk>/<str:dir>", views.TargetPortfolioPositionItemMove,
         name="positionMove"),

    path("sberbank/upload/", views.UploadSberbankReport,
         name="sberbankUpload")
]
