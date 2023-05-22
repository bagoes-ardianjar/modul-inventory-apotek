# -*- coding: utf-8 -*-
{
    'name': 'Inventory (ATI)',
    'version': '1.0.4.7',
    'author': 'Ibad - Akselerasi Teknologi Investama',
    'category': 'Inventory',
    'maintainer': 'Ibad - Akselerasi Teknologi Investama',
    'summary': """Stock & Logistic Management""",
    'description': """
        Stock & Logistic Management
    """,
    'website': 'https://akselerasiteknologi.id/',
    'license': 'LGPL-3',
    'support': 'Ahmad.Ibad@akselerasiteknologi.id',
    'depends': [
        'base',
        'stock',
        'sh_message',
        'mail',
        'account',
        'stock_account',
        'stock_picking_batch',
        'product_expiry',
        # 'web_studio',
        # 'website_studio',
        'report_xlsx',
        'ati_pbf_product'
    ],
    'data': [
        'security/ir.model.access.csv',
        'reports/no_backorder_report.xml',
        'reports/report_delivery_order.xml',
        'reports/batch_transfer_report.xml',
        'reports/report_tanda_terima_retur.xml',
        'views/stock_picking_type.xml',
        'views/stock_picking_views.xml',
        'views/stock_picking_batch.xml',
        'views/stock_move_line.xml',
        'views/company_view.xml',
        'wizards/prekusor_kemenkes_view.xml',
        'wizards/stock_picking_return_views.xml',
        'wizards/do_reportbutton_view.xml',
        'data/mail_template_data.xml',
    ],

    'installable': True,
    'application': True,
    'auto_install': False,
}