// Copyright (c) 2020, Michael Weißer and contributors
// For license information, please see license.txt

frappe.ui.form.on('Gift Card', {
	onload: function (frm) {
		var doc = frm.doc;

		// Print Format
		if (!frm.meta.default_print_format) {
			frm.meta.default_print_format = frm.doc.print_format;
		}

		// Queries
		//frm.set_query('billing_contact', erpnext.erpnext.queries.contact_query);
		//frm.set_query('billing_address', erpnext.queries.address_query);

		frm.set_query('billing_contact', function (doc) {
			if (!doc.billing_customer) {
				frappe.throw(__("Please set {0}",
					[__(frappe.meta.get_label(doc.doctype, frappe.dynamic_link.fieldname, doc.name))]));
			}
			return {
				query: 'frappe.contacts.doctype.contact.contact.contact_query',
				filters: {
					link_doctype: 'Customer',
					link_name: doc.billing_customer
				}
			};
		});

		frm.set_query('billing_address', function (doc) {
			if (!doc.billing_customer) {
				frappe.throw(__("Please set {0}",
					[__(frappe.meta.get_label(doc.doctype, frappe.dynamic_link.fieldname, doc.name))]));
			}
			return {
				query: 'frappe.contacts.doctype.address.address.address_query',
				filters: {
					link_doctype: 'Customer',
					link_name: doc.billing_customer
				}
			};
		});

		frm.set_query('shipping_contact', function (doc) {
			if (!doc.shipping_customer) {
				frappe.throw(__("Please set {0}",
					[__(frappe.meta.get_label(doc.doctype, frappe.dynamic_link.fieldname, doc.name))]));
			}
			return {
				query: 'frappe.contacts.doctype.contact.contact.contact_query',
				filters: {
					link_doctype: 'Customer',
					link_name: doc.shipping_customer
				}
			};
		});

		frm.set_query('shipping_address', function (doc) {
			if (!doc.shipping_customer) {
				frappe.throw(__("Please set {0}",
					[__(frappe.meta.get_label(doc.doctype, frappe.dynamic_link.fieldname, doc.name))]));
			}
			return {
				query: 'frappe.contacts.doctype.address.address.address_query',
				filters: {
					link_doctype: 'Customer',
					link_name: doc.shipping_customer
				}
			};
		});
	},

	refresh: function (frm) {
		if (frm.doc.docstatus == 1 && frm.doc.status != 'Redeemed') {
			if (frm.has_perm('write') && frm.doc.is_stopped == 0) {
				if (frm.doc.is_paid == 0 || frm.doc.has_received == 0) {
					frm.add_custom_button(__('Update Status'), function () {
						frm.trigger("update_status");
					});
				}

				if (frm.doc.current_value > 0 && frm.doc.has_received == 1) {
					frm.add_custom_button(__('Redeem'), function () {
						frm.trigger("redeem_gift_card");
					});
				}
			}

			if (frappe.perm.has_perm(frm.doctype, 1, 'write') == 1) {
				frm.add_custom_button(frm.doc.is_stopped == 0 ? __('Stop') : __('Resume'),
					() => frm.call({
						doc: frm.doc,
						method: 'stop_gift_card',
						freeze: true,
						callback: () => {
							//frm.refresh();
							frm.reload_doc();
						}
					})
				);

			}
		}
	},

	update_status: function (frm) {
		let paid_read_only = (frm.doc.is_paid == 1 || frappe.perm.has_perm(frm.doctype, 1, 'write') == 0) ? 1 : 0;
		let d = new frappe.ui.Dialog({
			title: __('Update Status'),
			fields: [
				{
					label: __('Is Paid'),
					fieldname: 'is_paid',
					fieldtype: 'Check',
					//read_only: frm.doc.is_paid == 1 ? 1 : 0,
					read_only: paid_read_only,
					default: frm.doc.is_paid,
					description: __('Gift Card has been paid by the customer.')
				},
				{
					label: __('Has received'),
					fieldname: 'has_received',
					fieldtype: 'Check',
					read_only: frm.doc.has_received == 1 ? 1 : 0,
					default: frm.doc.has_received,
					description: __('The Gift Card has been received by or is sent to the customer.')
				}
			],
			primary_action_label: __('Update'),
			primary_action(values) {
				//console.log(values);
				d.hide();
				if (values.is_paid == 1 || values.has_received == 1) {
					frm.call({
						doc: frm.doc,
						method: 'update_status_dialog',
						args: {
							is_paid: values.is_paid,
							has_received: values.has_received
						},
						freeze: true,
						callback: () => {
							//frm.refresh();
							frm.reload_doc();
						}
					})
				}

			}
		});
		d.show();

	},

	redeem_gift_card: function (frm) {
		if (frm.doc.allow_partial_redemption == 0) {

			frappe.confirm(__('Redeem the full outstanding value of {0} {1} for this gift card?', [frm.doc.current_value, frm.doc.currency]),
				() => {
					// action to perform if Yes is selected
					frm.call({
						doc: frm.doc,
						method: 'redeem',
						freeze: true,
						callback: () => {
							//frm.refresh();
							frm.reload_doc();
						}
					})
				})

		} else {
			let d = new frappe.ui.Dialog({
				title: __('Redeem'),
				fields: [
					{
						label: __('Redeemed Value'),
						fieldname: 'redeemed_value',
						fieldtype: 'Currency',
						reqd: 1,
						read_only: frm.doc.allow_partial_redemption == 1 ? 0 : 1,
						default: frm.doc.current_value,
						options: frm.doc.currency,
						description: __('The amount that should be redeemed.')
					}
				],
				primary_action_label: __('Submit'),
				primary_action(values) {
					//console.log(values);
					d.hide();
					frm.call({
						doc: frm.doc,
						method: 'redeem',
						args: {
							redeemed_value: values.redeemed_value
						},
						freeze: true,
						callback: () => {
							//frm.refresh();
							frm.reload_doc();
						}
					})
				}
			});
			d.show();
		}
	},


	template: function (frm) {
		var validity;
		frappe.db.get_value('Gift Card Template', frm.doc.template, 'validity_years')
			.then(r => {
				validity = r.message.validity_years; // Open
				if (validity != 0) {
					var end_date = frappe.datetime.add_months(frm.doc.valid_from, validity * 12);
					frm.set_value("valid_to", end_date);
				} else {
					frm.set_value("valid_to", null);
				}
			});
	}

});
