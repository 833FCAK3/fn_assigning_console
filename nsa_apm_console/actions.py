import sys
from abc import ABC, abstractmethod

import click
import requests

from nsa_apm_console import settings
from nsa_apm_console.utils import (
    get_order_id,
    logger,
    login,
    logout,
    prompt_decimal_number,
    prompt_order_number,
    prompt_order_year,
    read_fn,
    write_fn,
)


class ActionError(Exception):
    pass


class Action(ABC):
    # Название действия, которое будет отображено в списке действий
    title: str = ""

    @abstractmethod
    def execute(self):
        """Выполняет логику действия"""
        pass


class WriteFN(Action):
    title = "Присвоить продукту заводской номер"

    @staticmethod
    @click.pass_obj
    def execute(ctx):
        """Создаёт ЗН в ЕБД и записывает его в датчик"""
        # Получение id заказа по номеру
        order_id = ctx["order_id"] = get_order_id(ctx["order_number"])
        if not order_id:
            return

        # Создание ЗН в ЕБД
        if not ctx["factory_number"]:
            create_fn_product_response = requests.post(
                settings.PRODUCTS_URL,
                json={
                    "order_id": order_id,
                    "decimal_number": ctx["decimal_number"],
                    "status": "Годен",
                },
                headers={
                    "X-API-KEY": settings.API_KEY,
                    "Authorization": f"Bearer {ctx['token']}",
                },
            )
        else:
            print()
            logger.warning(
                f'{ctx["factory_number"]} не был записан.\nВыполните пункт меню 2'
            )
            return

        content = create_fn_product_response.json()
        if create_fn_product_response.status_code == 201:
            factory_number = ctx["factory_number"] = content["factory_number"]
            logger.info(f"Создан продукт с заводским номером {factory_number}")
        elif create_fn_product_response.status_code in (404, 409):
            raise ActionError(f"{content['detail']}")
        elif create_fn_product_response.status_code == 422:
            raise ActionError(
                f"{content['detail'][0]['loc'][1]}: {content['detail'][0]['msg']}"
            )

        # Запись ЗН в датчик
        write_fn(factory_number)

        # Проверка корректности записи заводского номера
        _check_written_fn(factory_number)
        ctx.pop("factory_number")

        logger.info(
            f"Заказ номер {ctx['order_number']}\nПродукту с децимальным номером {ctx['decimal_number']}\n"
            f"Присвоен заводской номер {factory_number}"
        )


class WriteLastFN(Action):
    title = "Повторить попытку записи последнего полученного заводского номера"

    @staticmethod
    @click.pass_obj
    def execute(ctx):
        if not ctx["factory_number"]:
            print()
            logger.warning("Выполните присвоение заводского номера, пункт меню 1")
        else:
            write_fn(ctx["factory_number"])
            _check_written_fn(ctx["factory_number"])
            logger.info(
                f"Заказ номер {ctx['order_number']}\nПродукту с децимальным номером {ctx['decimal_number']}\n"
                f"Присвоен заводской номер {ctx['factory_number']}"
            )


@click.pass_obj
def _check_written_fn(ctx, factory_number) -> None:
    """Проверка факта записи заводского номера"""
    fn_read = read_fn(ctx["product"])
    if fn_read != int(factory_number):
        raise ActionError(
            "Не удалось записать заводской номер:\n"
            f"Записываемый {factory_number} и считанный {fn_read} номера не совпадают"
        )


class Relogin(Action):
    title = "Cменить пользователя"

    @staticmethod
    @click.pass_obj
    def execute(ctx):
        logout()
        ctx["token"] = login()


class ChangeOrder(Action):
    title = "Изменить номер заказа"

    @staticmethod
    @click.pass_obj
    def execute(ctx):
        ctx["order_number"] = prompt_order_number()


class ChangeOrderYear(Action):
    title = "Изменить год заказа"

    @staticmethod
    @click.pass_obj
    def execute(ctx):
        ctx["order_year"] = prompt_order_year()


class ChangeDN(Action):
    title = "Изменить децимальный номер"

    @staticmethod
    @click.pass_obj
    def execute(ctx):
        ctx["decimal_number"] = prompt_decimal_number()


class ReadFN(Action):
    title = "Считать заводской номер"

    @staticmethod
    @click.pass_obj
    def execute(ctx):
        fn = read_fn(ctx["product"])
        print()
        logger.info(f"Считанный заводской номер: {fn}")


class ShowParams(Action):
    title = "Отобразить параметры"

    @staticmethod
    @click.pass_obj
    def execute(ctx):
        print()
        logger.info(
            "Текущие параметры:\n"
            f"Сотрудник: {ctx['username']}\n"
            f"Номер заказа: {ctx['order_number']}\n"
            f"Год заказа: {ctx['order_year']}\n"
            f"Децимальный номер продукта: {ctx['decimal_number']}"
        )


class Exit(Action):
    title = "Выход"

    @staticmethod
    def execute():
        logout()
        sys.exit()


actions = [
    WriteFN,
    WriteLastFN,
    ChangeOrder,
    ChangeOrderYear,
    ChangeDN,
    ReadFN,
    Relogin,
    ShowParams,
    Exit,
]

action_list = "\n".join(
    f"{n}. {action.title}" for n, action in enumerate(actions, start=1)
)
