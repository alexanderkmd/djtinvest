python3.11 manage.py migrate

python3.11 manage.py createsuperuser

# TODO: fill in Tinkoff API_key

echo "Подгружаем основные символы валют"
python3.11 manage.py loaddata currencies.json

echo "Подгружаем данные по банкам"
python3.11 manage.py loaddata banks.json

# Подгрузка курсов валют при помощи API за большой период - см analyzer/cbrf_client.py
python3.11 manage.py shell --command="from analyzer.tasks import preload_currencies_to_db; preload_currencies_to_db();"

