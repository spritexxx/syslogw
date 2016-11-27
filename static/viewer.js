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

app.controller('MessagesController', ['$scope', '$window', function ($scope, $window){
    $scope.socket = null;
    $scope.socketIsOpen = false;
    $scope.isPaused = false;

    $scope.messages = [];
    // this buffer will hold messages while the app is paused
    $scope.paused_messages = [];

    $scope.filters = [];
    // put a placeholder filter
    var filter = new Filter("myapp", ">= warning", "hide", "disabled");
    $scope.filters.push(filter);

    /*
     * Function to evaluate all user-specified filters on a message.
     * These filters will modify the message and return it.
     */
    $scope.applyFilters = function (message) {
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

			    // first evaluate filters, if this becomes too intense for the browser, offload it to server
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
	}

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

	$scope.gotoEndTable = function () {
	    // scroll to bottom of table
		var objDiv = document.getElementById("viewer");
        objDiv.scrollTop = objDiv.scrollHeight;
	};

    /* init function which takes care of the websocket */
    var create_websocket = function() {
	    socket = new WebSocket("ws://"+ server_ip +":9494");

	    socket.onopen = function() {
		    $scope.socketIsOpen = true;
		    $scope.socket = socket

		    // example if the message were a string
		    $scope.messages.push({severity: "info", msg: "Connected to syslogc", status: 2});
		    $scope.$apply();
	    }

	    socket.onmessage = function(e) {
		    if (typeof e.data == "string") {
			    $scope.handleMessage(e.data)
		    } else {
			    var arr = new Uint8Array(e.data);
			    var hex = '';
			    for (var i = 0; i < arr.length; i++) {
				    hex += ('00' + arr[i].toString(16)).substr(-2);
			    }
			    console.log("Binary message received: " + hex);
		    }
	    }

	    socket.onclose = function(e) {
		    $scope.socket = null;
		    $scope.socketIsOpen = false;

		    $scope.messages.push({severity: "err", msg: "Disconnected from syslogc"});
		    $scope.$apply();
	    }

	    $scope.socket = socket
	};

	create_websocket();
	}]
);


