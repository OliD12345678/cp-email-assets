"""Generate the blast + Work It email fragments for another Club Pilates studio.

Takes the approved Woodstock fragment as the base so the design stays byte-identical
apart from the studio-specific facts. Every substitution asserts, so a studio detail
can never be silently left as Woodstock's.

Usage: python build_studio.py <studio_key>
"""
import re, sys, pathlib

S = pathlib.Path(__file__).parent
BASE = S / "cp_woodstock_intro_cr.html"

STUDIOS = {
    "vinings": dict(
        brand="Club Pilates Vinings",
        masthead="VININGS, GEORGIA",
        footer_name="CLUB PILATES VININGS",
        slug="vinings",
        phone_display="(404) 882-4984",
        phone_e164="+14048824984",
        address="4687 South Atlanta Road SE &nbsp;·&nbsp; Atlanta, GA 30339",
        maps_q="4687+S+Atlanta+Rd+SE,+Atlanta,+GA+30339",
        email="vinings@clubpilates.com",
        instagram="https://www.instagram.com/clubpilatesvinings/",
        facebook="https://www.facebook.com/382621648263872",
        intro_times=[("WEDNESDAY","1:00 PM"),("THURSDAY","5:30 PM"),("SATURDAY","11:30 AM")],
    ),
    "mariettasouth": dict(
        brand="Club Pilates Marietta South",
        masthead="MARIETTA, GEORGIA",
        footer_name="CLUB PILATES MARIETTA SOUTH",
        slug="mariettasouthlafitness",
        phone_display="(404) 446-3662",
        phone_e164="+14044463662",
        address="1453 Terrell Mill Rd, Suite 145 &nbsp;·&nbsp; Marietta, GA 30067",
        maps_q="1453+Terrell+Mill+Rd+Ste+145,+Marietta,+GA+30067",
        email="mariettasouthlafitness@clubpilates.com",
        instagram="https://www.instagram.com/clubpilatesmariettasouthlaf/",
        facebook="https://www.facebook.com/110054641711922",
        intro_times=[("TUESDAY","5:30 PM"),("THURSDAY","1:00 PM"),("SATURDAY","1:00 PM")],
        # This studio sits inside an LA Fitness. Per Drew: you need an LA Fitness
        # membership to be a MEMBER here, but a guest pass covers the free Intro Class.
        # Say the part that affects the CTA, and don't scare anyone off the intro.
        extra_note=('<strong style="color:#1f2b4d;">We are inside LA Fitness.</strong> '
                    'You do not need an LA Fitness membership to take the free Intro Class. '
                    'We will set you up with a guest pass at the front desk, so just mention '
                    'it when you call and we will have it ready.'),
    ),
}

WD_TIMES = [("TUESDAY", "2:30 PM"), ("SATURDAY", "1:30 PM")]


def sub(h, old, new, expect=None):
    n = h.count(old)
    assert n and (expect is None or n == expect), f"expected {expect}, found {n}: {old[:70]}"
    return h.replace(old, new)


def build(cfg):
    h = BASE.read_text(encoding="utf-8")

    # Identity
    h = sub(h, "WOODSTOCK, GEORGIA", cfg["masthead"], 1)
    h = sub(h, "CLUB PILATES WOODSTOCK", cfg["footer_name"], 1)
    h = sub(h, "Club Pilates Woodstock", cfg["brand"])          # alts, panel, sign-off

    # Contact
    h = sub(h, "tel:+17704009557", "tel:" + cfg["phone_e164"], 5)
    h = sub(h, "sms:+17704009557", "sms:" + cfg["phone_e164"], 1)
    h = sub(h, "(770) 400-9557", cfg["phone_display"], 1)
    h = sub(h, "1428 Towne Lake Parkway, Suite 104 &nbsp;·&nbsp; Woodstock, GA 30189",
            cfg["address"], 1)
    h = sub(h, "https://maps.google.com/?q=1428+Towne+Lake+Pkwy+Ste+104,+Woodstock,+GA+30189",
            "https://maps.google.com/?q=" + cfg["maps_q"], 1)
    h = sub(h, "mailto:woodstock@clubpilates.com", "mailto:" + cfg["email"], 1)
    h = sub(h, "https://www.instagram.com/clubpilates_woodstock/", cfg["instagram"], 1)
    h = sub(h, "https://www.facebook.com/clubpilateswoodstock/", cfg["facebook"], 1)
    h = sub(h, "/location/woodstock", "/location/" + cfg["slug"])   # incl. /schedule

    # Class times. The card row is rebuilt from scratch so the layout flexes to
    # however many Intro Classes a studio actually runs.
    times = cfg["intro_times"]
    assert times and 2 <= len(times) <= 4, "2-4 intro times supported"
    n = len(times)
    colw = round((100 - 2 * (n - 1)) / n)
    tel = "tel:" + cfg["phone_e164"]
    cells = []
    for day, tm in times:
        cells.append(
            f'<td width="{colw}%" bgcolor="#fdfcfa" align="center" style="padding:16px 8px; '
            "font-family:Georgia,'Times New Roman',serif;\">\n"
            '                <p style="margin:0; font-size:11px; line-height:15px; '
            f'letter-spacing:2.5px; color:#6b665f;">{day}</p>\n'
            '                <table role="presentation" cellpadding="0" cellspacing="0" border="0" '
            'width="100%" style="border-collapse:collapse;"><tbody><tr><td height="6" '
            'style="height:6px; line-height:6px; font-size:0;">&nbsp;</td></tr></tbody></table>\n'
            '                <p style="margin:0; font-size:22px; line-height:28px; color:#2c6494;">'
            f'<a href="{tel}" style="color:#2c6494; text-decoration:none;">{tm}</a></p>\n'
            "              </td>")
    gap = '<td width="2%" style="font-size:0; line-height:0;">&nbsp;</td>'
    row = ("\n              " + f"\n              {gap}\n              ".join(cells) + "\n")

    # The cards contain nested spacer <table>s, so find the outer table's real end
    # by walking the tag stack rather than with a non-greedy regex.
    open_tag = ('<table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" '
                'style="border-collapse:collapse; max-width:420px;"><tbody>')
    assert h.count(open_tag) == 1, "time-card table not found"
    start = h.index(open_tag)
    depth, k = 0, start
    for m in re.finditer(r"<table\b|</table>", h[start:]):
        depth += 1 if m.group(0).startswith("<table") else -1
        if depth == 0:
            k = start + m.end()
            break
    assert depth == 0 and k > start, "unbalanced time-card table"
    h = h[:start] + open_tag + "\n            <tr>" + row + "            </tr>\n          </tbody></table>" + h[k:]

    # "Two Intro Classes a week" has to agree with the card count
    words = {2: "Two", 3: "Three", 4: "Four"}
    h = sub(h, "Two Intro Classes a week", f"{words[n]} Intro Classes a week", 1)

    # The line under the top CTA. Abbreviate days once there are more than two.
    cap_old = ("Thirty minutes, no charge &nbsp;·&nbsp; Tuesday 2:30 PM "
               "&nbsp;·&nbsp; Saturday 1:30 PM")
    fmt = (lambda d: d.title()) if n == 2 else (lambda d: d.title()[:3])
    cap_new = "Thirty minutes, no charge &nbsp;·&nbsp; " + " &nbsp;·&nbsp; ".join(
        f"{fmt(d)} {t}" for d, t in times)
    h = sub(h, cap_old, cap_new, 1)

    # Optional studio-specific practical note, added to the "what to expect" list
    if cfg.get("extra_note"):
        anchor = ("Nobody is keeping pace with anybody.</p>")
        assert anchor in h
        spacer16 = ('<table role="presentation" cellpadding="0" cellspacing="0" border="0" '
                    'width="100%" style="border-collapse:collapse;"><tbody><tr><td height="16" '
                    'style="height:16px; line-height:16px; font-size:0;">&nbsp;</td></tr></tbody></table>')
        note = ('\n      ' + spacer16 + '\n      <p style="margin:0; font-size:17px; '
                'line-height:29px; color:#33312e; mso-line-height-rule:exactly;">'
                + cfg["extra_note"] + '</p>')
        h = h.replace(anchor, anchor + note, 1)

    for leftover in ["Woodstock", "7704009557", "Towne Lake", "2:30 PM", "1:30 PM"]:
        assert leftover not in h, "leftover Woodstock detail: " + leftover

    # Work It twin: a [content] paragraph under the greeting
    greet = ('<p style="margin:0; font-size:17px; line-height:29px; color:#33312e; '
             'mso-line-height-rule:exactly;">Hi [firstname],</p>')
    i = h.index(greet) + len(greet)
    m = re.compile(r'\s*<table[^>]*><tbody><tr><td height="16"[^>]*>.*?</td></tr></tbody></table>',
                   re.S).match(h, i)
    assert m
    spacer = ('<table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" '
              'style="border-collapse:collapse;"><tbody><tr><td height="16" '
              'style="height:16px; line-height:16px; font-size:0;">&nbsp;</td></tr></tbody></table>')
    block = ('\n      <p style="margin:0; font-size:17px; line-height:29px; color:#33312e; '
             'mso-line-height-rule:exactly;">[content]</p>\n      ' + spacer)
    return h, h[:m.end()] + block + h[m.end():]


if __name__ == "__main__":
    key = sys.argv[1]
    blast, workit = build(STUDIOS[key])
    (S / f"cp_{key}_blast.html").write_text(blast, encoding="utf-8")
    (S / f"cp_{key}_workit.html").write_text(workit, encoding="utf-8")
    for n, d in (("blast", blast), ("workit", workit)):
        print(f"{key}/{n}: {len(d)}B imgs={d.count('<img')} tel={d.count('tel:')} "
              f"em={d.count(chr(8212))} content={d.count('[content]')} divs={d.count('<div')}")
