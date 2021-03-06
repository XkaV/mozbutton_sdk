// careful here, we only want to add if the are not defined
if (!this.Cc)
	this.Cc = Components.classes;
if (!this.Ci)
	this.Ci = Components.interfaces;
if (!this.Cu)
	this.Cu = Components.utils;

if(!this.toolbar_buttons) {
	this.toolbar_buttons = {
		interfaces: {},
		// the important global objects used by the extension
		toolbar_button_loader: function(parent, child) {
			var object_name;
			for(object_name in child){
				if(object_name == 'interfaces') {
					toolbar_buttons.toolbar_button_loader(parent.interfaces, child.interfaces);
				} else {
					parent[object_name] = child[object_name];
				}
			}
		}
	};
}