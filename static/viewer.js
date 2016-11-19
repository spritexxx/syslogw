var app = angular.module('app', []);

// change delimiter so that we don't clash with Flask
app.config(['$interpolateProvider', function($interpolateProvider) {
  $interpolateProvider.startSymbol('{a');
  $interpolateProvider.endSymbol('a}');
}]);

function init() {
    window.init()
}

app.controller('MessagesController', ['$scope', '$window', function ($scope, $window){
    $scope.socket = null;
    $scope.socket_is_open = false;
    $scope.messages = [];
    $scope.messages.push("connecting to syslogc");

    var init = function() {
	    socket = new WebSocket("ws://127.0.0.1:9494");

	    socket.onopen = function() {
		    console.log("Connected!");
		    isopen = true;

		    // example if the message were a string
		    $scope.messages.push("connected to syslogc");
		    $scope.$apply();
	    }

	    socket.onmessage = function(e) {
		    if (typeof e.data == "string") {
			    console.log("Message received: " + e.data);
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
		    console.log("Connection closed.");
		    socket = null;
		    isopen = false;
	    }

	    $scope.socket = socket
	}

	init();
	}]
);


