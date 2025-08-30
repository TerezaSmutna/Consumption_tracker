$(document).ready(function () {
    $('#meterListTable').DataTable(
        {
            info: false,
            searching: true,
            paging: false,
            columnDefs: [
                {
                    targets: [-1],
                    orderable: false
                }
            ],
            order: [],
            language: {
                url: datatables_lang_url,
                searchPlaceholder: ""
            }
        }
    );
});