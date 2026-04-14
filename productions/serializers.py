from rest_framework import serializers

from accounts.utils import get_user_company, is_admin, is_manager, is_operator
from .models import DailyProduction, Well


class WellShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Well
        fields = [
            "id",
            "name",
            "oil_company",
            "type",
            "max_drilling_depth",
        ]
        read_only_fields = fields


class DailyProductionCreateSerializer(serializers.ModelSerializer):
    """
    Сериализатор для мобильной отправки суточного рапорта.
    Принимает well как PK и валидирует доступ пользователя к этой скважине.
    """

    class Meta:
        model = DailyProduction
        fields = [
            "id",
            "well",
            "date",
            "work_time",
            "liquid_debit",
            "water_cut",
            "oil_density",
        ]
        read_only_fields = ["id"]
        validators = []
        extra_kwargs = {
            "well": {
                "error_messages": {
                    "required": "Выберите скважину.",
                    "does_not_exist": "Скважина не найдена.",
                    "incorrect_type": "Некорректный идентификатор скважины.",
                }
            },
            "date": {
                "error_messages": {
                    "required": "Укажите дату.",
                    "invalid": "Введите корректную дату.",
                }
            },
            "work_time": {
                "error_messages": {
                    "required": "Укажите время работы.",
                    "invalid": "Введите корректное значение времени работы.",
                }
            },
            "liquid_debit": {
                "error_messages": {
                    "required": "Укажите дебит жидкости.",
                    "invalid": "Введите корректное значение дебита жидкости.",
                }
            },
            "water_cut": {
                "error_messages": {
                    "required": "Укажите обводненность.",
                    "invalid": "Введите корректное значение обводненности.",
                }
            },
            "oil_density": {
                "error_messages": {
                    "required": "Укажите плотность нефти.",
                    "invalid": "Введите корректное значение плотности нефти.",
                }
            },
        }

    def validate_well(self, well):
        """
        Проверяем, что пользователь может работать с этой скважиной.
        Admin — любая скважина.
        Manager / Operator — только скважины своей компании.
        """
        request = self.context.get("request")
        user = getattr(request, "user", None)

        if not user or not user.is_authenticated:
            raise serializers.ValidationError("Требуется авторизация.")

        if is_admin(user):
            return well

        user_company = get_user_company(user)
        if user_company is None:
            raise serializers.ValidationError("Пользователь не привязан к компании.")

        if well.oil_company_id != user_company.id:
            raise serializers.ValidationError(
                "Нельзя отправить рапорт по скважине чужой компании."
            )

        return well

    def validate_water_cut(self, value):
        if value < 0 or value > 100:
            raise serializers.ValidationError(
                "Обводненность должна быть в диапазоне от 0 до 100."
            )
        return value

    def validate_work_time(self, value):
        if value < 0:
            raise serializers.ValidationError(
                "Время работы не может быть отрицательным."
            )
        return value

    def validate_liquid_debit(self, value):
        if value < 0:
            raise serializers.ValidationError(
                "Дебит жидкости не может быть отрицательным."
            )
        return value

    def validate_oil_density(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                "Плотность нефти должна быть больше нуля."
            )
        return value

    def validate(self, attrs):
        """
        Проверяем:
        1) роль пользователя,
        2) уникальность well + date,
        3) дополнительные бизнес-ограничения.
        """
        request = self.context.get("request")
        user = getattr(request, "user", None)

        if not user or not user.is_authenticated:
            raise serializers.ValidationError("Требуется авторизация.")

        if not (is_admin(user) or is_manager(user) or is_operator(user)):
            raise serializers.ValidationError(
                {"detail": "У пользователя нет роли для отправки рапорта."}
            )

        well = attrs.get("well")
        date = attrs.get("date")

        if well and date:
            if DailyProduction.objects.filter(well=well, date=date).exists():
                raise serializers.ValidationError(
                    {"date": "Для этой скважины уже есть запись на эту дату."}
                )

        return attrs


class DailyProductionReadSerializer(serializers.ModelSerializer):
    well = WellShortSerializer(read_only=True)
    calculated_oil = serializers.DecimalField(
        max_digits=14,
        decimal_places=4,
        read_only=True,
    )

    class Meta:
        model = DailyProduction
        fields = [
            "id",
            "well",
            "date",
            "work_time",
            "liquid_debit",
            "water_cut",
            "oil_density",
            "calculated_oil",
        ]
        read_only_fields = fields