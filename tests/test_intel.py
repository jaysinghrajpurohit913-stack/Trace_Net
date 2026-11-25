import pandas as pd
from tracenet.intel.analyse import domain_flags, ip_table
from tracenet.intel import lookup
from tracenet.intel.model import tidy_domains
from tracenet.intel.requests import drafts_for


def test_shared_ip_and_ns_flagged(an):
    f = an.flags.set_index("domain")
    assert any("share IP" in x for x in f.loc["secure-kyc-update.example", "flags"])
    assert any("name server" in x for x in f.loc["upi-refund-claim.example", "flags"])


def test_cdn_ip_is_weak_not_strong(an):
    p = an.dlinks
    cdn = p[(p.value == "192.0.2.99")]
    assert len(cdn) and (cdn.strength == "weak").all()


def test_vpn_ip_never_a_strong_link(an):
    vpn = an.dlinks[an.dlinks.value == "203.0.113.77"]
    assert (vpn.strength == "weak").all()


def test_infrastructure_links_complaints_without_shared_money(an):
    pair = an.dpairs[(an.dpairs.a == "NCRP-10") & (an.dpairs.b == "NCRP-40")]
    assert len(pair) == 1 and pair.iloc[0].strong >= 1


def test_ip_log_matches_transactions_after_utc_conversion(an):
    assert (an.corr["class"] == "same moment").sum() >= 3
    assert (an.corr["class"] == "far").sum() >= 1
    assert an.corr[an.corr.ip == "203.0.113.77"].caveat.str.contains("accounts").any()


def test_provider_letters_have_both_clocks(an):
    d = drafts_for(an.intel, an.intel.ips, an.corr)
    assert {"registrar", "hosting", "isp"} <= {x["kind"] for x in d}
    isp = next(x for x in d if x["kind"] == "isp")["text"]
    assert "IST" in isp and "UTC" in isp and "legal" in isp.lower()


# ---------------- passive lookups with a fake network
def fake(url):
    if "rdap.org/domain" in url:
        return {"events": [{"eventAction": "registration", "eventDate": "2026-09-20T00:00:00Z"}, {"eventAction": "expiration", "eventDate": "2026-12-20T00:00:00Z"}],
                "entities": [{"roles": ["registrar"], "vcardArray": ["vcard", [["fn", {}, "text", "Fake Registrar"]]]}], "nameservers": [{"ldhName": "NS1.FAKE.TEST"}]}
    if "crt.sh" in url:
        return [{"name_value": "a.fake.test\n*.fake.test", "issuer_name": "Test CA", "not_before": "2026-09-21T00:00:00"}]
    if "dns.google" in url:
        return {"Answer": [{"type": 1, "data": "8.8.4.4"}]}
    raise AssertionError(url)


def test_enrich_fills_blanks_and_logs_every_call(tmp_path):
    d = tidy_domains(pd.DataFrame([{"domain": "fake.test"}]))
    out, ips, certs, log = lookup.enrich_domains(d, fetch=fake, cache_dir=tmp_path)
    assert out.registrar[0] == "Fake Registrar" and out.ip[0] == "8.8.4.4" and "fake.test" in set(certs.domain)
    assert len(log.frame()) >= 3 and log.frame().ok.all()


def test_offline_is_survivable(tmp_path):
    def down(url): raise OSError("no network")
    d = tidy_domains(pd.DataFrame([{"domain": "fake.test", "registrar": "Imported"}]))
    out, ips, certs, log = lookup.enrich_domains(d, fetch=down, cache_dir=tmp_path)
    assert out.registrar[0] == "Imported" and not log.frame().ok.any()


def test_private_and_documentation_ips_are_never_sent():
    calls = []
    lookup.asn_of("203.0.113.5", fetch=lambda u: calls.append(u), cache=None)
    lookup.rdap_ip("10.0.0.1", fetch=lambda u: calls.append(u), cache=None)
    assert calls == []
