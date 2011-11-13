
var worker = new Worker('worker.js');

/*
 * Here we create the event handler for receiving commands from the worker 
 * thread which is handling the websocket and talking to the JSDB CLI tool.
 */
worker.addEventListener('message', function(e) {
    if ( e.data.cmd == 'exec' ) {
        json = JSON.parse(e.data.data);
        try {
            value = eval(json.js);
            worker.postMessage({'cmd':'jsresp',
                                'execid':json.execid,
                                'pass':'true',
                                'info':""+value}); 
        } catch(err) { 
            worker.postMessage({'cmd':'jsresp',
                                'execid':json.execid,
                                'pass':'false',
                                'info':""+err}); 
        }
    } else if ( e.data.cmd == 'log') {
        console.log('JSDB: ' + e.data.data);
    }
}, false);

worker.postMessage({'cmd':'start', 'href':document.location.href});