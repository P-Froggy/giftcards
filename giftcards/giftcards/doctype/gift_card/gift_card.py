# -*- coding: utf-8 -*-
# Copyright (c) 2020, Michael Weißer and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import frappe
from frappe import _
# import frappe
from frappe.model.document import Document
from frappe.utils import today, date_diff, getdate, flt


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
		if not self.is_paid and not (self.buying_customer and self.buying_contact and self.buying_address):
			frappe.throw(_("A buying customer has to be set if the gift card is not paid yet."))
		if not self.has_received and not (self.receiving_customer and self.receiving_contact and self.receiving_address):
			frappe.throw(_("A receiving customer has to be set if the gift card has to be sent to the customer."))

	def validate_dates(self):
		if (self.valid_from and self.valid_to) and self.valid_from > self.valid_to:
			frappe.throw(_("Valid from date has to be smaller than valid to date."))
		elif self.valid_to and date_diff(self.valid_to, today()) < 0:
			frappe.throw(_("Valid to date has to be in the future."))


	def on_submit(self):
		if self.is_paid == 1:
			self.db_set('current_value', self.target_value)
		self.db_set('posting_date', today())
		self.set_status(update=True)

	def on_cancel(self):
		self.set_status(update=True)

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
			if old_doc.status != self.status:
				self.add_comment("Label", _(self.status))
			self.db_set('status', self.status, update_modified = update_modified)
			self.db_set('per_current_value', self.per_current_value)


	@frappe.whitelist()
	def update_status_dialog(self, is_paid=0, has_received=0):
		if is_paid:
			self.db_set('is_paid', 1)
			self.db_set('current_value', self.target_value)

		if has_received:
			self.db_set('has_received', 1)
		self.set_status(update=True)


	@frappe.whitelist()
	def stop_gift_card(self):
		self.db_set('is_stopped', 0 if self.is_stopped else 1)
		self.set_status(update=True)

	@frappe.whitelist()
	def redeem(self, redeemed_value=0):
		if redeemed_value and self.current_value < redeemed_value:
			frappe.throw(_("Redeemed value cannot be greater than the current value."))

		if self.allow_partial_redemption and self.current_value > redeemed_value:
			self.db_set('current_value', self.current_value - redeemed_value)
			self.add_comment("Edit", _("redeemed <b>{0}</b>, new value is <b>{1}</b>.".format(
				frappe.format(redeemed_value, dict(fieldtype="Currency", options="currency")),
				frappe.format(self.current_value, dict(fieldtype="Currency", options="currency"))
				)))
		else:
			self.db_set('current_value', 0)

		if self.current_value == 0 and not self.redemption_date:
			self.db_set('redemption_date', today())
		self.set_status(update=True)

