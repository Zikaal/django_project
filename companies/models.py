from django.db import models

class OilCompany(models.Model):
    name = models.CharField("Название компании", max_length=255, unique=True)
    region = models.CharField("Регион", max_length=255)

    def __str__(self):
        return self.name
