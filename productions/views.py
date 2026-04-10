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

from accounts.models import Profile
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


class WellListView(LoginRequiredMixin, ListView):
    model = Well
    template_name = "productions/well_list.html"
    context_object_name = "wells"
    paginate_by = 20

    def get_queryset(self):
        queryset = Well.objects.select_related("oil_company")

        sort = self.request.GET.get("sort", "name")
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

        context["companies"] = OilCompany.objects.order_by("name")
        context["selected_company"] = self.request.GET.get("company", "")
        context["sort"] = self.request.GET.get("sort", "name")
        context["total_count"] = self.get_queryset().count()

        query_params = self.request.GET.copy()
        query_params.pop("page", None)
        context["query_string"] = query_params.urlencode()

        return context


class WellCreateView(LoginRequiredMixin, CreateView):
    model = Well
    form_class = WellForm
    template_name = "productions/well_form.html"
    success_url = reverse_lazy("well_list")


class WellUpdateView(LoginRequiredMixin, UpdateView):
    model = Well
    form_class = WellForm
    template_name = "productions/well_form.html"
    success_url = reverse_lazy("well_list")


class WellDeleteView(LoginRequiredMixin, DeleteView):
    model = Well
    template_name = "productions/well_confirm_delete.html"
    success_url = reverse_lazy("well_list")


class DailyProductionListView(LoginRequiredMixin, ListView):
    model = DailyProduction
    template_name = "productions/dailyproduction_list.html"
    context_object_name = "reports"
    paginate_by = 20

    def get_queryset(self):
        queryset = DailyProduction.objects.select_related("well", "well__oil_company")

        sort = self.request.GET.get("sort", "-date")
        company_id = self.request.GET.get("company")
        well_id = self.request.GET.get("well")
        date_from = self.request.GET.get("date_from")
        date_to = self.request.GET.get("date_to")

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

        context["companies"] = OilCompany.objects.order_by("name")
        context["wells"] = Well.objects.select_related("oil_company").order_by("name")

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

        return context


class DailyProductionCreateView(LoginRequiredMixin, CreateView):
    model = DailyProduction
    form_class = DailyProductionForm
    template_name = "productions/dailyproduction_form.html"
    success_url = reverse_lazy("dailyproduction_list")


class DailyProductionUpdateView(LoginRequiredMixin, UpdateView):
    model = DailyProduction
    form_class = DailyProductionForm
    template_name = "productions/dailyproduction_form.html"
    success_url = reverse_lazy("dailyproduction_list")


class DailyProductionDeleteView(LoginRequiredMixin, DeleteView):
    model = DailyProduction
    template_name = "productions/dailyproduction_confirm_delete.html"
    success_url = reverse_lazy("dailyproduction_list")


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


class DailyProductionImportView(LoginRequiredMixin, FormView):
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
                (
                    f"Файл '{uploaded_file.name}' был загружен, но задачу не удалось "
                    f"отправить в очередь. Проверь Redis/Celery."
                ),
            )
            return redirect(self.success_url)

    def form_invalid(self, form):
        messages.error(self.request, "Не удалось загрузить файл. Проверьте форму.")
        return redirect(self.success_url)


class MonthlyProductionExportView(LoginRequiredMixin, FormView):
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
                (
                    f"Экспорт отчёта за {month:02d}.{year} поставлен в очередь. "
                    f"Когда файл будет готов, страница обновится автоматически."
                ),
            )
            return redirect(f"{self.success_url}?watch_notifications=1")
        else:
            messages.error(
                self.request,
                (
                    f"Запрос на экспорт за {month:02d}.{year} создан, "
                    f"но задачу не удалось отправить в очередь."
                ),
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

        response = FileResponse(
            export_job.file.open("rb"),
            as_attachment=True,
            filename=export_job.original_filename,
        )
        return response


class DashboardView(LoginRequiredMixin, TemplateView):
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
                    Sum(oil_formula),
                    0,
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
                    Sum(oil_formula),
                    0,
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
            profiles_qs.values("oil_company__name")
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
            cached_payload = None

        payload = self._build_payload(company_ids, date_from, date_to)

        try:
            cache.set(cache_key, payload, settings.DASHBOARD_CACHE_TIMEOUT)
            return payload, "miss"
        except Exception:
            return payload, "off"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        company_ids = self.request.GET.getlist("company")
        company_ids = [company_id for company_id in company_ids if company_id]

        date_from = self.request.GET.get("date_from", "")
        date_to = self.request.GET.get("date_to", "")

        payload, cache_state = self._get_dashboard_payload(company_ids, date_from, date_to)

        context["companies"] = OilCompany.objects.order_by("name")
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

        return context