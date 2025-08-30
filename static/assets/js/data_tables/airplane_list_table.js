$(document).ready(function () {
    $('#airplaneListTable').DataTable(
        {
            info: false,
            searching: true,
            paging: false,
            columnDefs: [
                {
                    targets: [-2, -1],
                    orderable: false
                }
            ],
            order: []
        }
    );
});