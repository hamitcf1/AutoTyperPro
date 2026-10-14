"""Public product ownership and deliberately limited support information."""
import platform
from urllib.parse import urlencode
from preferences import VERSION
CREATOR='Hamit Can Fındık'
ORGANIZATION='AetheriusCo'
REPOSITORY='https://github.com/AetheriusCo/AutoTyperPro'
CREATOR_URL='https://github.com/hamitcf1'
ORGANIZATION_URL='https://github.com/AetheriusCo'

def technical_summary():
    system=platform.system()
    release=platform.mac_ver()[0] if system=='Darwin' else platform.release()
    return f'AutoTyper Pro {VERSION}\nOS: {system} {release}\nArchitecture: {platform.machine()}'

def bug_report_url(summary):
    return REPOSITORY+'/issues/new?'+urlencode({'template':'bug_report.yml','version':VERSION,'platform':summary})
