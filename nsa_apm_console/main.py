import click
from pga900_product.pga900 import PGA900

from nsa_apm_console import settings
from nsa_apm_console.loop import loop
from nsa_apm_console.utils import (
    logger,
    login,
    prompt_decimal_number,
    prompt_order_number,
    prompt_order_year,
)


@click.command()
@click.pass_context
def scenario(ctx):
    """Осуществляет аутентификацию пользователя, инициализацию параметров заказа, запуск меню"""
    ctx.obj = {}
    ctx.obj["product"] = PGA900(settings.PGA900_CONFIG, logger)
    ctx.obj["product"]._configuration["permission"] = "factory"
    ctx.obj["factory_number"] = None
    ctx.obj["token"] = login()
    ctx.obj["order_number"] = prompt_order_number()
    ctx.obj["decimal_number"] = prompt_decimal_number()
    ctx.obj["order_year"] = prompt_order_year()
    loop()


def run():
    scenario()


if __name__ == "__main__":
    run()
