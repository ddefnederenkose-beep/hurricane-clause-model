"""Headless run of the Streamlit app: defaults and the B'-lump rule must reproduce docs/RESULTS_v3.md (Tables 1 and 4)."""
import re
import pytest

pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest
from tests.helpers import SIM

APP = str(__import__("pathlib").Path(__file__).resolve().parent.parent / "app.py")


def _nums(at):
    html = " ".join(m.value for m in at.markdown)
    return re.findall(r'class="num[^>]*>([^<]*)', html), html


def test_app_defaults_and_bprime_lump_reproduce_results_v3():
    at = AppTest.from_file(APP, default_timeout=300).run()
    assert not at.exception
    nums, html = _nums(at)
    assert nums[:6] == ["23.1%", "24.7%", "+1.6&#8239;points", "38.5%", "25.7%", "&minus;12.8&#8239;points"]
    assert "Financing-stress episode" in html and html.count("attributable") == 1 and "formerly 'hurricane-attributable crisis'" in html
    assert "raises financing-stress risk" in html and "sign is opposite" in html
    [x for x in at.sidebar.selectbox if x.label == "Repayment rule"][0].select("Grenada's actual: one lump sum at strike year + 6 (B'-lump)").run()
    assert not at.exception
    nums, _ = _nums(at)
    assert nums[:6] == ["23.1%", "52.3%", "+29.2&#8239;points", "38.5%", "52.6%", "+14.1&#8239;points"]
    assert any(x.label == "Years from the strike to the due date" and x.value == 6 for x in at.sidebar.slider)


def test_app_refinanced_rule_runs_and_lowers_stress():
    at = AppTest.from_file(APP, default_timeout=300).run()
    [x for x in at.sidebar.selectbox if x.label == "Repayment rule"][0].select("Lump sum refinanced at the market rate (B'-lump refinanced)").run()
    assert not at.exception
    nums, html = _nums(at)
    assert nums[:3] == ["23.1%", "16.3%", "&minus;6.9&#8239;points"] and "lowers financing-stress risk" in html
