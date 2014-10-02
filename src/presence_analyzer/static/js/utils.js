var repository = "https://intranet.stxnext.pl/api/images/users/";

function parseInterval(value) {
    var result = new Date(1,1,1);
    result.setMilliseconds(value*1000);
    return result;
}

function changeImageFileName(user_id) {
    var src = repository + user_id;
    $('#image').show();
    $('#image > img').attr('src', src);
}
