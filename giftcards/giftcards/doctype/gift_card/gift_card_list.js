frappe.listview_settings['Gift Card'] = {
    add_fields: ["valid_to", "is_stopped"],
    get_indicator: function (doc) {
        if (doc.docstatus == 0) {
            return [__("Draft"), "red", "docstatus,=,0"];

        } else if (doc.docstatus == 1) {
            if (doc.status == 'Redeemed') {
                return [__("Redeemed"), "grey", "status,=,Redeemed"];
            } else if (doc.status == 'Unpaid & Unsent') {
                return [__("Unpaid & Unsent"), "orange", "status,=,Unpaid & Unsent"];
            } else if (doc.status == 'Unsent') {
                return [__("Unsent"), "orange", "status,=,Unsent"];
            } else if (doc.status == 'Unpaid') {
                return [__("Unpaid"), "orange", "status,=,Unpaid"];

            } else if (frappe.datetime.get_diff(doc.valid_to) < 0) {
                return [__("Expired"), "red", "valid_to,<,Today"];
            } else if (doc.status == 'Stopped') {
                return [__("Stopped"), "red", "status,=,Stopped"];
            } else {
                return [__("Open"), "green", "docstatus,=,1"];
            }
        } else if (doc.docstatus == 2) {
            return [__("Cancelled"), "red", "docstatus,=,2"];
        }
    }
};
