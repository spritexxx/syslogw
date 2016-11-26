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

app.controller('MessagesController', ['$scope', '$window', function ($scope, $window){
    $scope.socket = null;
    $scope.socketIsOpen = false;
    $scope.isPaused = false;

    $scope.messages = [];
    // this buffer will hold messages while the app is paused
    $scope.paused_messages = [];

    var init = function() {
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

	    $scope.handleMessage = function(string) {
			    message = JSON.parse(string);

			    if(isEmpty(message.msg)) {
			        console.log("not logging empty message");
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

	$scope.gotoEndTable = function () {
	    // scroll to bottom of table
		var objDiv = document.getElementById("viewer");
        objDiv.scrollTop = objDiv.scrollHeight;
	};

	init();
	}]
);


