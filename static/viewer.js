var app = angular.module('app', []);

// change delimiter so that we don't clash with Flask
app.config(['$interpolateProvider', function($interpolateProvider) {
  $interpolateProvider.startSymbol('{a');
  $interpolateProvider.endSymbol('a}');
}]);

function init() {
    window.init()
}

function isEmpty(str) {
    return (!str || 0 === str.length);
}

// Returns true if str matches the rule (which can contain * wildcards)
function matchRuleShort(str, rule) {
    return new RegExp("^" + rule.split("*").join(".*") + "$").test(str);
}

/* Filter class
 * Implements functions to evaluate whether a filter applies to a given message.
 * A filter consist of:
 *      - app: specify an app expression to match.
 *      - severity: specify on which severity this should act.
 *      - action: specify which action to take.
 */
function Filter(app_expr, severity_expr, action, state) {
    this.app_expr = app_expr;
    this.sev_expr = severity_expr;
    // action = highlight | hide
    this.action = action;
    // state = enabled | disabled
    this.state = state;

    this.severities = {
        "emerg" : 0,
        "alert" : 1,
        "crit" : 2,
        "err" : 3,
        "warning" : 4,
        "notice" : 5,
        "info" : 6,
        "debug" : 7,
    };

    this.operators = {
        "==" : 0,
        "!=" : 1,
        "<" : 2,
        "<=" : 3,
        ">" : 4,
        ">=" : 5,
        "*" : 6,
    };

    // TODO make it so that rules cannot simply be modified so that we can cache the expression!
    this.getOperator = function (severity_expr) {
        // first remove all whitespaces from severity expression
        severity_expr = severity_expr.replace(/\s/g,'');
        // get all non-alphabetical characters from expression
        operator = severity_expr.replace(/\w/g, '');
        if (!isEmpty(operator)) {
            return this.operators[operator];
        }
    }

    this.severityToInt = function (severity) {
        return this.severities[severity];
    };

    this.evaluateApp = function (appname) {
        return matchRuleShort(appname, this.app_expr);
    };

    // TODO refactor this so that apps can reuse this logic!
    this.evaluateSeverity = function (severity) {
        rule_int = this.severityToInt(this.sev_expr.replace(/\W/g, ''));
        sev_int = this.severityToInt(severity);
        operator = this.getOperator(this.sev_expr);
        if (operator == this.operators["*"])
            // so that if underneath does not fail...
            rule_int = 0;

        if (rule_int == null || sev_int == null || operator == null)
            return false;

        /* based on oparator */
        switch (operator) {
            case this.operators["=="]:
                if (rule_int == sev_int)
                    return true;
                else
                    return false;

            case this.operators["!="]:
                if (rule_int != sev_int)
                    return true;
                else
                    return false;

            case this.operators["<"]:
                if (rule_int < sev_int)
                    return true;
                else
                    return false;
                break;

            case this.operators["<="]:
                if (rule_int <= sev_int)
                    return true;
                else
                    return false;
                break;

            case this.operators[">"]:
                if (rule_int > sev_int)
                    return true;
                else
                    return false;
                break;

            case this.operators[">="]:
                if (rule_int >= sev_int)
                    return true;
                else
                    return false;
                break;

            case this.operators["*"]:
                return true;

            default:
                console.log("unmatched operator");
                break;
        }

        return false;
    };

    this.handleMessage = function (message) {
        if (this.state != "enabled")
            return message;

        if (!this.evaluateApp(message.appname)) {
            return message;
        }

        if (!this.evaluateSeverity(message.severity))
            return message;

        if (this.action == "hide")
            return null;
        else if (this.action == "highlight")
            message.status = 3;

        return message;
    };
}

function App(app_expr, state) {
    this.app_expr = app_expr;
    // state = enabled | disabled
    this.state = state;

    // TODO at some point refactor this as this is the same for the filter!
    this.evaluateApp = function (appname) {
        return matchRuleShort(appname, this.app_expr);
    };
}

/* Class that acts as a wrapper around the WebSocket class.
   It's goal is to create a robust connection with the server.
   This means that it will test the connection & reconnect if needed.
 */
function ViewerWebSocket(onReceiveHandler) {
    /* Configuration values */
    this.CHECK_MS = 5000;      // check connection every 5000 ms
    this.IDLE_S = 5;           // test connection every 5s when idle

    // refresh count is a temp. fix for the issue where no new logs can be sent from the server
    // although the connection is still valid. TODO: does this fix work?
    this.REFRESH_COUNT = 10;

    /* Function */
    this.createWebSocket = function(messageHandler, quiet) {
        socket = new WebSocket("ws://"+ server_ip +":9494");
        socket.quiet = quiet;
        console.log("create quiet: " + quiet);
        socket.messageHandler = messageHandler;
        socket.isOpen = false;

        // last time (in seconds since epoch) since we received something from server
        socket.lastTx = 0;

        /* Implementation of WebSocket functions */
	    socket.onopen = function() {
		    this.isOpen = true;
		    this.lastTx = new Date().getTime() / 1000;
		    if (!this.quiet) {
                this.messageHandler(JSON.stringify({
                    severity: "notice",
                    appname: "viewer",
                    msg: "Connected to syslogc"
                }));
            }

		    console.log("websocket opened");
	    };

	    socket.onmessage = function(e) {
		    this.lastTx = new Date().getTime() / 1000;
		    if (typeof e.data == "string") {
			      this.messageHandler(e.data)
		    }
		    else {
			    var arr = new Uint8Array(e.data);
			    var hex = '';
			    for (var i = 0; i < arr.length; i++) {
				    hex += ('00' + arr[i].toString(16)).substr(-2);
			    }
			    console.log("Binary message received: " + hex);
		    }
	    };

	    socket.onclose = function(e) {
		    this.isOpen = false;
		    console.log(this.quiet)
		    if (!this.quiet) {
                this.messageHandler(JSON.stringify({
                    severity: "err",
                    appname: "viewer",
                    msg: "Disconnected from syslogc"
                }));
            }
		    console.log("websocket closed");
	    };

	    return socket;
    };

    /* Test server connection by trying to send some data to the server.
       The server is configured so that it will reply whatever it receives on the WS.
     */
	this.testConnection = function() {
	    console.log("checking server connection");
	    this.socket.send((new Date().getTime()/1000).toString())
	};

	this.checkConnection = function(_this) {
	    if (!_this.socket.isOpen) {
	        console.log("socket is not open, reopening");
	        // create new one
	        _this.onReceiveHandler(JSON.stringify({severity: "debug", appname: "viewer", msg: "Trying to (re)connect to syslogc"}));

            _this.socket.close();
            _this.init(_this, _this.onReceiveHandler, false);
            return;
	    }
	    else {
	        console.log("socket is still open");

	        // TODO this needs to be properly fixed on the server at some point!
	        if(_this.refreshes > _this.REFRESH_COUNT) {
	            console.log("refreshing socket because REFRESH_COUNT reached");

                _this.socket.quiet = true;
                _this.socket.close();
                _this.init(_this, _this.onReceiveHandler, true);
	            return;
            }

	        currentTime = new Date().getTime() / 1000;
	        delta = currentTime - _this.socket.lastTx;

            /* test connection in case we haven't heard from server in a while */
	        if (delta >= _this.IDLE_S) {
	            console.log("no message received from server in a while...");
	            _this.testConnection();
	            _this.refreshes++;
	        }
	    }

	    setTimeout(_this.checkConnection, _this.CHECK_MS, _this);
	};

    this.init = function(_this, onReceiveHandler, quiet) {
        // this function sets up the websocket
        _this.refreshes = 0;
        // TODO probably not needed
        _this.onReceiveHandler = onReceiveHandler;

	    _this.socket = _this.createWebSocket(onReceiveHandler, quiet);
	    // check socket in 1 second
	    setTimeout(_this.checkConnection, _this.CHECK_MS, _this);
    };

    this.init(this, onReceiveHandler, false);
}

app.controller('MessagesController', ['$scope', '$window', function ($scope, $window){
    $scope.isPaused = false;

    $scope.messages = [];
    // this buffer will hold messages while the app is paused
    $scope.paused_messages = [];

    $scope.apps = [];
    // put a placeholder app
    $scope.apps.push(new App("my_app", "disabled"));

    $scope.filters = [];
    // put a placeholder filter
    var filter = new Filter("myapp", ">= warning", "hide", "disabled");
    $scope.filters.push(filter);

    $scope.applyApps = function (message) {
        if (!message)
            return null;

        var hasAppEnabled = false;

        for (var index = 0; index < $scope.apps.length; index++) {
            var app = $scope.apps[index];
            if (app.state == "enabled") {
                hasAppEnabled = true;
                if (app.evaluateApp(message.appname)) {
                    return message;
                }
            }
            else
                continue;
        }

        // if we got here and an enabled app was found, it means none of them match the message so we discard it
        if(hasAppEnabled) {
            console.log("discarded message with non-matching app");
            return null;
        }
        else {
            return message;
        }
    };

    /*
     * Function to evaluate all user-specified filters on a message.
     * These filters will modify the message and return it.
     */
    $scope.applyFilters = function (message) {
        if (!message)
            return null;

        for (var index = 0; index < $scope.filters.length; index++) {
            message = $scope.filters[index].handleMessage(message);
            // if filter removed the message, stop immediately
            if (!message)
                return message;
        }

        return message;
    };

    $scope.handleMessage = function (string) {
			    message = JSON.parse(string);

			    if(isEmpty(message.msg)) {
			        console.log("not logging empty message");
			        return;
			    }

			    // reset socket refresh counter
                $scope.viewer_ws.refreshes = 0;

			    // first check if only specific apps should be shown
			    message = $scope.applyApps(message);

			    // evaluate filters, if this becomes too intense for the browser, offload it to server
			    message = $scope.applyFilters(message);
			    if (!message) {
			        console.log("filtered out message");
			        return;
			    }

			    /* color time */
			    if (message.severity == "err" ||
			            message.severity == "emerg" ||
			            message.severity == "alert" ||
			            message.severity == "crit")
			        message.status = 0;
			    else if (message.severity == "warning")
			        message.status = 1;
			    else if (message.severity == "notice")
			        message.status = 2;

                /* if we are paused we simply keep messages in a separate buffer */
                if ($scope.isPaused) {
                    $scope.paused_messages.push(message);
                }
                else {
                    $scope.messages.push(message);
			        $scope.$apply();

	                $scope.gotoEndTable();
                }
	};

	$scope.onPause = function () {
	    $scope.isPaused = true;
	};

	$scope.onResume = function () {
	    $scope.isPaused = false;
	    $scope.messages = $scope.messages.concat($scope.paused_messages);
	    $scope.paused_messages.length = 0;

	    $scope.gotoEndTable();
	};

	$scope.onClear = function () {
	    $scope.messages.length = 0;
	    $scope.paused_messages.length = 0;

	    $scope.gotoEndTable();
	};

	$scope.addFilter = function () {
	    // the last filter of the list is simply a disabled example filter
	    $scope.filters.push(new Filter("appname", ">= warning", "hide", "disabled"));
	};

	$scope.removeFilter = function (index) {
	    $scope.filters.splice(index, 1);
	};

	$scope.addApp = function () {
	    $scope.apps.push(new App("my_app", "disabled"));
	};

	$scope.removeApp = function (index) {
	    $scope.apps.splice(index, 1);
	};

	$scope.gotoEndTable = function () {
	    // scroll to bottom of table
		var objDiv = document.getElementById("viewer");
        objDiv.scrollTop = objDiv.scrollHeight;
	};

    $scope.viewer_ws = new ViewerWebSocket($scope.handleMessage);

	}]
);
