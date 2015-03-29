import os
import re
from collections import defaultdict

try:
    from PIL import Image
except ImportError:
    pass

def get_image(settings, size, name):
    if isinstance(settings.get("image_path"), str):
        return os.path.join(settings.get("image_path"), size, name)
    else:
        for folder in settings.get("image_path"):
            file_name = os.path.join(folder, size, name)
            if os.path.exists(file_name):
                return file_name
    return os.path.join(settings.get("image_path")[0], size, name)

class SimpleButton(object):

    def __init__(self, folders, buttons, settings, applications):
        self._folders = folders
        self._buttons = buttons
        self._button_names = set(buttons)
        self._settings = settings
        try:
            Image
        except NameError:
            self._settings["merge_images"] = False
        if applications and "all" not in applications:
            self._applications = applications
        else:
            self._applications = self._settings["applications_data"].keys()
        self._button_image = defaultdict(list)
        self._icons = {}
        self._button_keys = {}
        self._button_applications = defaultdict(set)

        button_files = self._settings.get("file_to_application").keys()
        button_files.sort()
        self._app_files = self._settings.get("file_map").keys()
        self._app_files.sort()
        self._window_files = list(set(button_files).difference(self._app_files))
        self._info = []
        self._strings = {}
        self._xul_files = {}
        self._button_folders = {}
        self._button_windows = defaultdict(list)
        large_icon_size = settings.get("icon_size")[1]
        skip_without_icons = settings.get("skip_buttons_without_icons")

        for folder, button in zip(self._folders, self._buttons):
            if self._settings.get("exclude_buttons") and button in self._settings.get("exclude_buttons"):
                continue
            files = os.listdir(folder)
            button_wanted = False
            xul_data = []
            xul_files = []
            #file that belong to more then one window
            for group_name in self._app_files:
                xul_file = group_name + ".xul"
                if xul_file in files:
                    for file_name in self._settings.get("file_map")[group_name]:
                        for exclude in self._settings.get("file_exclude").get(file_name, []):
                            if exclude + ".xul" in files:
                                break
                        else:
                            if set(self._settings.get("file_to_application")[file_name]
                                   ).intersection(self._applications):
                                if self._settings.get("extended_buttons") and ("extended_%s" % xul_file) in files:
                                    xul_file = "extended_%s" % xul_file
                                xul_data.append((folder, button,
                                                       xul_file, file_name))
                                xul_files.append(os.path.join(folder, xul_file))
                                button_wanted = True
            #single window files
            for file_name in self._window_files:
                xul_file = file_name + ".xul"
                if (xul_file in files
                        and set(self._settings.get("file_to_application")[file_name]
                                   ).intersection(self._applications)):
                    if self._settings.get("extended_buttons") and ("extended_%s" % xul_file) in files:
                        xul_file = "extended_%s" % xul_file
                    xul_data.append((folder, button, xul_file, file_name))
                    xul_files.append(os.path.join(folder, xul_file))
                    button_wanted = True

            if "image" in files and button_wanted:
                with open(os.path.join(folder, "image"), "r") as images:
                    for line in images:
                        name, _, modifier = line.partition(" ")
                        self._button_image[button].append((name.strip(),
                                                           modifier.rstrip()))
                        if skip_without_icons:
                            name = name.strip().lstrip("*").lstrip("-")
                            if not os.path.exists(get_image(settings, large_icon_size, name.strip())):
                                button_wanted = False
                                del self._button_image[button]
                        if name and not modifier:
                            self._icons[button] = name.strip()
                    if skip_without_icons and not len(self._button_image[button]):
                        button_wanted = False
                            
            elif button_wanted:
                raise ValueError("%s does not contain image listing." % folder)

            if not button_wanted:
                self._button_names.remove(button)
                continue
            else:
                for item in xul_data:
                    self._process_xul_file(*item)
                self._info.append((folder, button, files))
                self._button_folders[button] = folder
                self._xul_files[button] = xul_files

            if "key" in files and self._settings.get("use_keyboard_shortcuts"):
                with open(os.path.join(folder, "key"), "r") as keys:
                    key_shortcut = list(keys.read().strip().partition(":"))
                    key_shortcut.pop(1)
                    self._button_keys[button] = key_shortcut
                    
            if "strings" in files:
                with open(os.path.join(folder, "strings"), "r") as strings:
                    for line in strings:
                        name, _, value = line.strip().partition("=")
                        if name:
                            self._strings[name] = value
                            
    def __len__(self):
        return len(self._buttons)

    def _process_xul_file(self, folder, button, xul_file, file_name):
        application = self._settings.get("file_to_application")[file_name]
        self._button_windows[button].append(file_name)
        self._button_applications[button].update(set(application).intersection(self._applications))
        return application

    def button_applications(self):
        return self._button_applications

    def applications(self):
        return self._applications

    def buttons(self):
        return list(self._button_names)
        
    def get_key(self, name, locale=None):
        if name[-4:] == ".key":
            return self._button_keys.get(name[:-4])[0]
        elif name[-9:] == ".modifier":
            return self._button_keys.get(name[:-9])[1]
        return ""

    def get_string(self, name, locale=None):
        return self._strings.get(name) or self.get_key(name, locale)

    def get_icons(self, button):
        return self._icons.get(button)
    
    def locale_string(self, button_locale, locale_name):
        def locale_str(str_type, button_id):
            default_locale = self._settings.get('default_locale', 'en-US')
            value = button_locale.get_dtd_value(locale_name, "%s.%s" % (button_id, str_type), self)
            if value is None:
                if str_type == "tooltip":
                    regexp = r'tooltiptext="&(.*\.tooltip);"'
                else:
                    regexp = r'label="&(.*\.label);"'
                with open(self._xul_files[button_id][0]) as fp:
                    data = fp.read()
                    match = re.search(regexp, data)
                    if match:
                        string_name = match.group(1)
                    else:
                        string_name = "%s.%s" % (button_id, str_type)
                    value = button_locale.get_dtd_value(locale_name, string_name, self)
                if value is None:
                    value = button_locale.get_dtd_value(default_locale, string_name, self)
            if value is None:
                return u'' #print button_id
            return unicode(value.replace("&brandShortName;", "").replace("&apos;", "'"))
        return locale_str