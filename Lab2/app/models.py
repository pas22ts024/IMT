from django.db import models

from django.contrib.auth.models import User


class Category(models.Model):
    STATUS_CHOICES = (
        (1, 'Действует'),
        (2, 'Удалена'),
    )

    name = models.CharField(max_length=100, verbose_name="Название")
    status = models.IntegerField(choices=STATUS_CHOICES, default=1, verbose_name="Статус")
    image = models.ImageField(blank=True, null=True, default='default.png')
    description = models.TextField(verbose_name="Описание")

    sex = models.CharField(verbose_name="Пол")
    age = models.CharField(verbose_name="Возраст")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Пациент"
        verbose_name_plural = "Пациенты"
        db_table = "categorys"
        ordering = ("pk",)


class Imt(models.Model):
    STATUS_CHOICES = (
        (1, 'Введён'),
        (2, 'В работе'),
        (3, 'Завершен'),
        (4, 'Отклонен'),
        (5, 'Удален')
    )

    status = models.IntegerField(choices=STATUS_CHOICES, default=1, verbose_name="Статус")
    date_created = models.DateTimeField(verbose_name="Дата создания", auto_now_add=True)
    date_formation = models.DateTimeField(verbose_name="Дата формирования", blank=True, null=True)
    date_complete = models.DateTimeField(verbose_name="Дата завершения", blank=True, null=True)

    owner = models.ForeignKey(User, on_delete=models.DO_NOTHING, verbose_name="Пользователь", null=True, related_name='owner')
    moderator = models.ForeignKey(User, on_delete=models.DO_NOTHING, verbose_name="Врач", null=True, related_name='moderator')

    related = models.BooleanField(blank=True, null=True)

    def __str__(self):
        return "Заключение №" + str(self.pk)

    class Meta:
        verbose_name = "Заключение"
        verbose_name_plural = "Заключения"
        db_table = "imts"
        ordering = ('-date_formation',)


class CategoryImt(models.Model):
    pk = models.CompositePrimaryKey("category_id", "imt_id")
    category = models.ForeignKey(Category, on_delete=models.DO_NOTHING)
    imt = models.ForeignKey(Imt, on_delete=models.DO_NOTHING)

    weight = models.IntegerField(default=0)
    height = models.IntegerField(default=0)

    # Вычисляемое поле
    factor = models.FloatField(blank=True, null=True)

    def __str__(self):
        return "м-м №" + str(self.pk)

    class Meta:
        verbose_name = "м-м"
        verbose_name_plural = "м-м"
        db_table = "category_imt"
        ordering = ('pk', )
