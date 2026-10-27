# dbf2pg: перенос данных DBF (Visual FoxPro) в PostgreSQL

Схемой базы владеет веб-приложение: модели строит `manage.py dbf_inspect`, таблицы создаёт
`manage.py migrate`. dbf2pg только наполняет эти таблицы и доказывает, что ничего не потерялось.

## Порядок работы

1. Скопируйте папку программы с .dbf/.fpt в отдельное место. Скрипт ничего не пишет в DBF,
   но работать лучше на копии.
2. В веб-приложении: `python manage.py dbf_inspect --dir КОПИЯ --output catalogs/models.py`.
3. Анализ ключей и связей:
   ```
   python migration/dbf2pg/dbf2pg.py analyze --src КОПИЯ --models catalogs/models.py
   ```
   В `report.md` будет таблица с кодировками и ключами и готовые строки `unique=True` и `ForeignKey`
   для catalogs/models.py. Перенесите их в модели и посмотрите раздел «значения без пары».
4. `python manage.py makemigrations catalogs && python manage.py migrate`.
5. Перенос и сверка:
   ```
   python migration/dbf2pg/dbf2pg.py all --src КОПИЯ --models catalogs/models.py \
       --dsn "host=localhost dbname=teplo user=teplo password=..."
   ```
   Код выхода 0, если все таблицы совпали. Повторный запуск сначала очищает таблицы.

## Команда для программы teplo_dog

Рабочие таблицы лежат в `D:\teplo_dog\dbf`. Папка `DATA` не используется, `sul.dbf` и `poisk_ab.dbf`
не переносятся. Главная таблица городов — `danrasch` (cod_gorod, name_gorod).

```
python migration/dbf2pg/dbf2pg.py all --src КОПИЯ_dbf --models catalogs/models.py ^
    --dbc КОПИЯ_dbf/ur_teplo.dbc --exclude sul.dbf,poisk_ab.dbf ^
    --link "*.cod_gor=danrasch.cod_gorod" --link "gvs_kot.kod_gor=danrasch.cod_gorod" ^
    --fix "potreb.accept:0=1" --fix "potreb.accept:=1" --dsn "host=localhost dbname=teplo user=teplo password=..."
```

- `--dbc` берёт ключи таблиц из словаря базы VFP;
- `--link` задаёт связь вручную, `*.поле` значит во всех таблицах, где есть это поле;
- `--exclude` пропускает файлы или папки;
- `--fix` исправляет значение при переносе: в `potreb.accept` (поле «Акцепт») 0 и пустое значение
  недопустимы, ставится 1 (так же делает импорт карточки абонента). `таблица.поле:=1` заменяет пустое.
  Сверка сравнивает с уже исправленными значениями, число исправлений печатается после загрузки.

Кроме `report.md`, `analyze` пишет `relations.json` в формате dbfsync. Положите его в
`dbfsync/labels/ur_teplo_relations.json`, и `manage.py dbf_inspect` сам проставит `unique` и `ForeignKey`.

## Что проверяет verify

По каждой таблице: число записей, число непустых значений в каждой колонке, суммы числовых колонок
и md5 всего текста колонки в порядке записей. Любое расхождение печатается с именем таблицы и колонки.

## Правила переноса

- Кодировка берётся из заголовка DBF. Если её там нет (байт 0), выбирается cp866 или cp1251
  по числу русских букв. `--encoding` задаёт её вручную для всех таблиц.
- Помеченные на удаление записи не переносятся (как при SET DELETED ON).
- `id` заполняет PostgreSQL по порядку записей в DBF.
- В колонках с внешним ключом 0 и пустая строка становятся NULL: в FoxPro это «нет ссылки».
- Битые даты и числа становятся NULL, а текст длиннее колонки обрезается. Список полей и
  количество печатаются после загрузки.
- Нулевые байты из текста удаляются, потому что PostgreSQL их не хранит.

## Тесты

```
pip install -r migration/dbf2pg/requirements.txt dbf==0.99.11 pytest
python -m pytest migration/dbf2pg
```

Тест переноса в PostgreSQL запускается, если задана переменная `DBF2PG_TEST_DSN` с адресом
пустой тестовой базы (тест создаёт и удаляет в ней таблицы danrasch, potreb, nachisl, tarif).
