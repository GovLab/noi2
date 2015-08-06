'''
NoI __init__

Creates globals
'''

from flask_assets import Bundle, Environment
from flask_security import Security
from flask_cache import Cache
from flask_babel import Babel
from flask_bcrypt import Bcrypt
from flask.ext.uploads import UploadSet, IMAGES
from celery import Celery
from flask_mail import Mail
from flask_s3 import FlaskS3
from flask_wtf.csrf import CsrfProtect

import yaml

s3 = FlaskS3()
mail = Mail()
security = Security()
csrf = CsrfProtect()
babel = Babel()
bcrypt = Bcrypt()

celery = Celery(
    __name__,
    #broker=os.environ.get('REDISGREEN_URL', None),
    include=[]
)

assets = Environment()

main_css = Bundle('css/vendor/bootstrap.css',
                  output='gen/main_packed.%(version)s.css')
assets.register('main_css', main_css)

main_js = Bundle('js/plugins.js',
                 #filters='jsmin',
                 output='gen/main_packed.%(version)s.js')
assets.register('main_js', main_js)

photos = UploadSet('photos', IMAGES)

cache = Cache()

LEVELS = {'LEVEL_I_CAN_EXPLAIN': {'score': 2,
                                  'icon': '<i class="fa-fw fa fa-book"></i>',
                                  'label': 'I can explain'},
          'LEVEL_I_CAN_DO_IT': {'score': 5,
                                'icon': '<i class="fa-fw fa fa-cogs"></i>',
                                'label': 'I can do it'},
          'LEVEL_I_CAN_REFER': {'score': 1,
                                'icon': '<i class="fa-fw fa fa-mail-forward"></i>',
                                'label': 'I can refer you'},
          'LEVEL_I_WANT_TO_LEARN': {'score': -1,
                                    'icon': '<i class="fa-fw fa fa-question"></i>',
                                    'label': 'I want to learn'}}

VALID_SKILL_LEVELS = [v['score'] for k, v in LEVELS.iteritems()]

NOI_COLORS = '#D44330,#D6DB63,#BFD19F,#83C8E7,#634662,yellow,gray'.split(',')

DOMAINS = """Business Licensing and Regulation
Civil Society
Corporate Social Responsibility
Defense and Security
Economic Development
Education
Emergency Services
Environment
Extractives Industries
Governance
Health
Human Rights
Immigration and Citizenship Services
Judiciary
Labor
Legislature
Media and Telecommunications
Public Safety
Research
Sanitation
Social Care
Sub-National Governance
Talent Services
Transportation
Water and Electricity""".split('\n')

COUNTRIES = "Afghanistan,Algeria,Argentina,Australia,Austria,Bahamas,Bangladesh,Belgium,Belize,Benin,Bhutan,Brazil,Bulgaria,Burkina Faso,Burundi,Cambodia,Cameroon,Canada,Central African Rep,Chad,Chile,China,Colombia,Congo,Congo (The Democratic Rep),Costa Rica,Cuba,Czech Republic,Denmark,Djibouti,Dominican Republic,Ecuador,Egypt,El Salvador,Ethiopia,Fiji,Finland,France,Gambia,Georgia,Germany,Ghana,Guatemala,Guinea,Haiti,Hungary,India,Indonesia,Iran,Iraq,Ireland,Italy,Ivory Coast (Cote D'Ivoire),Jamaica,Japan,Jordan,Kenya,Korea (Republic Of),Kyrgyzstan,Lebanon,Liberia,Lithuania,Macedonia (Republic of),Madagascar,Malawi,Malaysia,Mali,Mauritania,Mexico,Moldova (Rep),Mongolia,Montenegro,Namibia,Nepal,Netherlands,New Zealand,Niger,Nigeria,Pakistan,Panama,Papua New Guinea,Paraguay,Peru,Philippines,Romania,Russian Federation,Rwanda,Samoa,Senegal,Serbia,Slovakia (Slovak Rep),Somalia,South Africa,Spain,Sri Lanka,Sudan,Sweden,Switzerland,Taiwan,Tajikistan,Tanzania,Thailand,Togo,Tonga,Trinidad & Tobago,Tunisia,Turkey,Uganda,Ukraine,United Kingdom,United States,Uruguay,Viet Nam,Yemen,Zambia".split(',')
LANGS = 'Afrikaans|Albanian|Arabic|Armenian|Basque|Bengali|Bulgarian|Catalan|Cambodian|Chinese (Mandarin)|Croation|Czech|Danish|Dutch|English|Estonian|Fiji|Finnish|French|Georgian|German|Greek|Gujarati|Hebrew|Hindi|Hungarian|Icelandic|Indonesian|Irish|Italian|Japanese|Javanese|Korean|Latin|Latvian|Lithuanian|Macedonian|Malay|Malayalam|Maltese|Maori|Marathi|Mongolian|Nepali|Norwegian|Persian|Polish|Portuguese|Punjabi|Quechua|Romanian|Russian|Samoan|Serbian|Slovak|Slovenian|Spanish|Swahili|Swedish |Tamil|Tatar|Telugu|Thai|Tibetan|Tonga|Turkish|Ukranian|Urdu|Uzbek|Vietnamese|Welsh|Xhosa'.split('|')

ORG_TYPES = { 'edu': 'Academia', 'com': 'Private Sector', 'org': 'Non Profit', 'gov': 'Government', 'other': 'Other' }

CONTENT = yaml.load(open('/noi/app/content.yaml'))
VALID_SKILL_NAMES = set()
for area in CONTENT['areas']:
    for topic in area.get('topics', []):
        for question in topic['questions']:
            label = question['label']
            if label in VALID_SKILL_NAMES:
                raise Exception("Duplicate skill label {}".format(label))
            else:
                VALID_SKILL_NAMES.add(label)
