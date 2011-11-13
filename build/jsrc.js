
var ws = new WebSocket("ws://localhost:9999/");

ws.onopen = function() {
  ws.send("Hello Mr. Server!");
};

ws.onmessage = function (e) { alert(e.data); };
ws.onclose = function() { };

