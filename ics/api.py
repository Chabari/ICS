import frappe
from erpnext import get_default_company
from frappe.utils import flt, nowtime

def get_main_company():
    return frappe.get_doc("Company", get_default_company())

def create_sales_invoice(doc, method):
    _customer = None
    if doc.shipping_address:
        address = frappe.get_doc("Address", doc.shipping_address)
        _customer = frappe.db.get_value("Customer", {'customer_name': address.address_title, 'custom_phone_number': address.phone}, ['name'], as_dict=1)
        if not _customer:
            _customer = frappe.new_doc("Customer")
            _customer.customer_name = address.address_title
            _customer.customer_group = "All Customer Groups"
            _customer.territory = "All Territories"
            _customer.custom_phone_number = address.phone
            _customer.save(ignore_permissions=True)
                
    sales_invoice = frappe.new_doc("Sales Invoice")
    sales_invoice.discount_amount = 0
    sales_invoice.cost_center = doc.cost_center
    sales_invoice.customer = _customer.name if _customer else None
    sales_invoice.set_warehouse = "Stores - TE"
    sales_invoice.due_date = doc.schedule_date
    sales_invoice.posting_date = doc.transaction_date
    sales_invoice.posting_time = nowtime()
    sales_invoice.debit_to = get_main_company().default_receivable_account
    order_items = []
    for itm in doc.items:
        item_doc = frappe.get_doc('Item', itm.item_code)
        order_items.append(frappe._dict({
            'item_code': item_doc.item_code,
            'item_name': item_doc.item_name,
            'description': item_doc.description,
            'item_group': item_doc.item_group,
            'qty': itm.get('qty'),
            'uom': item_doc.stock_uom,
            'rate': itm.get('rate'),
            'amount': itm.get('amount'),
            'income_account': get_main_company().default_income_account
        }))
            
    sales_invoice.set("items", order_items)
    sales_invoice.is_pos = 1
    sales_invoice.paid_amount = doc.total
    
    payments = []
        
    payments.append(frappe._dict({
        'mode_of_payment': "Cash",
        'amount': doc.total,
        'type': "Cash",
        'default': 1
    }))
    sales_invoice.set("payments", payments)
    
    if doc.custom_sales_agents:
        sales_agents = []
        for itm in doc.custom_sales_agents:
            sales_agents.append(frappe._dict({
                'user': itm.user,
                'full_name': itm.full_name,
            }))
                
        sales_invoice.set("custom_sales_agents", sales_agents)

    sales_invoice.flags.ignore_permissions = True
    frappe.flags.ignore_account_permission = True
    sales_invoice.save()
    sales_invoice.flags.ignore_permissions = True
    frappe.flags.ignore_account_permission = True
    sales_invoice.submit()