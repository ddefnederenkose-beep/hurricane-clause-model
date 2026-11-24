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


def test_app_defaults_are_bprime_lump_and_instalments_reproduce_the_brief():
    at = AppTest.from_file(APP, default_timeout=300).run()
    assert not at.exception
    nums, html = _nums(at)
    assert nums[:6] == ["23.1%", "52.3%", "+29.2&#8239;points", "38.5%", "52.6%", "+14.1&#8239;points"]   # B'-lump is the baseline
    assert "Financing-stress episode" in html and html.count("attributable") == 1 and "formerly 'hurricane-attributable crisis'" in html
    assert "makes things worse" in html
    assert "Work in progress" not in html and "yet" not in html.split("Parameter entries")[1].split("</p>")[0]
    assert "Parameter entries: 15 sourced, 16 calibrated, 23 assumed" in html
    assert "Change the parameters in the sidebar" in html and "95% CI" not in html and "CI" not in re.sub(r"[^A-Za-z ]", "", html.split("Definitions")[0]).split()
    assert any(x.label == "Years from the strike to the due date" and x.value == 6 for x in at.sidebar.slider)
    [x for x in at.sidebar.selectbox if x.label == "Repayment rule"][0].select("Equal instalments over the repayment period (5-year case)").run()
    assert not at.exception
    nums, html = _nums(at)
    assert nums[:6] == ["23.1%", "24.7%", "+1.6&#8239;points", "38.5%", "25.7%", "&minus;12.8&#8239;points"]
    assert "The verdict flips" in html


def test_app_refinanced_rule_runs_and_lowers_stress():
    at = AppTest.from_file(APP, default_timeout=300).run()
    [x for x in at.sidebar.selectbox if x.label == "Repayment rule"][0].select("Lump sum refinanced at the market rate (B'-lump refinanced)").run()
    assert not at.exception
    nums, html = _nums(at)
    assert nums[:3] == ["23.1%", "16.3%", "&minus;6.9&#8239;points"] and "makes things better" in html


def test_switching_rules_back_and_forth_keeps_sensible_slider_defaults():
    at = AppTest.from_file(APP, default_timeout=300).run()
    box = lambda: [x for x in at.sidebar.selectbox if x.label == "Repayment rule"][0]
    box().select("Equal instalments over the repayment period (5-year case)").run()
    assert not at.exception and any(x.label.startswith("Repayment period") and x.value == 5 for x in at.sidebar.slider)
    box().select("Grenada's actual: one lump sum at strike year + 6 (B'-lump, baseline)").run()
    assert not at.exception and any(x.label == "Years from the strike to the due date" and x.value == 6 for x in at.sidebar.slider)
    assert _nums(at)[0][:3] == ["23.1%", "52.3%", "+29.2&#8239;points"]
