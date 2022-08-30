function other() {
    var x = document.getElementById("select1").value;
    if (x == "other"){
        document.getElementById("select2label").style.display = "block"
        document.getElementById("select2in").style.display = "block"
        document.getElementById("select2br").style.display = "none"
    }else{
        document.getElementById("select2label").style.display = "none"
        document.getElementById("select2in").style.display = "none"
        document.getElementById("select2br").style.display = "block"
    }
}

function other2() {
    var x = document.getElementById("select2").value;
    if (x == "other"){
        document.getElementById("input2").style.display = "block"
    }else{
        document.getElementById("input2").style.display = "none"
    }
}

function conf() {
    document.getElementById("confirm-form2").style.display = "block"
    document.getElementById("gebruiker-reset-button").style.display = "none"
}

function abortconf() {
    document.getElementById("confirm-form2").style.display = "none"
    document.getElementById("gebruiker-reset-button").style.display = "block"
}


function log(test){
    var magid = document.getElementById("magazijn_id66");
    var myelement = document.getElementById("logid");
    myelement.value = test;
    myelement.focus()
    window.dispatchEvent(new KeyboardEvent('keydown', {
        key: " ",
        keyCode: 32,
        code: "Space",
        shiftKey: false,
        ctrlKey: false,
        metaKey: false
    }));
        //fetch(magid+'/Magazijn Log')
        //    .then(function (response) {
        //        return response.json();
        //    }).then(function (text) {
        //        console.log('GET response:');
        //        console.log(text.greeting);
        //    });
}