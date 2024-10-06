# DjTInvest

Учет инвестиций и (пока в будущем) расчет портфеля исходя из индексов или по другим параметрам.
В чем-то будет похоже на табличку от [t.me/Finindie](https://t.me/Finindie), но с более широким функционалом.

На данный момент - во многом, это preBeta версия. Но часть уже работает.

## Установка

* Скачать и установить зависимости, прописанные в requirements.txt. Требуется python3.11 и старше
* прописать в файле djtinvest/settings.py токен для инвестирования в Т-Банке. Строка `TINKOFF_API_KEY` в самом низу файла.
* В том же файле - Изменить секретную строку (`SECRET_KEY`) для Django на свою.
* запустить `init.sh`
  * прописать имя и пароль для суперпользователя - потребуется для доступа к базе напрямую и изменения некоторых параметров
  * подождать пока прогрузятся счета, операции, портфолио, курсы валют и прочая информация
* Запустить сервер командой `python3.11 manage.py runserver`
* перейти в браузере по адресу [localhost:8000](http://localhost:8000)
* управлять своими инвестициями

## Ссылки

* [TBank - investAPI description](https://russianinvestments.github.io/investAPI/)
* [TBank - invest-python Github](https://github.com/RussianInvestments/invest-python/tree/main)
