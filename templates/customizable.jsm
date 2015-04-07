const Cc = Components.classes;
const Ci = Components.interfaces;
const Cu = Components.utils;

this.EXPORTED_SYMBOLS = ["CustomizableUI"];

var wm = Cc["@mozilla.org/appshell/window-mediator;1"].getService(Ci.nsIWindowMediator);
var gListeners = new Set();
var gWidgets = new Set();
var gAreas = new Set();

/*
 * This is a reimplementation of parts of resource:///modules/CustomizableUI.jsm
 * It is used for those applications that don't have it available.
 */

this.CustomizableUI = {

	shim: true, // so that this library can be detected if needed

	createWidget: function (aProperties) {
		gWidgets.add(aProperties);
		callWithEachWindow(function (win) {
			addWidgetToWindow(win, aProperties);
		});
		// return WidgetGroupWrapper
	},

	destroyWidget: function (aWidgetId) {
		callWithEachWindow(function (win) {
			let document = win.document;
			var button = document.getElementById(aWidgetId);
			if (button) {
				button.parentNode.removeChild(button);
			} else {
				var toolboxes = document.getElementsByTagName('toolbox');
				for(var t = 0; t < toolbars.length; t++) {
					var toolbox = toolboxes[i];
					var buttons = toolbox.palette.getElementsByAttribute('id', aWidgetId);
					for (var i = 0; i < buttons.length; i++) {
						toolbox.palette.removeChild(buttons[i]);
					}
				}
			}
		});
		for (let aProperties of gWidgets) {
			if(aProperties.id == aWidgetId) {
				gWidgets.delete(aProperties);
			}
		}
	},

	addWidgetToArea: function (aWidgetId, aArea, aPosition) {
		// we are not yet handeling aPosition
		callWithEachWindow(function (win) {
			let document = win.document;
			var toolbar = document.getElementById(aArea);
			if(!toolbar) {
				return;
			}
			try {
				toolbar.insertItem(aWidgetId, null, null, false);
				document.persist(aArea, 'currentset');
			} catch(e) {}
		});
	},

	registerArea: function (aName, aProperties) {
		// TODO: we need to do something about tracking the currentset for registered toolbars
		gAreas.add(aName);
		callWithEachWindow(function (win) {
			registerAreaForWindow(win, aName, aProperties);
		});
	},

	unregisterArea: function (aName, aDestroyPlacements) {
		gAreas.delete(aName);
	},

	addListener: function(aListener) {
		gListeners.add(aListener);
	},

	removeListener: function(aListener) {
		if (aListener == this) {
			return;
		}
		gListeners.delete(aListener);
	},

	beginBatchUpdate: function() {
		// Do we care?
	},

	endBatchUpdate: function(aForceDirty) {
		// do we care?
	},

	registerToolbarNode: function(aToolbar, aExistingChildren) {
		throw("registerToolbarNode Not Implimented.");
	},

	registerMenuPanel: function(aPanel) {
		throw("registerMenuPanel Should not be called.");
	},

	removeWidgetFromArea: function(aWidgetId) {
		throw("removeWidgetFromArea Not Implimented.");
	},

	moveWidgetWithinArea: function(aWidgetId, aPosition) {
		throw("moveWidgetWithinArea Not Implimented.");
	},

	ensureWidgetPlacedInWindow: function(aWidgetId, aWindow) {
		throw("ensureWidgetPlacedInWindow Not Implimented.");
	},

	getWidget: function(aWidgetId) {
		throw("getWidget Not Implimented.");
		// return WidgetGroupWrapper
	},

	getUnusedWidgets: function(aWindow) {
		throw("getUnusedWidgets Not Implimented.");
		// return Array
	},
	getWidgetIdsInArea: function(aAreaId) {
		throw("getWidgetIdsInArea Not Implimented.");
		// return Array
	},
	getWidgetsInArea: function(aAreaId) {
		throw("getWidgetsInArea Not Implimented.");
		// return Array
	},
	getAreaType: function(aAreaId) {
		throw("getAreaType Not Implimented.");
		// return String
	},
	getCustomizeTargetForArea: function(aAreaId, aWindow) {
		throw("getCustomizeTargetForArea Not Implimented.");
		// return DOMElement
	},
	reset: function() {
		throw("reset Not Implimented.");
	},
	undoReset: function() {
		throw("undoReset Not Implimented.");
	},
	removeExtraToolbar: function() {
		throw("removeExtraToolbar Not Implimented.");
	},
	getPlacementOfWidget: function(aWidgetId) {
		throw("getPlacementOfWidget Not Implimented.");
		// return Object
	},
	isWidgetRemovable: function(aWidgetNodeOrWidgetId) {
		throw("isWidgetRemovable Not Implimented.");
		// return bool
	},
	canWidgetMoveToArea: function(aWidgetId) {
		throw("canWidgetMoveToArea Not Implimented.");
		// return bool
	},
	getLocalizedProperty: function(aWidget, aProp, aFormatArgs, aDef) {
		throw("getLocalizedProperty Not Implimented.");
	},
	hidePanelForNode: function(aNode) {
		throw("hidePanelForNode Not Implimented.");
	},
	isSpecialWidget: function(aWidgetId) {
		throw("isSpecialWidget Not Implimented.");
		// return bool
	},
	addPanelCloseListeners: function(aPanel) {
		throw("addPanelCloseListeners Not Implimented.");
	},
	removePanelCloseListeners: function(aPanel) {
		throw("removePanelCloseListeners Not Implimented.");
	},
	onWidgetDrag: function(aWidgetId, aArea) {
		throw("onWidgetDrag Not Implimented.");
	},
	notifyStartCustomizing: function(aWindow) {
		throw("notifyStartCustomizing Not Implimented.");
	},
	notifyEndCustomizing: function(aWindow) {
		throw("notifyEndCustomizing Not Implimented.");
	},
	dispatchToolboxEvent: function(aEvent, aDetails, aWindow) {
		throw("dispatchToolboxEvent Not Implimented.");
	},
	isAreaOverflowable: function(aAreaId) {
		return false;
	},
	setToolbarVisibility: function(aToolbarId, aIsVisible) {
		throw("setToolbarVisibility Not Implimented.");
	},
	getPlaceForItem: function(aElement) {
		throw("getPlaceForItem Not Implimented.");
		// return String
	},
	isBuiltinToolbar: function(aToolbarId) {
		throw("isBuiltinToolbar Not Implimented.");
		// return bool
	}
}


function getButton(aButtonId, toolbar) {
	var node = toolbar.ownerDocument.getElementById(aButtonId);
	// most likely to happen in SeaMonkey, that keeps the toolbarpalette in the DOM
	if(node != null && node.parentNode != toolbar) {
		return null;
	}
	return node;
}

function restoreToToolbar(toolbox, aWidgetId) {
	let document = toolbox.ownerDocument;
	let potentialToolbars = Array.slice(toolbox.getElementsByTagName('toolbar'));
	for (let externalToolbar of toolbox.externalToolbars) {
		if (externalToolbar.getAttribute("prependmenuitem")) {
			potentialToolbars.unshift(externalToolbar);
		} else {
			potentialToolbars.push(externalToolbar);
		}
	}
	for(var i in potentialToolbars) {
		var toolbar = potentialToolbars[i];
		var buttonSet = toolbar.getAttribute('currentset');
		var buttons = buttonSet.split(",");
		var index = buttons.indexOf(aWidgetId);
		if(index != -1) {
			var spacers = 0;
			try {
				var beforeNode = getButton(buttons[index], toolbar);
				while(beforeNode == null && index < buttons.length) {
					var nodeId = buttons[index];
					if(nodeId == 'spacer' || nodeId == 'separator' || nodeId == 'spring') {
						// in the DOM these will have some random ID, and we will not be able to find them
						// so we keep looking for the next node, and then count back.
						spacers++;
					} else {
						beforeNode = getButton(nodeId, toolbar);
					}
					index++;
				}
				if(!beforeNode && spacers) {
					// we find so many spacers, but no node to insert before, so we go back as many nodes
					// as there are spacers
					beforeNode = toolbar.childNodes[toolbar.childNodes.length-spacers];
				} else {
					for(var j = 0; j < spacers; j++) {
						// counting back before the spacers
						beforeNode = beforeNode.previousSibling;
					}
				}
				toolbar.insertItem(aWidgetId, beforeNode, null, false);
				toolbar.setAttribute('currentset', buttonSet);
				document.persist(toolbar.id, 'currentset');
				return true;
			} catch(e) {
				document.defaultView.console.log(e);
			}
		}
	}
	return false;
}

function addWidgetToWindow(window, aProperties) {
	let document = window.document;
	if(aProperties.toolbox) {
		var toolboxId = aProperties.toolbox;
	} else {
		var toolboxId = 'navigator-toolbox';
	}
	var toolbox = document.getElementById(toolboxId);
	if(!toolbox) {
		return;
	}
	let uri = window.document.documentURI;
	if(aProperties.window && uri.indexOf(aProperties.window) == -1) {
		return;
	}
	try {
		if (aProperties.type == 'custom' && aProperties.onBuild) {
			var button = aProperties.onBuild(document);
			toolbox.palette.appendChild(button);
		} else {
			var button = document.createElement('toolbarbutton');
			button.id = aProperties.id;
			if (aProperties.label) {
				button.setAttribute('label', aProperties.label);
			}
			if (aProperties.tooltiptext) {
				button.setAttribute('tooltiptext', aProperties.tooltiptext);
			}
			if (aProperties.onBeforeCreated) {
				aProperties.onBeforeCreated(document);
			}
			if (aProperties.type == 'view') {
				button.setAttribute('type', 'panel');
				var view = document.getElementById(aProperties.viewId);
				if (aProperties.onViewShowing) {
					view.addEventListener('popupshowing', aProperties.onViewShowing, false);
				}
				if (aProperties.onViewHiding) {
					view.addEventListener('popuphiding', aProperties.onViewHiding, false);
				}
				button.appendChild(view);
			} else {
				if (aProperties.onCommand) {
					button.addEventListener('command', aProperties.onCommand, false);
				}
				if (aProperties.onClick) {
					button.addEventListener('click', aProperties.onClick, false);
				}
			}
			button.classList.add("toolbarbutton-1");
			button.classList.add("chromeclass-toolbar-additional");
			toolbox.palette.appendChild(button);
		}
		if (aProperties.onCreated) {
			aProperties.onCreated(button);
		}
		if (!restoreToToolbar(toolbox, aProperties.id)) {
			if (aProperties.defaultArea) {
				var buttonSet = toolbox.getAttribute('_addeddefaultset');
				var buttons = buttonSet.split(",");
				var index = buttons.indexOf(aProperties.id);
				if (index == -1) {
					addWidgetToArea(aProperties.id, aProperties.defaultArea, null);
					if (buttonSet) {
						buttonSet += ',' + aProperties.id;
					} else {
						buttonSet = aProperties.id;
					}
					toolbox.setAttribute('_addeddefaultset', buttonSet);
					document.persist(toolbox.id, '_addeddefaultset');
				}
			}
		}
	} catch (e) {
		document.defaultView.console.log(e);
	}
}

function addWidgetToArea(window, aWidgetId, aArea, aPosition) {
	// we are not yet handeling aPosition
	let document = window.document;
	var toolbar = document.getElementById(aArea);
	if(!toolbar) {
		return;
	}
	toolbar.insertItem(aWidgetId, null, null, false);
	document.persist(aArea, 'currentset');
}

function registerAreaForWindow(win, aName, aProperties) {
	let document = win.document;
	var toolbar = document.getElementById(aName);
	if(!toolbar) {
		return;
	}
	if (toolbar.hasAttribute('currentset')) {
		var buttonSet = toolbar.getAttribute('currentset');
	} else {
		var buttonSet = toolbar.getAttribute('defaultset');
	}
	var buttons = buttonSet.split(",");
	for (var i in buttons) {
		toolbar.insertItem(buttons[i], null, null, false);
	}
	// we do this to make sure we have not changed or messed up anything by calling insertItem
	toolbar.setAttribute('currentset', buttonSet);
	document.persist(aName, 'currentset');
}

function handelWindowLoad(window) {
	for (let aProperties of gWidgets) {
		addWidgetToWindow(window, aProperties);
	}
	for (let aName of gAreas) {
		registerAreaForWindow(window, aName, null);
	}
}

function callWithEachWindow(func) {
	let windows = wm.getEnumerator(null);
	while (windows.hasMoreElements()) {
		let domWindow = windows.getNext().QueryInterface(Ci.nsIDOMWindow);
		func(domWindow);
	}
}

var windowListener = {
	onOpenWindow: function(aWindow) {
		// Wait for the window to finish loading
		let domWindow = aWindow.QueryInterface(Components.interfaces.nsIInterfaceRequestor).getInterface(Components.interfaces.nsIDOMWindowInternal || Components.interfaces.nsIDOMWindow);
		domWindow.addEventListener("load", function onLoad() {
			domWindow.removeEventListener("load", onLoad, false);
			handelWindowLoad(domWindow);
		}, false);
	},
	onCloseWindow: function(aWindow) {},
	onWindowTitleChange: function(aWindow, aTitle) {}
};
wm.addListener(windowListener);