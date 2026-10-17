/** @odoo-module **/
import { registry } from "@web/core/registry";
import { download } from "@web/core/network/download";

registry.category("ir.actions.report handlers").add("xlsx", async (action) => {
    if (action.report_type !== "xlsx") {
        return false;
    }
    // Send the report options to the controller, which streams the xlsx back.
    await download({
        url: "/xlsx_reports",
        data: action.data,
    });
    return true;
});
