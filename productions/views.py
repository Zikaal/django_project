import hashlib
import json
import logging
from decimal import Decimal

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.cache import cache
from django.http import FileResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import ListView, TemplateView
from django.views.generic.edit import CreateView, DeleteView, FormView, UpdateView
from django.db import transaction
from django.db.models import Count, F, Sum, Value, DecimalField, ExpressionWrapper
from django.db.models.functions import Coalesce

from accounts.mixins import (
    AdminOrManagerMixin,
    AdminOrManagerScopedMixin,
    AnyRoleScopedMixin,
)
from accounts.models import Profile
from django.core.exceptions import PermissionDenied
from accounts.utils import (
    can_import_export,
    can_edit_dailyproduction_obj,
    can_delete_dailyproduction_obj,
    get_user_company,
    is_admin,
    is_manager,
)
from companies.models import OilCompany
from .forms import (
    DailyProductionForm,
    WellForm,
    DailyProductionImportForm,
    MonthlyProductionExportForm,
)
from .models import (
    DailyProduction,
    DailyProductionImportJob,
    MonthlyProductionExportJob,
    Well,
)
from .tasks import import_daily_productions, generate_monthly_production_export

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Скважины (Wells)
# Правила: Admin — полный CRUD; Manager — CRUD только своей компании;
# Operator — доступа нет вообще
# ---------------------------------------------------------------------------

class WellListView(AdminOrManagerScopedMixin, ListView):
    required_permissions = ("productions.view_well",)
    model = Well
    template_name = "productions/well_list.html"
    context_object_name = "wells"
    paginate_by = 20
    company_filter_field = "oil_company_id"

    def get_queryset(self):
        queryset = super().get_queryset().select_related("oil_company")

        sort = self.request.GET.get("sort", "name")

        # Admin может дополнительно фильтровать по компании через URL
        if is_admin(self.request.user):
            company_id = self.request.GET.get("company", "")
            if company_id:
                queryset = queryset.filter(oil_company_id=company_id)

        if sort == "-name":
            queryset = queryset.order_by("-name")
        elif sort == "company":
            queryset = queryset.order_by("oil_company__name", "name")
        else:
            queryset = queryset.order_by("name")

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if is_admin(self.request.user):
            context["companies"] = OilCompany.objects.order_by("name")
        else:
            user_company = get_user_company(self.request.user)
            context["companies"] = (
                OilCompany.objects.filter(id=user_company.id)
                if user_company else OilCompany.objects.none()
            )

        context["selected_company"] = self.request.GET.get("company", "")
        context["sort"] = self.request.GET.get("sort", "name")
        context["total_count"] = self.get_queryset().count()

        query_params = self.request.GET.copy()
        query_params.pop("page", None)
        context["query_string"] = query_params.urlencode()

        return context


class WellCreateView(AdminOrManagerScopedMixin, CreateView):
    required_permissions = ("productions.add_well",)
    model = Well
    form_class = WellForm
    template_name = "productions/well_form.html"
    success_url = reverse_lazy("well_list")

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        _scope_company_in_form(form, self.request.user)
        return form


class WellUpdateView(AdminOrManagerScopedMixin, UpdateView):
    required_permissions = ("productions.change_well",)
    model = Well
    form_class = WellForm
    template_name = "productions/well_form.html"
    success_url = reverse_lazy("well_list")
    company_filter_field = "oil_company_id"

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        _scope_company_in_form(form, self.request.user)
        return form


class WellDeleteView(AdminOrManagerScopedMixin, DeleteView):
    required_permissions = ("productions.delete_well",)
    model = Well
    template_name = "productions/well_confirm_delete.html"
    success_url = reverse_lazy("well_list")
    company_filter_field = "oil_company_id"


# ---------------------------------------------------------------------------
# Суточные рапорты (DailyProduction)
# Правила: Admin — полный CRUD; Manager — CRUD своей компании;
# Operator — создание + просмотр своей компании
# ---------------------------------------------------------------------------

class DailyProductionListView(AnyRoleScopedMixin, ListView):
    required_permissions = ("productions.view_dailyproduction",)
    model = DailyProduction
    template_name = "productions/dailyproduction_list.html"
    context_object_name = "reports"
    paginate_by = 20
    company_filter_field = "well__oil_company_id"

    def get_queryset(self):
        queryset = super().get_queryset().select_related("well", "well__oil_company")

        sort = self.request.GET.get("sort", "-date")
        well_id = self.request.GET.get("well")
        date_from = self.request.GET.get("date_from")
        date_to = self.request.GET.get("date_to")

        if is_admin(self.request.user):
            company_id = self.request.GET.get("company")
            if company_id:
                queryset = queryset.filter(well__oil_company_id=company_id)

        if well_id:
            queryset = queryset.filter(well_id=well_id)
        if date_from:
            queryset = queryset.filter(date__gte=date_from)
        if date_to:
            queryset = queryset.filter(date__lte=date_to)

        if sort == "date":
            queryset = queryset.order_by("date")
        elif sort == "well":
            queryset = queryset.order_by("well__name")
        elif sort == "company":
            queryset = queryset.order_by("well__oil_company__name", "well__name")
        else:
            queryset = queryset.order_by("-date", "well__name")

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if is_admin(self.request.user):
            context["companies"] = OilCompany.objects.order_by("name")
            context["wells"] = Well.objects.select_related("oil_company").order_by("name")
        else:
            user_company = get_user_company(self.request.user)
            if user_company:
                context["companies"] = OilCompany.objects.filter(id=user_company.id)
                context["wells"] = (
                    Well.objects.filter(oil_company=user_company)
                    .select_related("oil_company").order_by("name")
                )
            else:
                context["companies"] = OilCompany.objects.none()
                context["wells"] = Well.objects.none()

        context["sort"] = self.request.GET.get("sort", "-date")
        context["selected_company"] = self.request.GET.get("company", "")
        context["selected_well"] = self.request.GET.get("well", "")
        context["date_from"] = self.request.GET.get("date_from", "")
        context["date_to"] = self.request.GET.get("date_to", "")
        context["total_count"] = self.get_queryset().count()

        query_params = self.request.GET.copy()
        query_params.pop("page", None)
        context["query_string"] = query_params.urlencode()

        context["import_form"] = DailyProductionImportForm()
        context["export_form"] = MonthlyProductionExportForm()
        context["can_import"] = can_import_export(self.request.user)
        context["can_export"] = can_import_export(self.request.user)

        return context


class DailyProductionCreateView(AnyRoleScopedMixin, CreateView):
    required_permissions = ("productions.add_dailyproduction",)
    model = DailyProduction
    form_class = DailyProductionForm
    template_name = "productions/dailyproduction_form.html"
    success_url = reverse_lazy("dailyproduction_list")

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        _scope_well_queryset(form, self.request.user)
        return form


class DailyProductionUpdateView(AnyRoleScopedMixin, UpdateView):
    required_permissions = ("productions.change_dailyproduction",)
    model = DailyProduction
    form_class = DailyProductionForm
    template_name = "productions/dailyproduction_form.html"
    success_url = reverse_lazy("dailyproduction_list")
    company_filter_field = "well__oil_company_id"

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not can_edit_dailyproduction_obj(request.user, self.object):
            raise PermissionDenied("Оператор не может редактировать рапорты старше 7 дней.")
        return super().dispatch(request, *args, **kwargs)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        _scope_well_queryset(form, self.request.user)
        return form


class DailyProductionDeleteView(AnyRoleScopedMixin, DeleteView):
    required_permissions = ("productions.delete_dailyproduction",)
    model = DailyProduction
    template_name = "productions/dailyproduction_confirm_delete.html"
    success_url = reverse_lazy("dailyproduction_list")
    company_filter_field = "well__oil_company_id"

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not can_delete_dailyproduction_obj(request.user, self.object):
            raise PermissionDenied("Оператор не может удалять рапорты старше 7 дней.")
        return super().dispatch(request, *args, **kwargs)


# ---------------------------------------------------------------------------
# Импорт / экспорт — только Admin и Manager
# ---------------------------------------------------------------------------

def _enqueue_import_job(job_id: int) -> bool:
    try:
        async_result = import_daily_productions.delay(job_id)
        DailyProductionImportJob.objects.filter(pk=job_id).update(
            celery_task_id=async_result.id
        )
        return True
    except Exception:
        logger.exception("Не удалось отправить задачу импорта %s в Celery.", job_id)
        try:
            job = DailyProductionImportJob.objects.get(pk=job_id)
            job.mark_failed(
                "Не удалось отправить задачу в очередь. Проверьте Redis, REDIS_URL и Celery worker."
            )
        except DailyProductionImportJob.DoesNotExist:
            pass
        return False


def _enqueue_export_job(job_id: int) -> bool:
    try:
        async_result = generate_monthly_production_export.delay(job_id)
        MonthlyProductionExportJob.objects.filter(pk=job_id).update(
            celery_task_id=async_result.id
        )
        return True
    except Exception:
        logger.exception("Не удалось отправить задачу экспорта %s в Celery.", job_id)
        try:
            job = MonthlyProductionExportJob.objects.get(pk=job_id)
            job.mark_failed(
                "Не удалось отправить задачу экспорта в очередь. Проверьте Redis, REDIS_URL и Celery worker."
            )
        except MonthlyProductionExportJob.DoesNotExist:
            pass
        return False


class DailyProductionImportView(AdminOrManagerMixin, FormView):
    required_permissions = ("productions.add_dailyproduction",)
    form_class = DailyProductionImportForm
    success_url = reverse_lazy("dailyproduction_list")

    def form_valid(self, form):
        uploaded_file = form.cleaned_data["file"]
        with transaction.atomic():
            import_job = DailyProductionImportJob.objects.create(
                file=uploaded_file,
                uploaded_by=self.request.user,
                status=DailyProductionImportJob.Status.PENDING,
            )
        queued = _enqueue_import_job(import_job.id)
        if queued:
            messages.success(
                self.request,
                f"Файл '{uploaded_file.name}' загружен и отправлен на фоновую обработку.",
            )
            return redirect(f"{self.success_url}?watch_notifications=1")
        else:
            messages.error(
                self.request,
                f"Файл '{uploaded_file.name}' был загружен, но задачу не удалось отправить в очередь.",
            )
            return redirect(self.success_url)

    def form_invalid(self, form):
        messages.error(self.request, "Не удалось загрузить файл. Проверьте форму.")
        return redirect(self.success_url)


class MonthlyProductionExportView(AdminOrManagerMixin, FormView):
    required_permissions = ("productions.view_dailyproduction",)
    form_class = MonthlyProductionExportForm
    success_url = reverse_lazy("dailyproduction_list")

    def form_valid(self, form):
        year = form.cleaned_data["year"]
        month = form.cleaned_data["month"]
        with transaction.atomic():
            export_job = MonthlyProductionExportJob.objects.create(
                requested_by=self.request.user,
                year=year,
                month=month,
                status=MonthlyProductionExportJob.Status.PENDING,
            )
        queued = _enqueue_export_job(export_job.id)
        if queued:
            messages.success(
                self.request,
                f"Экспорт за {month:02d}.{year} поставлен в очередь.",
            )
            return redirect(f"{self.success_url}?watch_notifications=1")
        else:
            messages.error(
                self.request,
                f"Запрос на экспорт за {month:02d}.{year} создан, но задачу не удалось отправить.",
            )
            return redirect(self.success_url)

    def form_invalid(self, form):
        messages.error(self.request, "Проверьте год и месяц для экспорта.")
        return redirect(self.success_url)


class MonthlyProductionExportDownloadView(LoginRequiredMixin, View):
    def get(self, request, pk):
        queryset = MonthlyProductionExportJob.objects.all()
        if not request.user.is_staff:
            queryset = queryset.filter(requested_by=request.user)
        export_job = get_object_or_404(queryset, pk=pk)
        if export_job.status != MonthlyProductionExportJob.Status.SUCCESS or not export_job.file:
            messages.error(request, "Файл экспорта ещё не готов.")
            return redirect("notification_list")
        return FileResponse(
            export_job.file.open("rb"),
            as_attachment=True,
            filename=export_job.original_filename,
        )


# ---------------------------------------------------------------------------
# Dashboard — Admin и Manager; Operator — 403
# ---------------------------------------------------------------------------

class DashboardView(AdminOrManagerMixin, TemplateView):
    required_permissions = (
        "companies.view_oilcompany",
        "productions.view_well",
        "productions.view_dailyproduction",
        "accounts.view_profile",
    )
    template_name = "productions/dashboard.html"

    def _get_cache_version(self):
        try:
            version = cache.get(settings.DASHBOARD_CACHE_VERSION_KEY)
            if version is None:
                cache.set(settings.DASHBOARD_CACHE_VERSION_KEY, 1, None)
                version = 1
            return version
        except Exception:
            return 1

    def _build_cache_key(self, company_ids, date_from, date_to):
        raw = json.dumps(
            {
                "company_ids": sorted(company_ids),
                "date_from": date_from or "",
                "date_to": date_to or "",
                "version": self._get_cache_version(),
            },
            sort_keys=True,
            ensure_ascii=False,
        )
        digest = hashlib.md5(raw.encode("utf-8")).hexdigest()
        return f"dashboard:analytics:{digest}"

    def _build_payload(self, company_ids, date_from, date_to):
        oil_formula = ExpressionWrapper(
            F("liquid_debit")
            * (Value(Decimal("1.0")) - F("water_cut") / Value(Decimal("100.0")))
            * F("oil_density"),
            output_field=DecimalField(max_digits=14, decimal_places=4),
        )

        reports_qs = DailyProduction.objects.select_related("well", "well__oil_company")
        wells_qs = Well.objects.select_related("oil_company")
        profiles_qs = Profile.objects.select_related("oil_company")
        companies_qs = OilCompany.objects.all()

        if company_ids:
            reports_qs = reports_qs.filter(well__oil_company_id__in=company_ids)
            wells_qs = wells_qs.filter(oil_company_id__in=company_ids)
            profiles_qs = profiles_qs.filter(oil_company_id__in=company_ids)
            companies_qs = companies_qs.filter(id__in=company_ids)

        if date_from:
            reports_qs = reports_qs.filter(date__gte=date_from)
        if date_to:
            reports_qs = reports_qs.filter(date__lte=date_to)

        production_by_date = (
            reports_qs.values("date")
            .annotate(
                total_oil=Coalesce(
                    Sum(oil_formula), 0,
                    output_field=DecimalField(max_digits=14, decimal_places=4),
                )
            )
            .order_by("date")
        )

        line_labels = [item["date"].strftime("%Y-%m-%d") for item in production_by_date]
        line_data = [float(item["total_oil"]) for item in production_by_date]

        production_by_well = (
            reports_qs.values("well__name")
            .annotate(
                total_oil=Coalesce(
                    Sum(oil_formula), 0,
                    output_field=DecimalField(max_digits=14, decimal_places=4),
                )
            )
            .order_by("-total_oil", "well__name")[:10]
        )

        bar_labels = [item["well__name"] for item in production_by_well]
        bar_data = [float(item["total_oil"]) for item in production_by_well]

        wells_by_company = (
            wells_qs.values("oil_company__name")
            .annotate(wells_count=Count("id"))
            .order_by("oil_company__name")
        )
        pie_labels = [item["oil_company__name"] for item in wells_by_company]
        pie_data = [item["wells_count"] for item in wells_by_company]

        users_by_company = (
            profiles_qs.exclude(oil_company__isnull=True).values("oil_company__name")
            .annotate(users_count=Count("id"))
            .order_by("oil_company__name")
        )
        doughnut_labels = [item["oil_company__name"] for item in users_by_company]
        doughnut_data = [item["users_count"] for item in users_by_company]

        return {
            "total_companies": companies_qs.count(),
            "total_wells": wells_qs.count(),
            "total_users": profiles_qs.count(),
            "total_reports": reports_qs.count(),
            "line_labels": line_labels,
            "line_data": line_data,
            "bar_labels": bar_labels,
            "bar_data": bar_data,
            "pie_labels": pie_labels,
            "pie_data": pie_data,
            "doughnut_labels": doughnut_labels,
            "doughnut_data": doughnut_data,
        }

    def _get_dashboard_payload(self, company_ids, date_from, date_to):
        cache_key = self._build_cache_key(company_ids, date_from, date_to)
        try:
            cached_payload = cache.get(cache_key)
            if cached_payload is not None:
                return cached_payload, "hit"
        except Exception:
            pass

        payload = self._build_payload(company_ids, date_from, date_to)
        try:
            cache.set(cache_key, payload, settings.DASHBOARD_CACHE_TIMEOUT)
            return payload, "miss"
        except Exception:
            return payload, "off"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        if is_admin(user):
            company_ids = [cid for cid in self.request.GET.getlist("company") if cid]
            context["companies"] = OilCompany.objects.order_by("name")
        else:
            user_company = get_user_company(user)
            company_ids = [str(user_company.id)] if user_company else []
            context["companies"] = (
                OilCompany.objects.filter(id=user_company.id)
                if user_company else OilCompany.objects.none()
            )

        date_from = self.request.GET.get("date_from", "")
        date_to = self.request.GET.get("date_to", "")

        payload, cache_state = self._get_dashboard_payload(company_ids, date_from, date_to)

        context["selected_companies"] = company_ids
        context["date_from"] = date_from
        context["date_to"] = date_to
        context["cache_state"] = cache_state

        context["total_companies"] = payload["total_companies"]
        context["total_wells"] = payload["total_wells"]
        context["total_users"] = payload["total_users"]
        context["total_reports"] = payload["total_reports"]

        context["line_labels"] = json.dumps(payload["line_labels"], ensure_ascii=False)
        context["line_data"] = json.dumps(payload["line_data"])
        context["bar_labels"] = json.dumps(payload["bar_labels"], ensure_ascii=False)
        context["bar_data"] = json.dumps(payload["bar_data"])
        context["pie_labels"] = json.dumps(payload["pie_labels"], ensure_ascii=False)
        context["pie_data"] = json.dumps(payload["pie_data"])
        context["doughnut_labels"] = json.dumps(payload["doughnut_labels"], ensure_ascii=False)
        context["doughnut_data"] = json.dumps(payload["doughnut_data"])

        context["is_admin"] = is_admin(user)
        context["is_manager"] = is_manager(user)

        return context


# ---------------------------------------------------------------------------
# Вспомогательные функции форм
# ---------------------------------------------------------------------------

def _scope_company_in_form(form, user) -> None:
    if is_admin(user):
        return
    user_company = get_user_company(user)
    if user_company and "oil_company" in form.fields:
        form.fields["oil_company"].queryset = OilCompany.objects.filter(id=user_company.id)
        form.fields["oil_company"].initial = user_company


def _scope_well_queryset(form, user) -> None:
    if is_admin(user):
        return
    user_company = get_user_company(user)
    if user_company:
        form.fields["well"].queryset = (
            Well.objects.filter(oil_company=user_company).select_related("oil_company")
        )
    else:
        form.fields["well"].queryset = Well.objects.none()