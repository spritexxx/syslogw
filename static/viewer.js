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
    $scope.socket_is_open = false;
    $scope.messages = [];

    var init = function() {
	    socket = new WebSocket("ws://127.0.0.1:9494");

	    socket.onopen = function() {
		    $scope.socket_is_open = true;
		    $scope.socket = socket

		    // example if the message were a string
		    $scope.messages.push({severity: "notice", msg: "Connected to syslogc"});
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
		    $scope.socket_is_open = false;

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

			    $scope.messages.push(message);
			    $scope.$apply();

			    // scroll to bottom of table
			    var objDiv = document.getElementById("viewer");
                objDiv.scrollTop = objDiv.scrollHeight;
	    }
	}

	init();
	}]
);


