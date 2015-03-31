import os
import re
import json
import io # we might not need this as much now, that PIL as .tobytes()
import math
import hashlib
from collections import defaultdict
import grayscale
import codecs
from util import get_pref_folders
import lxml.etree as ET
try:
    from PIL import Image
except ImportError:
    pass

from ext_button import Button

class RestartlessButton(Button):
    
    def jsm_keyboard_shortcuts(self, file_name):
        keys = self.get_keyboard_shortcuts(file_name)
        if keys:
            statements, count, _ = self._create_dom(ET.fromstring(re.sub(r'&([^;]+);', r'\1', keys)), doc="document")
            statements.pop(-1)
            statements.insert(0, "var keyset_0 = document.getElementById('%s');\n\tif(!keyset_0) {" % self._settings.get("file_to_keyset").get(file_name))
            statements.insert(3, 'document.documentElement.appendChild(keyset_0);\n\t}')
            return "\n\t".join(statements)
        return ''
    
    def _jsm_create_menu(self, file_name, buttons):
        if not self._settings.get('menuitems'):
            return ''
        menu_id, menu_label, location = self._settings.get("menu_meta")
        statements = []
        data = self.create_menu_dom(file_name, buttons)
        in_submenu = {button: menuitem for button, menuitem in data.items() if menuitem.parent_id is None}
        in_menu = {button: menuitem for button, menuitem in data.items() if menuitem.parent_id is not None}
        num = 0
        meta = self._settings.get("file_to_menu").get(location, {}).get(file_name)
        if in_submenu and meta:
            with codecs.open(os.path.join(self._settings.get('button_sdk_root'),
                                          'templates', 'menu.js'), encoding='utf-8') as template_file:
                template = template_file.read()
            menu_name, insert_after = meta
            statements.append(template % {
                "menu_name": menu_name,
                "menu_id": menu_id,
                "label": menu_label,
                "menu_label": menu_label,
                "insert_after": insert_after
            })
            num += 3
            for item, _, _ in in_submenu.values():
                item_statements, count, _ = self._create_dom(item, top="menupopup_2", count=num, doc="document")
                num += count
                statements.extend(item_statements)
        for item, menu_name, insert_after in in_menu.values():
            statements.append("var menupopup_%s = document.getElementById('%s');" % (num, menu_name))
            var_name = "menupopup_%s" % num
            num += 1
            item.attrib["insertafter"] = insert_after
            item_statements, count, _ = self._create_dom(item, top=var_name, count=num, doc="document")
            num += count
            statements.extend(item_statements)
        return "\n\t".join(statements)
    
    def _dom_string_lookup(self, value):
        value = re.sub(r'&([^;]+);', r'\1', value)
        if " " in value:
            name, sep, other = value.partition(' ')
            other = " + '%s%s'" % (sep, other) if sep else ""
            return "buttonStrings.get('%s')%s" % (name, other)
        elif "&brandShortName;" in value:
            return "buttonStrings.get('%s'.replace('&brandShortName;', Cc['@mozilla.org/xre/app-info;1'].createInstance(Ci.nsIXULAppInfo).name))" % value
        else:
            return "buttonStrings.get('%s')" % value

    def _create_dom(self, root, top=None, count=0, doc='doc', child_parent=None, rename=None, append_children=True):
        num = count
        if rename == None:
            rename = {}
        children = []
        statements = [
            "var %s_%s = %s.createElement('%s');" % (root.tag, num, doc, rename.get(root.tag, root.tag)),
        ]
        for key, value in sorted(root.attrib.items(), key=self._attr_key):
            if key == 'id':
                if not self._settings.get("custom_button_mode"):
                    statements.append("%s_%s.id = '%s';" % (root.tag, num, value))
            elif key in ('label', 'tooltiptext') or (root.tag == 'key' and key in ('key', 'keycode', 'modifiers')):
                statements.append("%s_%s.setAttribute('%s', %s);" % ((root.tag, num, key, self._dom_string_lookup(value))))
            elif key == "class":
                for val in value.split():
                    statements.append('%s_%s.classList.add("%s");' % (root.tag, num, val))
            elif key[0:2] == 'on':
                if key == 'oncommand' and root.tag == 'key':
                    # we do this because key elements without a oncommand are optimized away
                    # but we can't call our function, because that might not exist 
                    # in the window scope, so the event listener has to be used
                    statements.append("%s_%s.setAttribute('oncommand', 'void(0);');" % (root.tag, num))
                if key == 'oncommand' and self._settings.get("custom_button_mode") and top == None:
                    self._command = value
                else:
                    this = 'var aThis = event.target;\n\t\t\t\t' if 'this' in value else ''
                    statements.append("%s_%s.addEventListener('%s', function(event) {\n\t\t\t\t%s%s\n\t\t\t}, false);" % (root.tag, num, key[2:], this, value.replace('this', 'aThis')))
            elif key == "insertafter":
                pass
            elif key == "showamenu":
                statements.append("%s_%s.addEventListener('DOMMenuItemActive', toolbar_buttons.menuLoaderEvent, false);"  % (root.tag, num))
                statements.append("%s_%s._handelMenuLoaders = true;"  % (root.tag, num))
                statements.append("%s_%s.setAttribute('%s', '%s');" % ((root.tag, num, key, value)))
            elif key == "toolbarname":
                # this is just for our custom toolbars which are named "Toolbar Buttons 1" and the like
                name, sep, other = value.partition(' ')
                other = " + '%s%s'" % (sep, other) if sep else ""
                value = "buttonStrings.get('%s')%s" % (name, other)
                statements.append("%s_%s.setAttribute('%s', %s);" % ((root.tag, num, key, value)))
            else:
                statements.append('%s_%s.setAttribute("%s", "%s");' % ((root.tag, num, key, value)))
        for node in root:
            sub_nodes, count, _ = self._create_dom(node, '%s_%s' % (root.tag, num), count+1, doc=doc, rename=rename, child_parent=(child_parent if top == None else None))
            if append_children:
                statements.extend(sub_nodes)
            else:
                children = sub_nodes
        if not top:
            statements.append('return %s_%s;' % (root.tag, num))
        else:
            if "insertafter" in root.attrib:
                statements.append("%s.insertBefore(%s_%s, %s.getElementById('%s').nextSibling);" % (top, root.tag, num, doc, root.attrib.get("insertafter")))
            else:
                statements.append('%s.appendChild(%s_%s);' % (top if not child_parent else child_parent, root.tag, num))
        return statements, count, children
    
    def _attr_key(self, attr):
        order = ('id', 'defaultarea', 'type', 'label', 'tooltiptext', 'command', 'onclick', 'oncommand')
        if attr[0].lower() in order:
            return order.index(attr[0].lower())
        return 100
        
    def _create_dom_button(self, button_id, xul, file_name, count, toolbar_ids):
        add_to_main_toolbar = self._settings.get("add_to_main_toolbar")
        root = ET.fromstring(xul)
        if 'viewid' in root.attrib:
            statements, _, children = self._create_dom(root, child_parent="popupset", rename={"menupopup": "panelview"}, append_children=False)
            children.insert(0, "var popupset = doc.getElementById('PanelUI-multiView');")
            data = {
                "type": "'view'",
                "onBeforeCreated": 'function (doc) {\n\t\t\t%s\n\t\t}' % "\n\t\t\t".join(children),
            }
        else:
            children = ''
            statements, _, _ = self._create_dom(root)
            data = {
                "type": "'custom'",
                "onBuild": 'function (doc) {\n\t\t\t%s\n\t\t}' % "\n\t\t\t".join(statements)
            }
        toolbar_max_count = self._settings.get("buttons_per_toolbar")
        if add_to_main_toolbar and button_id in add_to_main_toolbar:
            data['defaultArea'] = "'%s'" % self._settings.get('file_to_main_toolbar').get(file_name)
        elif self._settings.get("put_button_on_toolbar"):
            toolbar_index = count / toolbar_max_count
            if len(toolbar_ids) > toolbar_index:
                data['defaultArea'] = "'%s'" % toolbar_ids[toolbar_index]
        for key, value in root.attrib.items():
            if key in ('label', 'tooltiptext'):
                data[key] = self._dom_string_lookup(value)
            elif key == "id":
                data[key] = "'%s'" % value
            elif key == 'oncommand':
                self._button_commands[file_name][button_id] = value
            elif key == 'viewid':
                data["viewId"] = "'%s'" % value
            elif key == 'onviewshowing':
                data["onViewShowing"] = "function(event){\n\t\t\t%s\n\t\t}" % value
            elif key == 'onviewhideing':
                data["onViewHiding"] = "function(event){\n\t\t\t%s\n\t\t}" % value
        for js_file in self._get_js_file_list(file_name):
            if self._button_js_setup.get(js_file, {}).get(button_id):
                data["onCreated"] = "function(aNode){\n\t\t\t%s\n\t\t}" % self._button_js_setup[js_file][button_id]
        items = sorted(data.items(), key=self._attr_key)
        return "\tCustomizableUI.createWidget({\n\t\t%s\n\t});" % ",\n\t\t".join("%s: %s" % (key, value) for key, value in items)


    def _create_jsm_button(self, file_name, toolbar_ids, count, button_id, attr):
        toolbar_max_count = self._settings.get("buttons_per_toolbar")
        add_to_main_toolbar = self._settings.get("add_to_main_toolbar")
        data = {}
        if add_to_main_toolbar and button_id in add_to_main_toolbar:
            data['defaultArea'] = "'%s'" % self._settings.get('file_to_main_toolbar').get(file_name)
        elif self._settings.get("put_button_on_toolbar"):
            toolbar_index = count / toolbar_max_count
            if len(toolbar_ids) > toolbar_index:
                data['defaultArea'] = "'%s'" % toolbar_ids[toolbar_index]
        for key, value in attr.items():
            if key in ('label', 'tooltiptext'):
                data[key] = self._dom_string_lookup(value)
            elif key == "id":
                data[key] = "'%s'" % value
            elif key in ('onclick', 'oncommand'):
                if key == 'oncommand':
                    self._button_commands[file_name][button_id] = value
                key = 'onCommand' if key == 'oncommand' else 'onClick'
                this = 'var aThis = event.target;\n\t\t\t' if 'this' in value else ''
                data[key] = "function(event) {\n\t\t\t%s%s\n\t\t}" % (this, value.replace('this', 'aThis'))
        for js_file in self._get_js_file_list(file_name):
            if self._button_js_setup.get(js_file, {}).get(button_id):
                data["onCreated"] = "function(aNode) {\n\t\t\t%s\n\t\t}" % self._button_js_setup[js_file][button_id]
        items = sorted(data.items(), key=self._attr_key)
        result = "\tCustomizableUI.createWidget({\n\t\t%s\n\t});" % ",\n\t\t".join("%s: %s" % (key, value) for (key, value) in items)
        return result

    def get_jsm_files(self):
        with codecs.open(os.path.join(self._settings.get('button_sdk_root'), 'templates', 'button.jsm'), encoding='utf-8') as template_file:
            template = template_file.read()
        result = {}
        simple_button_re = re.compile(r"^<toolbarbutton(.*)/>$", re.DOTALL)
        attr_match = re.compile(r'''\b([\w\-]+)="([^"]*)"''', re.DOTALL)
        simple_attrs = {'label', 'tooltiptext', 'id', 'oncommand', 'onclick', 'key', 'class'}
        button_hash, toolbar_template = self._get_toolbar_info()
        
        for file_name, values in self._button_xul.iteritems():
            jsm_file = []
            js_includes = []
            for js_file in self._get_js_file_list(file_name):
                if js_file != "loader":
                    js_includes.append("""loader.loadSubScript("chrome://%s/content/%s.js", scope);""" % (self._settings.get("chrome_name"), js_file))
            toolbars, toolbar_ids = self._create_jsm_toolbar(button_hash, toolbar_template, file_name, values)
            count = 0
            modules = set()
            for button_id, xul in values.items():
                modules.update(self._modules[button_id])
                attr_data_match = simple_button_re.findall(xul)
                if attr_data_match:
                    attr_data = attr_data_match[0]
                else:
                    attr_data = ''
                attr = dict(attr_match.findall(attr_data))
                if attr_data and not set(attr.keys()).difference(simple_attrs) and (not "class" in attr or attr["class"] == "toolbarbutton-1 chromeclass-toolbar-additional"):
                    jsm_file.append(self._create_jsm_button(file_name, toolbar_ids, count, button_id, attr))
                else:
                    jsm_file.append(self._create_dom_button(button_id, re.sub(r'&([^;]+);', r'\1', xul), file_name, count, toolbar_ids))
                count += 1
            modules_import = "\n" + "\n".join("try { Cu.import('%s'); } catch(e) {}" % mod for mod in modules if mod)
            if self._settings.get("menu_meta"):
                menu_id, menu_label, _ = self._settings.get("menu_meta")
            else:
                menu_id, menu_label = "", ""
            end = []
            menu = self._jsm_create_menu(file_name, values)
            for js_file in set(self._get_js_file_list(file_name) + [file_name]):
                if self._button_js_setup.get(js_file, {}).get(button_id):
                    end.append(self._button_js_setup[js_file][button_id])
            if self._settings.get("menuitems") and menu:
                end.append("toolbar_buttons.setUpMenuShower();")
            result[file_name] = (template.replace('{{locale-file-prefix}}', self._settings.get("locale_file_prefix"))
                        .replace('{{modules}}', modules_import)
                        .replace('{{scripts}}', "\n\t".join(js_includes))
                        .replace('{{button_ids}}', json.dumps(values.keys())) # we use this not self._buttons, because of the possible generated toolbar toggle buttons
                        .replace('{{toolbar_ids}}', json.dumps(toolbar_ids))
                        .replace('{{toolbars}}', toolbars)
                        .replace('{{menu_id}}', menu_id)
                        .replace('{{toolbox}}', self._settings.get("file_to_toolbar_box").get(file_name, ('', ''))[1])
                        .replace('{{menu}}', menu)
                        .replace('{{keys}}', self.jsm_keyboard_shortcuts(file_name))
                        .replace('{{end}}', "\n\t".join(end))
                        .replace('{{buttons}}', "\n\n".join(jsm_file))
                        .replace('{{pref_root}}', self._settings.get("pref_root"))
                        .replace('{{chrome-name}}', self._settings.get("chrome_name")))
        return result
    
    def _create_jsm_toolbar(self, button_hash, toolbar_template, file_name, values):
        tool_bars, bottom_box, toolbar_ids = self._create_toolbar(button_hash, toolbar_template, file_name, values)
        if not tool_bars and not bottom_box:
            return '', []
        result = []
        count = 0
        for toolbars, box_setting in ((tool_bars, "file_to_toolbar_box"), (bottom_box, "file_to_bottom_box")):
            num = count
            if not toolbars: 
                continue
            toolbar_node, toolbar_box = self._settings.get(box_setting).get(file_name, ('', ''))
            toolbox = '\n<%s id="%s">\n%s\n</%s>' % (toolbar_node, toolbar_box, '\n'.join(toolbars), toolbar_node)
            statements, count, _ = self._create_dom(ET.fromstring(re.sub(r'&([^;]+);', r'\1', toolbox)), count=num,
                                                    doc="document")
            count += 1
            statements.pop(-1)
            statements.pop(1)
            statements[0] = "var %s_%s = document.getElementById('%s');" % (toolbar_node, num, toolbar_box)
            result.extend(statements)
        return "\n\t".join(result), toolbar_ids