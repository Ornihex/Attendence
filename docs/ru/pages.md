# Деплой документации на GitHub Pages

## Что используется
- `MkDocs`
- `Material for MkDocs`
- GitHub Actions (`.github/workflows/docs-pages.yml`)

## Локальный просмотр документации
Установите зависимости:
```bash
pip install mkdocs mkdocs-material
```

Запустите локальный сервер документации:
```bash
mkdocs serve
```

Откройте: `http://127.0.0.1:8000`

## Сборка статического сайта
```bash
mkdocs build
```
Результат: директория `site/`.

## Публикация через GitHub Actions
1. В репозитории откройте `Settings -> Pages`.
2. Для `Build and deployment` выберите `Source: GitHub Actions`.
3. Запушьте изменения в `main` (или в ветку по умолчанию).
4. Workflow соберет docs и опубликует их в GitHub Pages.

## Важно настроить
Перед первым деплоем замените в `mkdocs.yml`:
- `site_url`
- `repo_url`
- `repo_name`
