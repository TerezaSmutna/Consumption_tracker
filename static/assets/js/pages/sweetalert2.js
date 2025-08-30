document.querySelectorAll('.delete-btn').forEach(function (btn) {
    btn.addEventListener('click', function (e) {
        e.preventDefault();
        const objectStr = JSON.parse('"' + this.getAttribute('data-object') + '"');
        Swal.fire({
            title: 'Are you sure?',
            html: `You are about to delete:<br><br>${objectStr}`,
            icon: 'warning',
            showCancelButton: true,
            confirmButtonText: 'Yes, delete it!',

        }).then((result) => {
            if (result.isConfirmed) {
                this.closest('form').submit();
            }
        });
    });
});


document.querySelectorAll('.bulk-delete-btn').forEach(function (btn) {
    btn.addEventListener('click', function (e) {
        e.preventDefault();
        let checkedDomains = [];
        const checkboxes = document.querySelectorAll('input[type="checkbox"][name="domains"]:checked');

        for (let i = 0; i < checkboxes.length; i++) {
            const label = document.querySelector('label[for="' + checkboxes[i].id + '"]');
            if (label) {
                checkedDomains.push(label.textContent.trim());
            }
        }
        console.log(checkedDomains); // output array of checked domains
        const objectStr = JSON.parse('"' + this.getAttribute('data-object') + '"');

        let alertText = '';
        checkedDomains.forEach(domain => {
            let parts = objectStr.split('" "');
            parts[1] = `@${domain}`;
            let newString = parts.join('" "');

            alertText += '<br>' + escapeHtml(newString);
            console.log(newString);
        });
        console.log(alertText)

        Swal.fire({
            title: 'Are you sure?',
            html: `You are about to delete following rules:<br>${alertText}`,
            icon: 'warning',
            showCancelButton: true,
            confirmButtonText: 'Yes, delete it!',

        }).then((result) => {
            if (result.isConfirmed) {
                const button = document.getElementById('button-name');
                if (button) {
                    button.value = this.getAttribute('name');
                }
                this.closest('form').submit();
            }
        });
    });
});


function escapeHtml(unsafe) {
    let textNode = document.createTextNode(unsafe);
    let div = document.createElement('div');
    div.appendChild(textNode);
    return div.innerHTML;
}