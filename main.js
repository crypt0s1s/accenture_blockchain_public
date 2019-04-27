function postToChain() {
    var xhr = new XMLHttpRequest();
    xhr.open("POST", "http://google.com/", true);
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.send(JSON.stringify({
        "test":"string"
    }));
}