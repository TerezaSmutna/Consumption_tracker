$(document).ready(function () {
    $("#id_token-otp_token, #id_generator-token, #id_otp_token").keypress(function (e) {
        if(e.which === 13)  // allow Enter key
            return;

        const chr = String.fromCharCode(e.which);
        if (!(/[0-9]/.test(chr)))
            e.preventDefault();
    });
});
