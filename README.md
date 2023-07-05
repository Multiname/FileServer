# Запуск приложения
Зависимости проекта хранятся в файле `requirements.txt`

Запуск сервера производится командой `python runner.py`

Файлы, с которыми работает сервер и БД, хранятся в папке `server_files`

Для изменения этой директории необходимо указать нужный путь в `BaseConfig.UPLOAD_FODLER` в `config.py`, сохраняя формат `/path`

# Описание API
## get_files_info/
- Краткое описание: `получение информации по всем файлам`
- Метод: `GET`
- Формат запроса: `/`
- Формат ответа: `200`, `Массив JSON объектов, описывающих файлы`
```JSON
[
  {
    "name": "first_file",
    "extension": ".txt",
    "size": 8,
    "path": "/",
    "created_at": "2023-07-05 12:49:45.330076",
    "updated_at": null,
    "comment": null
  },
  {
    "name": "another_file",
    "extension": ".txt",
    "size": 12,
    "path": "/",
    "created_at": "2023-07-05 12:53:15.813008",
    "updated_at": null,
    "comment": "another file"
  }
]
```

## get_files_info_by_path/
- Краткое описание: `получение информации о файлах в указанной и вложенных директориях`
- Метод: `GET`
- Формат запроса: `путь к директории в строке запроса`

    `get_files_info_by_path/subfolder/`
- Формат ответа: `200`, `Массив JSON объектов, описывающих файлы, хранящиеся по укзанному пути`
```JSON
[
  {
    "name": "still_file",
    "extension": ".txt",
    "size": 17,
    "path": "/subfolder/",
    "created_at": "2023-07-05 12:54:50.349056",
    "updated_at": null,
    "comment": null
  },
  {
    "name": "suddenly_not_file",
    "extension": ".txt",
    "size": 24,
    "path": "/subfolder/",
    "created_at": "2023-07-05 12:55:31.792707",
    "updated_at": null,
    "comment": "mysterious file"
  }
]
```

## get_file_info_by_id/
- Краткое описание: `получение информации о файле с указанным ID`
- Метод: `GET`
- Формат запроса: `ID строке запроса`

    `get_file_info_by_id/1`
- Формат ответа: 
    + `404`, `not found` - файл с указанным ID не найден
    + `200`, `JSON с информацией файла`
```JSON
{
  "name": "first_file",
  "extension": ".txt",
  "size": 8,
  "path": "/",
  "created_at": "2023-07-05 12:49:45.330076",
  "updated_at": null,
  "comment": null
}
```

## get_file_info_by_name/
- Краткое описание: `получение информации о файле, который хранится по указанному пути`
- Метод: `GET`
- Формат запроса: `путь к файлу в строке запроса`

    `get_file_info_by_name/subfolder/still_file.txt`
- Формат ответа: 
    + `404`, `not found` - файл по указанному пути не найден
    + `200`, `JSON с информацией файла`
```JSON
{
  "name": "still_file",
  "extension": ".txt",
  "size": 17,
  "path": "/subfolder/",
  "created_at": "2023-07-05 12:54:50.349056",
  "updated_at": null,
  "comment": null
}
```

## upload_file/
- Краткое описание: `загрузка файла на сервер`
- Метод: `POST`
- Формат запроса:
    + Загружаемый файл в поле формы `file`
    + *Опционально*: комментарий в поле формы `comment`
    + *Опционально*: директория в поле формы `extra_path`
- Формат ответа: 
    + `200`, `file has been uploaded` - файл был успешно загружен
    + `400`, `no file to load` - в поле формы `file` не указан загружаемый файл
    + `400`, `file already exists` - в указанной директории уже существует файл с таким же именем

## download_file/
- Краткое описание: `скачивание указанного файла с сервера`
- Метод: `GET`
- Формат запроса: `путь к файлу в строке запроса`

    `download_file/subfolder/still_file.txt`
- Формат ответа: 
    + `404`, `not found` - файл по указанному пути не найден
    + `200`, `указанный файл`

## delete_file_by_id/
- Краткое описание: `удаление файла с указанным ID`
- Метод: `DELETE`
- Формат запроса:
```JSON
{
    "id": 1
}
```
- Формат ответа: 
    + `404`, `no file to delete` - не указан ID файла
    + `404`, `not found` - файл с указанным ID не найден
    + `200`, `file has been deleted` - файл успешно удален

## delete_file_by_name/
- Краткое описание: `удаление файла, который хранится по указанному пути`
- Метод: `DELETE`
- Формат запроса:
```JSON
{
    "path": "subfolder/still_file.txt"
}
```
- Формат ответа: 
    + `404`, `no file to delete` - не указан путь файла
    + `404`, `not found` - файл по указанному пути не найден
    + `200`, `file has been deleted` - файл успешно удален

## edit_file/
- Краткое описание: `переименование, перемещение или изменение комментраия файла`
- Метод: `PUT`
- Формат запроса: поля `name`, `folder` и `comment` опциональны
```JSON
{
  "path": "subfolder/still_file.txt",
  "name": "s_file",
  "folder": "/user_folder/",
  "comment": "changed file"
}
```
- Формат ответа: 
    + `404`, `not found` - файл по указанному пути не найден
    + `200`, `no fields to edit were specified` - файл не был изменен, так как не было указано ни одного опционального поля
    + `200`, `file has been updated` - файл был успешно изменен