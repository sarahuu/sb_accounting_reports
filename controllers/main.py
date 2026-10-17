import json

from odoo import http
from odoo.http import content_disposition, request


class XLSXReportController(http.Controller):
    @http.route('/xlsx_reports', type='http', auth='user', csrf=False)
    def get_report_xlsx(self, model, options, output_format, report_name,
                        token='ads'):
        """Build the xlsx workbook and return it as a download response."""
        report_object = request.env[model].with_user(request.session.uid)
        options = json.loads(options)
        if output_format == 'xlsx':
            response = request.make_response(
                None,
                headers=[
                    ('Content-Type', 'application/vnd.ms-excel'),
                    ('Content-Disposition',
                     content_disposition(f"{report_name}.xlsx")),
                ],
            )
            report_object.get_xlsx_report(options, response)
            response.set_cookie('fileToken', token)
            return response
