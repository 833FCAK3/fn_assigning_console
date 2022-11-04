import json
from getpass import getpass
from typing import List

import click
import requests
from loggers.console_logger import ConsoleLogger
from pga900_product.pga900 import PGA900
from requests.exceptions import ConnectionError

from nsa_apm_console import settings

logger = ConsoleLogger(level="info")


@click.pass_obj
def get_order_id(ctx, order_number) -> str:
    """Получение id заказа"""
    # Поисковый запрос
    order_id_response = requests.post(
        settings.ORDER_SEARCH_URL,
        data=json.dumps(
            {"request": order_number},
        ),
        headers={
            "X-API-KEY": settings.API_KEY,
            "Authorization": f"Bearer {ctx['token']}",
        },
    )
    content: dict = order_id_response.json()

    # Проверка найден ли хоть один заказ
    if len(content["search_result"]) < 1:
        print()
        logger.warning(f"Заказ с номером {order_number} не найден\n")
        return False

    if order_id_response.status_code == 200:
        if len(content["search_result"]) == 0:
            print()
            logger.warning(f"Заказ с номером {order_number} не найден\n")
            return False

        # Форсим точное совпадение номера заказа
        if len(content["search_result"]) > 1:
            for _, order in enumerate(content["search_result"].copy()):
                if order["number"] != int(order_number):
                    content["search_result"].pop(_)

        # Отсеиваем по году запуска
        if len(content["search_result"]) > 1:
            created_at = [date["created_at"][:4] for date in content["search_result"]]
            try:
                order_index = created_at.index(ctx["order_year"])
            except ValueError:
                print()
                logger.warning(
                    f"Заказа с номером {order_number}, созданного в {ctx['order_year']} году не существует. "
                    f"Проверьте год заказа.\n"
                )
                return False
            order_id = content["search_result"][order_index]["id"]
    else:
        print()
        logger.warning(f"Не удалось получить id заказа:\n{order_id_response}")
        return False

    return order_id


@click.pass_obj
def write_fn(ctx, factory_number) -> List[int]:
    """Запись заводского номера в память датчика.
    Returns:
        Лист содержащий год + месяц и номер: [2210, 1]"""
    logger.info(f"Присвоение заводского номера {factory_number} датчику")
    factory_number = format_fn(ctx["factory_number"])
    ctx["product"].write_register(settings.FN_REGISTER, factory_number)
    return factory_number


def format_fn(factory_number: str) -> List[int]:
    """Преобразует ЗН в нужный для записи формат"""
    year = int(factory_number[:2])
    month = int(factory_number[2:4])
    factory_number = int(factory_number[4:])
    date_prefix = (year << 4) + (month)
    hex_factory_number = (date_prefix << 20) + int(factory_number)
    hex_date = int(hex(hex_factory_number)[2:6], 16)
    return [hex_date, factory_number]


def read_fn(product: PGA900) -> int:
    """Считывает заводской номер"""
    raw_fn = product.read_register(settings.FN_REGISTER).content["value"]
    fn = str(raw_fn[1])
    raw_date = hex(raw_fn[0])[2:]
    year = str(int(raw_date[:2], 16))
    month = str(int(raw_date[2:3], 16))
    date = year + month
    full_fn = date + fn
    for _ in range(10 - len(full_fn)):
        full_fn = full_fn[:4] + "0" + full_fn[4:]
    full_fn = int(full_fn)

    return full_fn


@click.pass_obj
def login(ctx) -> str:
    """Осуществляет аутентификацию и возвращает токен доступа"""
    logged_in = None
    while not logged_in:
        username = ctx["username"] = input("Введите ваш логин:\n")
        pswd = getpass("Введите ваш пароль:\n")

        try:
            login_response = requests.post(
                settings.LOGIN_URL,
                data=json.dumps(
                    {"username": username, "password": pswd},
                ),
                headers={"X-API-KEY": settings.API_KEY},
            )
        except ConnectionError as e:
            print()
            logger.warning(
                f"Не удалось подключиться к серверу. "
                f"Проверьте его доступность или корректность адреса подключения:\n {str(e)}"
            )
            continue

        content = login_response.json()
        if login_response.status_code == 200:
            logged_in = True
        if login_response.status_code == 401:
            print()
            logger.warning(f'Неверные логин или пароль\n{content["detail"]}')
        if login_response.status_code == 403:
            print()
            logger.warning(f'Неверный API ключ\n{content["detail"]}')
        if login_response.status_code == 404:
            print()
            logger.warning(
                f'Сотрудник {username} не найден в базе данных сервиса ЕБД\n{content["detail"]}'
            )

    token = login_response.json().get("token")
    return token


@click.pass_obj
def logout(ctx) -> None:
    """Аннулирует текущий токен доступа"""
    requests.post(
        settings.LOGOUT_URL,
        headers={
            "X-API-KEY": settings.API_KEY,
            "Authorization": "Bearer" + ctx["token"],
        },
    )


def prompt_decimal_number():
    dn = input("Введите децимальный номер продукта:\n")
    return dn


def prompt_order_number():
    number = input("Введите номер заказа:\n")
    return number


def prompt_order_year():
    year = input("Введите год заказа (например 2022):\n")
    return year
