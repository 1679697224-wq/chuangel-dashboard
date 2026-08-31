from pathlib import Path
import unittest


REPO_ROOT = Path(__file__).resolve().parents[2]
INDEX = REPO_ROOT / "caixiao/frontend/index.html"
APP_JS = REPO_ROOT / "caixiao/frontend/assets/app.js"
APP_CSS = REPO_ROOT / "caixiao/frontend/assets/app.css"


class BusinessFrontendInformationArchitectureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.index = INDEX.read_text(encoding="utf-8")
        cls.source = APP_JS.read_text(encoding="utf-8")
        cls.css = APP_CSS.read_text(encoding="utf-8")

    def test_business_navigation_has_exactly_five_groups(self):
        for number, name in (
            ("01", "经营总览"), ("02", "商品经营"), ("03", "库存与采购"),
            ("04", "政策经营"), ("05", "行动中心"),
        ):
            self.assertIn("<b>{}</b><span>{}</span>".format(number, name), self.index)
        self.assertEqual(self.index.count('class="nav-group"'), 5)

    def test_technical_tools_are_only_in_admin_navigation(self):
        business_nav = self.index.split('<nav id="mainNav"', 1)[1].split("</nav>", 1)[0]
        for technical in ("Sandbox", "吉客云", "数据映射", "口径管理", "版本管理"):
            self.assertNotIn(technical, business_nav)
        self.assertIn('id="adminNav"', self.index)
        self.assertIn("⚙ 系统管理", self.index)
        self.assertIn("document.getElementById(\"adminNav\").hidden=!isAdmin()", self.source)

    def test_all_required_business_routes_are_registered(self):
        for route in (
            "/cx/anomalies", "/cx/priorities", "/cx/products", "/cx/sku",
            "/cx/inventory", "/cx/purchase", "/cx/transfer", "/cx/policy/dg",
            "/cx/policy/subsidy", "/cx/policy", "/cx/actions", "/cx/actions/tracking",
        ):
            self.assertIn('"{}"'.format(route), self.source + self.index)

    def test_business_pages_use_business_language(self):
        for phrase in (
            "销售达成", "库存周转", "报需与采购", "调拨与在途",
            "DG任务", "单店补贴", "我的待办", "执行跟踪",
        ):
            self.assertIn(phrase, self.source + self.index)

    def test_demo_label_is_single_low_interference_control(self):
        self.assertIn("当前为模拟数据，仅用于页面和交互验证。", self.index + self.source)
        self.assertIn("pill.hidden=demo", self.source)

    def test_tables_support_sticky_sort_search_and_pagination(self):
        for phrase in ("position:sticky", "table-search", "table-prev", "table-next", "th.sortable"):
            self.assertIn(phrase, self.css + self.source)

    def test_mobile_layout_has_375_compatible_breakpoint(self):
        self.assertIn("@media(max-width:390px)", self.css)
        self.assertIn("overflow:auto", self.css)
        self.assertIn("mobileFilterToggle", self.source)
        self.assertIn(".global-filters form.open", self.css)

    def test_formal_logo_asset_replaces_simulated_text_mark(self):
        self.assertIn('src="/cx/assets/chuangel-logo-white.png"', self.index)
        self.assertIn('src="/cx/assets/chuangel-logo-navy.png"', self.index)
        self.assertNotIn('class="brand-mark"', self.index)

    def test_home_has_complete_sales_and_inventory_metric_positions(self):
        for phrase in (
            "月末预计达成率", "同比", "环比", "毛利额", "毛利率",
            "现货库存金额", "在途库存金额", "经营库存金额", "周转天数",
            "90天+库存", "180天+库存", "360天+库存", "已计提库存",
            "零库存SKU", "累计清理率",
        ):
            self.assertIn(phrase, self.source)

    def test_distribution_channel_name_has_no_legacy_business_wording(self):
        frontend = "".join(path.read_text(encoding="utf-8") for path in (REPO_ROOT / "caixiao/frontend").rglob("*.js"))
        business_docs = "".join(path.read_text(encoding="utf-8") for path in (REPO_ROOT / "caixiao/docs").glob("*.md"))
        self.assertNotIn("Apple渠道", frontend + business_docs)
        self.assertIn("分销渠道", frontend)

    def test_product_filter_has_derived_business_tags(self):
        for phrase in ("productSearchTags", "畅销", "慢动销", "滞销", "DG商品"):
            self.assertIn(phrase, self.source)

    def test_data_governance_routes_and_raw_lock_remain(self):
        for phrase in (
            "/cx/admin/data-mapping", "/cx/admin/connectors/jikexyun",
            "/cx/admin/validation/sandbox", "raw_code、raw_name、history_mapping永久只读",
            "验证数据，不代表正式经营口径",
        ):
            self.assertIn(phrase, self.source + self.index)


if __name__ == "__main__":
    unittest.main()
