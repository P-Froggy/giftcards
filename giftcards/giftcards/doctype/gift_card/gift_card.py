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
		self.validate_dates()
		self.set_status()

	def validate_values(self):
		if self.target_value and not self.target_value > 0:
			frappe.throw(_("Target value must be a positive number."))
		if self.current_value and not self.current_value > 0:
			frappe.throw(_("Current value must be a positive number."))

	def validate_dates(self):
		if (self.valid_from and self.valid_to) and self.valid_from > self.valid_to:
			frappe.throw(_("Valid from date has to be smaller than valid to date."))
		elif self.valid_to and date_diff(self.valid_to, today()) < 0:
			frappe.throw(_("Valid to date has to be in the future."))


	def before_submit(self):
		if self.is_paid == 1:
			self.current_value = self.target_value
			self.per_current_value = 100
		self.posting_date = today()
		self.set_status()
		#self.save()

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

		if update:
			self.db_set('status', self.status, update_modified = update_modified)

	@frappe.whitelist()
	def update_status_dialog(self, is_paid=0, has_received=0):
		if is_paid:
			self.is_paid = 1
			self.current_value = self.target_value
			self.per_current_value = 100
		if has_received:
			self.has_received = 1
		self.set_status()
		self.save()


	@frappe.whitelist()
	def stop_gift_card(self):
		self.is_stopped = 0 if self.is_stopped else 1
		self.set_status()
		self.save()

	@frappe.whitelist()
	def redeem(self, redeemed_value=0):
		if redeemed_value and self.current_value < redeemed_value:
			frappe.throw(_("Redeemed value cannot be greater than the current value."))

		if self.allow_partial_redemption:
			self.current_value -= redeemed_value
			self.per_current_value = flt(self.current_value / self.target_value * 100)
		else:
			self.current_value = 0
			self.per_current_value = 0

		if self.current_value == 0 and not self.redemption_date:
			#self.redemption_date = today()
			self.db_set('redemption_date', today())
		self.set_status()
		self.save()
