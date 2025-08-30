$(document).ready(function () {
    $('#inspectionListTable').DataTable(
        {
            info: false,
            searching: true,
            paging: false,
            columnDefs: [
                {
                    targets: [0],
                    render: function (data, type, row) {
                        if (type === 'sort' || type === 'type') {
                            // Convert the date to a timestamp for sorting
                            return moment(data, 'DD.MM.YYYY').valueOf();
                        }
                        return data;  // Display the original date format for other data types
                    }
                },
                {
                    targets: [-2, -1],
                    orderable: false
                }
            ],
            order: []
        }
    );
});