import json
import requests
from flask_babel import _
from app import app


def translate(text, source_language, dest_language):
    print("KEY: {}".format(app.config['MS_TRANSLATOR_KEY']))
    if 'MS_TRANSLATOR_KEY' not in app.config or not app.config['MS_TRANSLATOR_KEY']:
        print("\n\n###TRANSLATE###\n{}\n{}\n{}".format(text, source_language, dest_language))
        return _('Error: the translation service is not configured')
    auth = {'Ocp-Apim-Subscription-Key': app.config['MS_TRANSLATOR_KEY']}
    r = requests.get(
        'https://api.microsofttranslator.com/v2/Ajax.svc/Translate?text={}&from={}&to={}'.format(
            text, source_language, dest_language), headers=auth)
    print(r)
    print(r.content)
    print(type(r.content.decode('utf-8-sig')))
    if r.content.decode('utf-8-sig').find("ArgumentOutOfRangeException") >= 0:
        return _("Language not identifiable")
    if r.status_code != 200:
        return _("Error: translation failed")
    return json.loads(r.content.decode('utf-8-sig'))
