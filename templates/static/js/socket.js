$(document).ready(
	function () {
		//connect to the socket server.
		var socket = io.connect();
		//receive details from server
		socket.on("loop", function (msg) {
			document.getElementById("ctime").innerHTML = msg.now;
			//document.getElementById("plotid").src = msg.plot;
		});
	}
);