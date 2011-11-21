
function log(msg) { 
	postMessage({cmd:'log', data:msg});
};

function JSDBClient(name, href, config) {
	var JSDB_HOST = '127.0.0.1';
	var JSDB_PORT = 22222;
	
	if ( config ) {
		if ( config['host'] ) { JSDB_HOST = config['host']; }
		if ( config['port'] ) { JSDB_PORT = config['port']; }
	}
	
    var url = 'ws://' + JSDB_HOST + ':' + JSDB_PORT + '/test';
    
//@ifdef DEBUG
    log("connecting to " + url);
//@end
    this.name = name;
    this.url = url;
    
    var clientid = {
        client : {
            url         : href,
            platform    : navigator.platform,
            useragent   : navigator.userAgent,
            ctime       : new Date().getTime()
        }
    };

    this.clientid = clientid;
}

JSDBClient.prototype.start = function() { 
	var HEARTBEAT_INTERVAL=5000;
    this.ws = new WebSocket(this.url);
    ws = this.ws;

    this.ws.name = this.name;
    this.ws.clientid = this.clientid;
    this.ws.isclosed = false;
    
    this.ws.sendCmd = function(cmd) { 
        cmd.id = this.clientid;
        ws.send(JSON.stringify(cmd));
    };

    this.ws.onerror = function(reason) {
        log('unable to connect, ' + reason);
    };

    this.ws.onopen = function() {
        cmd = { cmd : "register", id : this.clientid };
        this.send(JSON.stringify(cmd));
    };
    
    this.ws.onmessage = function(e) {
        postMessage({cmd:'exec', data:e.data });
    };

    this.ws.heartbeat = function heartbeat(ws) { 
        if ( !ws.isclosed ) {
        	ws.sendCmd({cmd:"heartbeat","from": this.name});
        	setTimeout(function() { this.heartbeat(ws); },HEARTBEAT_INTERVAL);
        }
    };
    
    heartbeat = function() { ws.heartbeat(ws); };
    this.ws.onclose = function() {
        this.sendCmd({cmd:"unregister"});
    };
        
    setTimeout(function() { ws.heartbeat(ws); },HEARTBEAT_INTERVAL);
};

JSDBClient.prototype.stop = function() { 
	this.ws.close();
	this.ws.isclosed = true;
};

