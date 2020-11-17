from __future__ import unicode_literals
from frappe import _

def get_data():
	return [
		{
			"label": _("Sales"),
			"icon": "fa fa-star",
			"items": [
				{
					"type": "doctype",
					"name": "Gift Card",
					"description": _("Create and manage gift cards."),
				}				
			]
		},

		{
			"label": _("Items and Pricing"),
			"icon": "fa fa-star",
			"items": [
				{
					"type": "doctype",
					"name": "Gift Card Template",
					"description": _("Create and manage gift card templates."),
				}				
			]
		},
		
	]
