from django.shortcuts import render

categorys_mock = [
    {
        "id": 1,
        "name": "Ребенок",
        "sex": "Мужской",
        "age": "12-18",
        "image": "http://localhost:9000/images/1.png"
    },
    {
        "id": 2,
        "name": "Ребенок",
        "sex": "Женский",
        "age": "12-18",
        "image": "http://localhost:9000/images/2.png"
    },
    {
        "id": 3,
        "name": "Взрослый",
        "sex": "Мужской",
        "age": "18-60",
        "image": "http://localhost:9000/images/3.png"
    },
    {
        "id": 4,
        "name": "Взрослый",
        "sex": "Женский",
        "age": "18-60",
        "image": "http://localhost:9000/images/4.png"
    },
    {
        "id": 5,
        "name": "Пожилой",
        "sex": "Мужской",
        "age": "60-100",
        "image": "http://localhost:9000/images/5.png"
    },
    {
        "id": 6,
        "name": "Пожилой",
        "sex": "Женский",
        "age": "60-100",
        "image": "http://localhost:9000/images/6.png"
    }
]

imts_mock = [
    {
        "id": 1,
        "status": "Черновик",
        "date_created": "5 сентября 2025г",
        "related": "Да",
        "categorys": [
            {
                "id": 1,
                "weight": 80,
                "height": 180,
                "imt": "Не рассчитано"
            },
            {
                "id": 2,
                "weight": 60,
                "height": 170,
                "imt": "Не рассчитано"
            },
            {
                "id": 3,
                "weight": 50,
                "height": 160,
                "imt": "Не рассчитано"
            }
        ]
    },
    {
        "id": 2,
        "status": "В работе",
        "date_created": "3 сентября 2025г",
        "related": "Да",
        "categorys": [
            {
                "id": 1,
                "weight": 60,
                "height": 170,
                "imt": "Норма"
            },
            {
                "id": 3,
                "weight": 50,
                "height": 170,
                "imt": "Ожирение"
            }
        ]
    },
    {
        "id": 3,
        "status": "Завершена",
        "date_created": "27 августа 2025г",
        "related": "Да",
        "categorys": [
            {
                "id": 2,
                "weight": 60,
                "height": 170,
                "imt": "Дефицит"
            }
        ]
    }
]


def get_category(category_id):
    for category in categorys_mock:
        if category["id"] == category_id:
            return category


def get_categorys():
    return categorys_mock


def search_categorys(category_name):
    res = []

    for category in categorys_mock:
        if category_name.lower() in category["name"].lower():
            res.append(category)

    return res


def get_draft_imt():
    for imt in imts_mock:
        if imt["status"] == "Черновик":
            return imt


def get_imt(imt_id):
    for imt in imts_mock:
        if imt["id"] == imt_id:
            return imt


def index(request):
    category_name = request.GET.get("category_name", "")
    categorys = search_categorys(category_name) if category_name else get_categorys()
    draft_imt = get_draft_imt()

    context = {
        "categorys": categorys,
        "category_name": category_name,
        "categorys_count": len(draft_imt["categorys"]),
        "draft_imt": draft_imt
    }

    return render(request, "categorys_page.html", context)


def category_page(request, category_id):
    context = {
        "category": get_category(category_id),
    }

    return render(request, "category_page.html", context)


def imt_page(request, imt_id):
    imt = get_imt(imt_id)
    categorys = [
        {
            **get_category(category["id"]),
             "weight": category["weight"],
             "height": category["height"],
             "imt": category["imt"]
        }
        for category in imt["categorys"]
    ]

    context = {
        "imt": imt,
        "categorys": categorys
    }

    return render(request, "imt_page.html", context)
