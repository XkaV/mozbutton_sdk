SendWithNoSave: function() {
	var prefs = toolbar_buttons.interfaces.PrefBranch;
	var prefstring = "mail.identity." + gCurrentIdentity.key + ".fcc";
	try {
		var send = prefs.getBoolPref(prefstring);
	} catch (e) {
		prefstring = "mail.identity.default.fcc";
		var send = prefs.getBoolPref(prefstring);
	}
	if (send == false) {
		goDoCommand("cmd_sendButton");
	} else {
		prefs.setBoolPref(prefstring, false);
		try {
			if (toolbar_buttons.interfaces.IOService.offline) {
				SendMessageLater();
			} else {
				SendMessage();
			}
		} catch (e) {}
		prefs.setBoolPref(prefstring, send);
	}
}
