# Help translate AutoTyper Pro

Translations are community contributions. Open a [translation request](https://github.com/AetheriusCo/AutoTyperPro/issues/new?template=translation.yml) to coordinate a language, or send a pull request with a catalog and registry entry. You can contribute a partial translation; missing messages use the default catalog.

1. Copy `locales/en.json` to `locales/<language-code>.json`, for example `es.json` or `pt-BR.json`. Translate values, keep message keys unchanged. Remove untranslated entries if contributing a partial catalog.
2. Add an entry in `locales/manifest.json` with `code`, `native_name` and a `contributors` list. Use the language's own name in the picker. Add only the public name you want credited.
3. Keep every formatting placeholder unchanged, including `{name}`, `{v0}` and `{key}`. Preserve intentional newlines. Do not change shortcuts, filenames or product names without context.
4. Run `python tools/check_translations.py`. Resolve validation errors; the report lists missing keys and completion counts. Run `python -m unittest discover -s tests` before submitting.
5. Check screens at the minimum window size and both appearances. Prefer short, natural labels. Include screenshots without private text when useful.

Catalogs contain JSON strings only. Duplicate keys, unsafe language codes, malformed metadata and incompatible placeholders are rejected. Invalid translations fall back rather than breaking the UI. Reviewed registry entries appear in the language picker; users do not need a separate account or translation service.

Contributor names from the registry appear in the application's About/translation credits. Do not add private contact details. Maintainers review the translations, resource packaging and screenshots before release.
