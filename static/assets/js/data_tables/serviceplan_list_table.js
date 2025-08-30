$(document).ready(function () {
    $('#servicePlanListTable').DataTable(
        {
            info: false,
            searching: true,
            paging: false,
            columnDefs: [
                {
                    targets: [-5, -4, -3, -2, -1],
                    orderable: false
                }
            ],
            order: []
        }
    );
});