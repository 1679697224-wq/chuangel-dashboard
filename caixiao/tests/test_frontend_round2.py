import json
from pathlib import Path
import subprocess
import unittest


REPO_ROOT = Path(__file__).resolve().parents[2]
APP_JS = REPO_ROOT / "caixiao/frontend/assets/app.js"
FILTER_UTILS = REPO_ROOT / "caixiao/frontend/assets/filter-utils.js"


class FrontendRound2Tests(unittest.TestCase):
    def node_eval(self, expression):
        script = "const u=require({}); console.log(JSON.stringify({}));".format(
            json.dumps(str(FILTER_UTILS)), expression
        )
        result = subprocess.run(
            ["node", "-e", script], check=True, capture_output=True, text=True
        )
        return json.loads(result.stdout)

    def test_business_unit_is_closed_enumeration(self):
        values = self.node_eval("u.BUSINESS_UNITS")
        self.assertEqual(values, ["Apple线下", "Apple电商", "舒尔电商", "分销渠道"])
        source = APP_JS.read_text(encoding="utf-8")
        self.assertIn('<select name="businessUnit">', source)
        self.assertNotIn('<input name="businessUnit"', source)

    def test_three_level_cascade_and_illegal_combinations(self):
        cascade = self.node_eval("({offline:u.channelsForUnit('Apple线下'),ecommerce:u.channelsForUnit('Apple电商'),shure:u.channelsForUnit('舒尔电商'),distribution:u.channelsForUnit('分销渠道'),aprStores:u.storesForUnitChannel('Apple线下','APR'),jdStore:u.storesForUnitChannel('Apple电商','京东'),shureStore:u.storesForUnitChannel('舒尔电商','天猫')})")
        self.assertEqual(cascade["offline"], ["APR", "即时零售"])
        self.assertEqual(cascade["ecommerce"], ["京东", "苏宁"])
        self.assertEqual(cascade["shure"], ["天猫", "京东"])
        self.assertEqual(cascade["distribution"], ["分销"])
        self.assertEqual(len(cascade["aprStores"]), 10)
        self.assertEqual(cascade["jdStore"], ["京东羽通分期免息店"])
        self.assertEqual(cascade["shureStore"], ["舒尔官方旗舰店"])
        invalid = self.node_eval("({a:u.normalizeGlobalFilters({businessUnit:'舒尔电商',channel:'APR'}),b:u.normalizeGlobalFilters({businessUnit:'Apple线下',channel:'天猫'}),c:u.normalizeGlobalFilters({businessUnit:'Apple电商',channel:'京东',store:'舒尔官方旗舰店'})})")
        self.assertEqual(invalid["a"]["channel"], "")
        self.assertEqual(invalid["b"]["channel"], "")
        self.assertEqual(invalid["c"]["store"], "")

    def test_date_quick_ranges(self):
        ranges = self.node_eval("({today:u.quickDateRange('today',new Date('2026-08-30T12:00:00+08:00')),yesterday:u.quickDateRange('yesterday',new Date('2026-08-30T12:00:00+08:00')),week:u.quickDateRange('week',new Date('2026-08-30T12:00:00+08:00')),month:u.quickDateRange('month',new Date('2026-08-30T12:00:00+08:00'))})")
        self.assertEqual(ranges["today"], {"start":"2026-08-30","end":"2026-08-30"})
        self.assertEqual(ranges["yesterday"], {"start":"2026-08-29","end":"2026-08-29"})
        self.assertEqual(ranges["week"]["start"], "2026-08-24")
        self.assertEqual(ranges["month"]["start"], "2026-08-01")

    def test_compare_options_and_missing_target_notice(self):
        source = APP_JS.read_text(encoding="utf-8")
        for value in ("none", "previous", "year_on_year", "target", "difference"):
            self.assertIn('value="{}"'.format(value), source)
        notice = self.node_eval("u.compareNotice('target')")
        self.assertIn("目标数据待接入", notice)
        self.assertIn("compareNotice(filters.compare)", source)

    def test_sku_url_drilldown_and_refresh_restore(self):
        parsed = self.node_eval("u.skuFromSearch('?sku=SKU-MOCK-001')")
        self.assertEqual(parsed, "SKU-MOCK-001")
        source = APP_JS.read_text(encoding="utf-8")
        self.assertIn("/cx/sku?sku=${encodeURIComponent", source)
        self.assertIn("history.replaceState", source)
        self.assertIn("skuFromSearch(window.location.search)", source)


if __name__ == "__main__":
    unittest.main()
