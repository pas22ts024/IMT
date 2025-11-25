from django.contrib.auth.models import User
from django.db import connection
from django.shortcuts import render, redirect
from django.utils import timezone

from app.models import Category, Imt, CategoryImt


def index(request):
    category_name = request.GET.get("category_name", "")
    categorys = Category.objects.filter(status=1)

    if category_name:
        categorys = categorys.filter(name__icontains=category_name)

    context = {
        "category_name": category_name,
        "categorys": categorys
    }

    draft_imt = get_draft_imt()
    if draft_imt:
        context["categorys_count"] = len(draft_imt.categoryimt_set.all())
        context["draft_imt"] = draft_imt

    return render(request, "categorys_page.html", context)


def category_page(request, category_id):
    if not Category.objects.filter(pk=category_id).exists():
        return redirect("/")

    context = {
        "category": Category.objects.get(id=category_id)
    }

    return render(request, "category_page.html", context)


def imt_page(request, imt_id):
    if not Imt.objects.filter(pk=imt_id).exists():
        return redirect("/")

    imt = Imt.objects.get(id=imt_id)
    if imt.status == 5:
        return render(request, "imt_removed.html")

    context = {
        "imt": imt,
        "items": imt.categoryimt_set.all()
    }

    return render(request, "imt_page.html", context)


def add_category_to_draft_imt(request, category_id):
    category_name = request.POST.get("category_name")
    redirect_url = f"/?category_name={category_name}" if category_name else "/"

    if not Category.objects.filter(pk=category_id).exists():
        return redirect(redirect_url)

    draft_imt = get_draft_imt()
    if draft_imt is None:
        draft_imt = Imt.objects.create()
        draft_imt.owner = get_current_user()
        draft_imt.date_created = timezone.now()
        draft_imt.save()

    category = Category.objects.get(pk=category_id)
    if CategoryImt.objects.filter(imt=draft_imt, category=category).exists():
        return redirect(redirect_url)

    item = CategoryImt(
        imt=draft_imt,
        category=category
    )
    item.save()

    return redirect(redirect_url)


def delete_imt(request, imt_id):
    if not Imt.objects.filter(pk=imt_id).exists():
        return redirect("/")

    with connection.cursor() as cursor:
        cursor.execute("UPDATE imts SET status=5 WHERE id = %s", [imt_id])

    return redirect("/")


def get_draft_imt():
    return Imt.objects.filter(status=1).first()


def get_current_user():
    return User.objects.filter(is_superuser=False).first()