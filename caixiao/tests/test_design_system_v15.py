from pathlib import Path
import unittest


REPO_ROOT = Path(__file__).resolve().parents[2]
DESIGN = REPO_ROOT / "DESIGN.md"
INDEX = REPO_ROOT / "caixiao/frontend/index.html"
APP_JS = REPO_ROOT / "caixiao/frontend/assets/app.js"
APP_CSS = REPO_ROOT / "caixiao/frontend/assets/app.css"
FILTERS = REPO_ROOT / "caixiao/frontend/assets/filter-utils.js"
BACKEND = REPO_ROOT / "caixiao/backend/app.py"


class DesignSystemV15Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.design = DESIGN.read_text(encoding="utf-8")
        cls.index = INDEX.read_text(encoding="utf-8")
        cls.app = APP_JS.read_text(encoding="utf-8")
        cls.css = APP_CSS.read_text(encoding="utf-8")
        cls.filters = FILTERS.read_text(encoding="utf-8")
        cls.backend = BACKEND.read_text(encoding="utf-8")

    def test_design_document_and_required_sections_exist(self):
        self.assertTrue(DESIGN.is_file())
        for section in (
            "Design Philosophy", "Visual Atmosphere", "Color Tokens", "Typography",
            "Spacing System", "Grid", "Sidebar", "Top Filter Bar", "KPI Cards",
            "Tables", "Charts", "Tabs", "Filters", "Inputs", "Buttons",
            "Badges / Status", "Empty State", "Loading State", "Error State",
            "Drawer / Modal", "SKU Detail", "Responsive", "Mobile", "Demo Mode",
            "Admin Area", "Do's", "Don'ts",
        ):
            self.assertIn(section, self.design)

    def test_core_semantic_tokens_are_implemented(self):
        for token in (
            "--color-brand-primary", "--color-brand-deep", "--color-brand-light",
            "--color-bg-page", "--color-bg-surface", "--color-bg-muted",
            "--color-border-default", "--color-border-subtle",
            "--color-text-primary", "--color-text-secondary", "--color-text-muted",
            "--color-success", "--color-warning", "--color-danger", "--color-info",
        ):
            self.assertIn(token, self.design)
            self.assertIn(token, self.css)

    def test_business_navigation_and_three_level_filters_are_unchanged(self):
        self.assertEqual(self.index.count('class="nav-group"'), 5)
        for label in ("经营总览", "商品经营", "库存与采购", "政策经营", "行动中心"):
            self.assertIn(label, self.index)
        for unit in ("Apple线下", "Apple电商", "舒尔电商", "分销渠道"):
            self.assertIn(unit, self.filters)
        for channel in ("APR", "即时零售", "京东", "苏宁", "天猫", "分销"):
            self.assertIn(channel, self.filters)
        self.assertIn("京东羽通分期免息店", self.filters)
        self.assertIn("苏宁啟韬专卖店", self.filters)
        self.assertNotIn("Apple渠道", self.app + self.filters)

    def test_technical_pages_remain_outside_business_navigation(self):
        business_nav = self.index.split('<nav id="mainNav"', 1)[1].split("</nav>", 1)[0]
        for word in ("Sandbox", "API", "数据映射", "口径管理", "版本管理"):
            self.assertNotIn(word, business_nav)
        self.assertIn('id="adminNav"', self.index)

    def test_demo_formal_and_sandbox_isolation_remains(self):
        self.assertEqual(self.index.count('id="demoBanner"'), 1)
        self.assertIn("DemoAdapter() if settings.demo_mode else None", self.backend)
        self.assertNotIn("if not payload: demo", self.backend)
        self.assertIn("验证数据，不代表正式经营口径", self.app)
        self.assertNotIn("（演示）", self.app)
        self.assertNotIn("演示公式", self.app)

    def test_sku_url_and_nine_part_business_hierarchy(self):
        self.assertIn("skuFromSearch(window.location.search)", self.app)
        self.assertIn("history.replaceState", self.app)
        for heading in (
            "01 商品概览", "02 经营判断", "03 销售趋势", "04 库存与WOI",
            "05 库龄", "06 渠道 / 仓库 / 门店", "07 价格与利润",
            "08 政策", "09 风险与建议动作",
        ):
            self.assertIn(heading, self.app)

    def test_all_thirteen_business_routes_remain(self):
        for route in (
            "/cx/anomalies", "/cx/priorities", "/cx/products", "/cx/sku",
            "/cx/inventory", "/cx/purchase", "/cx/transfer", "/cx/policy/dg",
            "/cx/policy/subsidy", "/cx/policy", "/cx/actions", "/cx/actions/tracking",
        ):
            self.assertIn(route, self.index + self.app)

    def test_confirmed_core_metrics_remain(self):
        for metric in (
            "销售额", "销量", "销售目标", "达成率", "时间进度", "销售差额",
            "同比", "环比", "月末预计达成", "毛利额", "毛利率",
            "现货库存", "在途库存", "经营库存", "现货WOI", "含在途WOI",
            "库存周转天数", "90天+", "180天+", "360天+", "已计提库存",
            "建议报需", "实际报需", "采购数量", "DG SI", "DG ST", "单店补贴",
        ):
            self.assertIn(metric, self.app)

    def test_logo_and_375_structure_remain(self):
        self.assertIn('src="/cx/assets/chuangel-logo-white.png"', self.index)
        self.assertIn('src="/cx/assets/chuangel-logo-navy.png"', self.index)
        self.assertIn("@media(max-width:390px)", self.css)
        self.assertIn(".global-filters form.open", self.css)
        self.assertIn("overflow: auto", self.css)
        self.assertIn(".executive-grid { grid-template-columns: 1fr; }", self.css)


if __name__ == "__main__":
    unittest.main()
