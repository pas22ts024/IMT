from django.core.management.base import BaseCommand

from app.calc import calc
from app.models import *
from app.utils import *


def add_users():
    User.objects.create_user("user", "user@user.com", "1234", first_name="user", last_name="user")
    User.objects.create_superuser("root", "root@root.com", "1234", first_name="root", last_name="root")

    for i in range(2, 10):
        User.objects.create_user(f"user{i}", f"user{i}@user.com", "1234", first_name=f"user{i}", last_name=f"user{i}")
        User.objects.create_superuser(f"root{i}", f"root{i}@root.com", "1234", first_name=f"user{i}", last_name=f"user{i}")


def add_categorys():
    Category.objects.create(
        name="Ребенок",
        sex="Мужской",
        age="12-18",
        image="1.png"
    )

    Category.objects.create(
        name="Ребенок",
        sex="Женский",
        age="12-18",
        image="2.png"
    )

    Category.objects.create(
        name="Взрослый",
        sex="Мужской",
        age="12-18",
        image="3.png"
    )

    Category.objects.create(
        name="Взрослый",
        sex="Женский",
        age="12-18",
        image="4.png"
    )

    Category.objects.create(
        name="Пожилой",
        sex="Мужской",
        age="60-100",
        image="5.png"
    )

    Category.objects.create(
        name="Пожилой",
        sex="Женский",
        age="60-100",
        image="6.png"
    )


def add_imts():
    users = User.objects.filter(is_staff=False)
    moderators = User.objects.filter(is_staff=True)
    categorys = Category.objects.all()

    for _ in range(30):
        status = random.randint(2, 5)
        owner = random.choice(users)
        add_imt(status, categorys, owner, moderators)

    # add_imt(1, categorys, users[0], moderators)
    add_imt(2, categorys, users[0], moderators)
    add_imt(3, categorys, users[0], moderators)
    add_imt(4, categorys, users[0], moderators)
    add_imt(5, categorys, users[0], moderators)

    for _ in range(10):
        status = random.randint(2, 5)
        add_imt(status, categorys, users[0], moderators)


def add_imt(status, categorys, owner, moderators):
    imt = Imt.objects.create()
    imt.status = status

    if status in [3, 4]:
        imt.moderator = random.choice(moderators)
        imt.date_complete = random_date()
        imt.date_formation = imt.date_complete - random_timedelta()
        imt.date_created = imt.date_formation - random_timedelta()
    else:
        imt.date_formation = random_date()
        imt.date_created = imt.date_formation - random_timedelta()

    imt.related = random_bool()

    imt.owner = owner

    for category in random.sample(list(categorys), 3):
        item = CategoryImt(
            imt=imt,
            category=category,
            weight=random.randint(160, 200),
            height=random.randint(50, 100),
        )

        if imt.status == 3:
            item.factor = calc(imt, item)

        item.save()

    imt.save()


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        add_users()
        add_categorys()
        add_imts()
