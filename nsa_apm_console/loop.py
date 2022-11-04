import time

from interface_vip.protocol import ProtocolError
from pga900_product.pga900 import PGA900Error
from requests.exceptions import ConnectionError

from nsa_apm_console.actions import Action, ActionError, action_list, actions
from nsa_apm_console.utils import logger


def loop() -> None:
    """Меню консоли"""
    while True:
        n = input("\nВыберите действие:\n" f"{action_list}\n\n")

        try:
            current_action: Action = actions[int(n) - 1]
            current_action.execute()
        except (PGA900Error, ProtocolError, ActionError) as e:
            print()
            logger.warning(f"Не удалось {current_action.title}: \n" + str(e))
        except ConnectionError as e:
            print()
            logger.warning(
                f"Не удалось подключиться к серверу. "
                f"Проверьте его доступность или корректность адреса подключения:\n {str(e)}"
            )
        except (IndexError, ValueError) as e:
            time.sleep(0.5)
