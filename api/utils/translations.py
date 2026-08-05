PUSH_TRANSLATIONS = {
    "en": {
        "transfer_title": "Transfer received",
        "transfer_body": "{amount} OC from @{sender}"
    },
    "ru": {
        "transfer_title": "Перевод получен",
        "transfer_body": "{amount} OC от @{sender}"
    },
}


def t(locale: str, key: str, **kwargs) -> str:
    lang = locale if locale in PUSH_TRANSLATIONS else "en"
    text_template = PUSH_TRANSLATIONS[lang].get(key, key)

    try:
        return text_template.format(**kwargs)
    except KeyError:
        return text_template
