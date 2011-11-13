JSDB_HOST = '127.0.0.1';
JSDB_PORT = 22222;

HEARTBEAT_INTERVAL=5000;

function log(msg) { 
	postMessage({cmd:'log', data:msg});
};

function JSDBClient(name,href) {
    var url = 'ws://' + JSDB_HOST + ':' + JSDB_PORT + '/test';
//@ifdef DEBUG
    log("connecting to " + url);
//@end
    this.name = name;

    var jsdb = {
        client : {
            url         : href,
            platform    : navigator.platform,
            useragent   : navigator.userAgent,
            ctime       : new Date().getTime()
        }
    };

    this.jsdb = jsdb;
    this.ws = new WebSocket(url);
    ws = this.ws;

    this.ws.sendCmd = function(cmd) { 
        cmd.id = jsdb;
        ws.send(JSON.stringify(cmd));
    };

    this.ws.onerror = function(reason) {
        log('unable to connect, ' + reason);
    };

    this.ws.onopen = function() {
        cmd = { cmd : "register", id : jsdb };
        this.send(JSON.stringify(cmd));
    };
    
    this.ws.onmessage = function(e) {
        postMessage({cmd:'exec', data:e.data });
    };

    this.ws.heartbeat = function heartbeat(ws) { 
        ws.sendCmd({cmd:"heartbeat","from":name});
        setTimeout(function() { this.heartbeat(ws); },HEARTBEAT_INTERVAL);
    };
    
    heartbeat = function() { ws.heartbeat(ws); };
    this.ws.onclose = function() {
        this.sendCmd({cmd:"unregister"});
    };
        
    setTimeout(function() { ws.heartbeat(ws); },HEARTBEAT_INTERVAL);
}

JSDBClient.prototype.start = function() { 
    
};

JSDBClient.prototype.stop = function() { 
    
};

