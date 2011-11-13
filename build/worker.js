
importScripts('jsdbclient.js');

self.addEventListener('message', function(e) {
    var data = e.data;
    switch (data.cmd) {
        case 'jsresp':
            self.client.ws.sendCmd({'cmd':'resp', 'data':data});
            break;
        case 'start':
            var href = data.href;
            self.client = new JSDBClient('worker',href);
            self.postMessage({ cmd: 'log', data: 'worker started'});
            break;
        case 'stop':
            self.postMessage({ cmd: 'log', data : 'worker stopped'});
            self.close(); 
            break;
        default:
            self.postMessage({ cmd: 'log', data : 'unknown command: ' + data});
    }
},false);
