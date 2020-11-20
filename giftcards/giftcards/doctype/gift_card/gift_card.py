# -*- coding: utf-8 -*-
# Copyright (c) 2020, Michael Weißer and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import frappe
from frappe import _
# import frappe
from frappe.model.document import Document
from frappe.utils import today, date_diff, getdate, flt
from frappe.contacts.doctype.address.address import get_address_display


class GiftCard(Document):

	def validate(self):
		self.validate_values()
		self.validate_customers()
		self.validate_dates()

	def validate_values(self):
		if self.target_value and not self.target_value > 0:
			frappe.throw(_("Target value must be a positive number."))
		if self.current_value and not self.current_value > 0:
			frappe.throw(_("Current value must be a positive number."))

	def validate_customers(self):
		if not self.is_paid and not (self.billing_customer and self.billing_contact and self.billing_address):
			frappe.throw(_("A billing customer, contact and address has to be set if the gift card is not paid yet."))
		if not self.has_received and not (self.shipping_customer and self.shipping_contact and self.shipping_address):
			frappe.throw(_("A shipping customer, contact and address has to be set if the gift card has to be sent to the customer."))

	def validate_dates(self):
		if (self.valid_from and self.valid_to) and self.valid_from > self.valid_to:
			frappe.throw(_("Valid from date has to be smaller than valid to date."))
		elif self.valid_to and date_diff(self.valid_to, today()) < 0:
			frappe.throw(_("Valid to date has to be in the future."))

	def on_submit(self):
		if self.is_paid == 1 and not self.current_value:
			self.db_set('current_value', self.target_value)
		if not self.posting_date:
			self.db_set('posting_date', today())
		self.set_status(update=True)

	def on_cancel(self):
		self.set_status(update=True)

	#def before_print(self):
	#	self.add_comment("Info", _("printed document"))

	def set_status(self, update=False, status=None, update_modified=True):
		if self.docstatus == 0:
			self.status = 'Draft'
		elif self.docstatus == 1:
			if self.is_stopped == 1:
				self.status = 'Stopped'
			elif self.is_paid == 0 and self.has_received == 0:
				self.status = 'Unpaid & Unsent'
			elif self.is_paid == 1 and self.has_received == 0:
				self.status = 'Unsent'
			elif self.is_paid == 0 and self.has_received == 1:
				self.status = 'Unpaid'
			elif self.current_value > 0 and self.is_paid == 1 and self.has_received == 1:
				self.status = 'Open'
			elif self.current_value == 0 and self.is_paid == 1 and self.has_received == 1:
				self.status = 'Redeemed'
		elif self.docstatus == 2:
			self.status = 'Cancelled'

		# Update Current Value Percentage
		if self.current_value and self.target_value:
			self.per_current_value = flt(self.current_value / self.target_value * 100, 1)
		else:
			self.per_current_value = 0

		if update:
			old_doc = self.get_doc_before_save()
			if old_doc and old_doc.status != self.status:
				self.add_comment("Label", _(self.status))
			self.db_set('status', self.status, update_modified = update_modified)
			self.db_set('per_current_value', self.per_current_value)


	@frappe.whitelist()
	def update_status_dialog(self, is_paid=0, has_received=0):
		if is_paid == 0 and has_received == 0:
			return
		self.check_permission(permtype='write')

		if is_paid and self.is_paid == 0:
			self.db_set('is_paid', 1)
			self.db_set('current_value', self.target_value)

		if has_received and self.has_received == 0:
			self.db_set('has_received', 1)

		self.set_status(update=True)


	@frappe.whitelist()
	def stop_gift_card(self):
		self.check_permission(permtype='write')

		self.db_set('is_stopped', 0 if self.is_stopped else 1)
		self.set_status(update=True)

	@frappe.whitelist()
	def redeem(self, redeemed_value=0):
		self.check_permission(permtype='write')
	
		if self.allow_partial_redemption and 0 < redeemed_value < self.current_value:
			self.db_set('current_value', self.current_value - redeemed_value)
			self.add_comment("Edit", _("redeemed {0}, new value is {1}").format(
				frappe.bold(frappe.format(redeemed_value, dict(fieldtype="Currency", options="currency"))),
				frappe.bold(frappe.format(self.current_value, dict(fieldtype="Currency", options="currency")))
			))

		elif self.allow_partial_redemption == 0 or redeemed_value == self.current_value:
			self.db_set('current_value', 0)
			if not self.redemption_date:
				self.db_set('redemption_date', today())

		else:
			frappe.throw(_("The redemption value must be between {0} and {1}.").format(
				frappe.bold(frappe.format(0, dict(fieldtype="Currency", options="currency"))),
				frappe.bold(frappe.format(self.current_value, dict(fieldtype="Currency", options="currency")))
			))

		self.set_status(update=True)
