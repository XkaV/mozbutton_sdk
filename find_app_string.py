
import os
import sys
import re
from collections import defaultdict
from .config import settings
from .builder.util import get_locale_folders, apply_settings_files
from .builder.locales import Locale

entity_re = re.compile(r"<!ENTITY\s+([\w\-\.]+?)\s+[\"'](.*?)[\"']\s*>")

def find_val(value, strings):
    for val in strings:
        if val.lower() == value.lower():
            return True
    return False

def get_entities(strings, path):
    with open(path) as data:
        for line in data:
            match = entity_re.match(line.strip())
            if match:
                name, value = match.group(1), match.group(2)
                if value in strings: #find_val(value, strings):
                    key = ",".join(strings[value])
                    print "%s\t%s\t%s\t%s" % (value, name, path, key)
                    
def get_properties(strings, path):
    with open(path) as data:
        for line in data:
            if not line.strip() or not '=' in line:
                continue
            name, value = line.strip().split('=', 1)
            value = value.strip()
            name = name.strip()
            if name and value in strings: #find_val(value, strings):
                key = ",".join(strings[value])
                print "%s\t%s\t%s\t%s" % (value, name, path, key)                    

def find_string(strings, folder):
    files = os.listdir(folder)
    for file_name in files:
        path = os.path.join(folder, file_name)
        if os.path.isdir(path):
            find_string(strings, path)
        elif file_name.endswith(".dtd"):
            get_entities(strings, path)
        elif file_name.endswith(".properties"):
            get_properties(strings, path)
    
def main():
    args = sys.argv[1:]
    config = dict(settings.config)
    apply_settings_files(config, args)
    config["locale"] = "en-US"
    locale_folders, locales = get_locale_folders(config.get("locale"), config)
    button_locales = Locale(config, locale_folders, locales, all_files=True)
    items = button_locales._dtd['en-US']
    items.update(button_locales._properties['en-US'])
    strings = defaultdict(list)
    for key, value in items.items():
        if value:
            strings[value].append(key)    
    find_string(strings, os.path.join("app_locale", "en-US"))
    
if __name__ == "__main__":
    main()

# python find_app_string.py | sort > app_locale/data
