import re, pathlib

S = pathlib.Path(r"C:\Users\pursu\AppData\Local\Temp\claude\C--Users-pursu-Downloads-open-design-main\72f949d9-204d-412a-8d84-a1ab6c98ffe6\scratchpad")
src = (S / "cp_email" / "Club-Pilates-Woodstock-Intro-Class.html").read_text(encoding="utf-8")

# 1. Body fragment only: strip doctype/html/head/style/body wrappers
h = src.split("<body", 1)[1].split(">", 1)[1]
h = h.rsplit("</body>", 1)[0].strip()

BASE = "https://img.alpharetta.fit/img/"

# 2. Hosted https image URLs
h = h.replace('src="uploads/clubpilates-logo-5a6ce194.png"', f'src="{BASE}cp-logo-navy-v1.png"')
h = h.replace('src="uploads/2_taller.jpg"',                   f'src="{BASE}cp-wds-intro-hero-v1.jpg"')
h = h.replace('src="uploads/_H2A8659.jpg"',                   f'src="{BASE}cp-wds-intro-studio-v1.jpg"')
assert "uploads/" not in h

# 3. Real ClubReady merge tags. [viewinbrowser]/[unsubscribe] render as COMPLETE links,
#    so they must stand alone -- never inside an href.
h = h.replace(
    '<a href="{{WebVersionURL}}" style="color:#7c7770; text-decoration:underline;">View this in your browser</a>',
    '[viewinbrowser]')
h = h.replace(
    '<a href="{{UpdatePreferencesURL}}" style="color:#9a958e; text-decoration:underline;">Update preferences</a> &nbsp;|&nbsp;\n        <a href="{{UnsubscribeURL}}" style="color:#9a958e; text-decoration:underline;">Unsubscribe</a>',
    '[unsubscribe]')
assert "{{" not in h
assert "[unsubscribe]" in h and "[viewinbrowser]" in h

# 4. Fix line-heights smaller than their font-size (headings overlapped when they wrapped)
for bad, good in [
    ("font-size:37px; line-height:34px", "font-size:37px; line-height:44px"),
    ("font-size:39px; line-height:34px", "font-size:39px; line-height:46px"),
    ("font-size:23px; line-height:15px", "font-size:23px; line-height:26px"),
]:
    assert bad in h, bad
    h = h.replace(bad, good)

# --- Drew's copy edits (2026-08-15) ------------------------------------------
BOOK = "https://www.clubpilates.com/location/woodstock"
TEL  = "tel:+17704009557"

# 4a. Every "book online" CTA becomes call-to-book: the two buttons and the two
#     clickable class times. The schedule link at the bottom stays informational.
n_book = h.count(f'href="{BOOK}"')
assert n_book == 4, n_book
h = h.replace(f'href="{BOOK}"', f'href="{TEL}"')
for bad, good in [(">BOOK MY FREE INTRO CLASS<", ">CALL US TO BOOK<"),
                  (">RESERVE MY SPOT<",          ">CALL TO RESERVE<")]:
    assert bad in h, bad
    h = h.replace(bad, good)
assert f'href="{BOOK}/schedule"' in h, "schedule link should survive"

# 4b. Drop the "One honest note" caveat paragraph and the spacer above it,
#     so the preceding paragraph keeps its original gap to the next section.
caveat = re.compile(
    r'\s*<div style="height:16px; line-height:16px; font-size:0;">&nbsp;</div>'
    r'\s*<p class="body"[^>]*>One honest note.*?</p>', re.S)
assert len(caveat.findall(h)) == 1
h = caveat.sub("", h)
assert "One honest note" not in h

# 4b-ii. Calling is the preferred route, so the navy panel's whole secondary block
#        (headline, explainer, and the Call/Text button pair) collapses to one small,
#        muted "or text us" link sitting just under the CALL TO RESERVE button.
#        Two options remain, but the visual weight now clearly favours calling.
region = re.compile(
    r'<div style="height:30px; line-height:30px; font-size:0;">&nbsp;</div>\s*'
    r'<div style="font-size:19px[^>]*>Or simply call or text us\.</div>.*?'
    r'<a href="sms:\+17704009557".*?</table>', re.S)
assert len(region.findall(h)) == 1
h = region.sub(
    '<div style="height:14px; line-height:14px; font-size:0;">&nbsp;</div>\n'
    '          <div style="font-size:13px; line-height:20px; mso-line-height-rule:exactly;">'
    '<a href="sms:+17704009557" style="color:#9db4d4; text-decoration:underline;">or text us</a></div>',
    h)
for gone in ["Or simply call or text us", "If you'd rather ask a question first",
             "Call (770) 400-9557</a>"]:
    assert gone not in h, gone
assert h.count('href="sms:+17704009557"') == 1

# 4c. No em dashes. Rewritten per sentence rather than swapped one-for-one.
EM_EDITS = [
    ("no charge &mdash; and three things", "no charge, and three things"),
    ("no charge — and three things",       "no charge, and three things"),
    ("genuinely worth reading — and an open invitation",
     "genuinely worth reading, and an open invitation"),
    ("gets you in the door — it's what you leave with.",
     "gets you in the door. It's what you leave with."),
    ("on a sit-and-reach test</strong> — about three inches.",
     "on a sit-and-reach test</strong>, about three inches."),
    ("Functional reach — how far you can lean before you have to step — improved",
     "Functional reach, how far you can lean before you have to step, improved"),
    ("leg strength test</strong> — around ten pounds — without a single barbell",
     "leg strength test</strong>, around ten pounds, without a single barbell"),
    ("do tell your instructor — we will adjust for it.",
     "do tell your instructor. We will adjust for it."),
    ("&mdash; The team at", "The team at"),
    ("— The team at",       "The team at"),
]
for bad, good in EM_EDITS:
    if bad in h:
        h = h.replace(bad, good)
assert "—" not in h and "&mdash;" not in h, "em dash survived: " + repr(
    [h[max(0,i-60):i+60] for i in range(len(h)) if h[i] == "—"][:2])

# 5. Drop all classes -- CR strips <style>, so class-based rules are dead weight
h = re.sub(r'\s+class="[^"]*"', "", h)
assert "class=" not in h

# --- Survive ClubReady's Redactor editor -------------------------------------
# Redactor rewrites every <div> to <p> (adding default client margins) and strips
# &nbsp;/&zwnj; to plain whitespace. So do both transforms ourselves, defensively.

# 5a. Spacer divs -> real table spacer rows. The height="" ATTRIBUTE holds the box
#     open in Outlook even after the &nbsp; is stripped; a bare <p> would not.
SPACER = re.compile(r'<div style="height:(\d+)px; line-height:\d+px; font-size:0;">&nbsp;</div>')
n_spacers = len(SPACER.findall(h))
h = SPACER.sub(
    lambda m: ('<table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" '
               'style="border-collapse:collapse;"><tbody><tr>'
               f'<td height="{m.group(1)}" style="height:{m.group(1)}px; line-height:{m.group(1)}px; font-size:0;">&nbsp;</td>'
               '</tr></tbody></table>'), h)

# 5b. Every remaining div -> <p> with an explicit margin:0 so Redactor's conversion
#     is a no-op instead of injecting ~1em of client default margin.
n_divs = len(re.findall(r"<div ", h))
h = re.sub(r'<div style="', '<p style="margin:0; ', h)
h = h.replace("</div>", "</p>")
assert "<div" not in h and "</div>" not in h

# 6. Inline what the stripped global <style> used to provide
h = re.sub(r"<table(?![^>]*border-collapse)([^>]*?)style=\"", r'<table\1style="border-collapse:collapse; ', h)
h = h.replace('<table role="presentation" cellpadding="0" cellspacing="0" border="0">',
              '<table role="presentation" cellpadding="0" cellspacing="0" border="0" style="border-collapse:collapse;">')
h = h.replace("<img ", '<img border="0" ')

# 7. Explicit <tbody> on every table (skip the spacer tables, already built with one)
h = re.sub(r"(<table[^>]*>)(?!<tbody>)", r"\1<tbody>", h)
h = re.sub(r"(?<!</tbody>)</table>", "</tbody></table>", h)
assert h.count("<tbody>") == h.count("</tbody>") == h.count("<table"), "tbody mismatch"

# 8. Every <p> must carry margin:0 -- that is the whole point of 5b
p_tags = re.findall(r"<p\b[^>]*>", h)
missing = [t for t in p_tags if "margin:0" not in t]
assert not missing, f"{len(missing)} <p> without margin:0, e.g. {missing[:2]}"
n_p = len(p_tags)

out = S / "cp_woodstock_intro_cr.html"
out.write_text(h, encoding="utf-8")
print(f"bytes:{len(h)} tables:{h.count('<table')} imgs:{h.count('<img')} "
      f"spacers:{n_spacers} divs_converted:{n_divs} p:{n_p} (all margin:0)")
print("tags:", sorted(set(re.findall(r"\[[a-z]+\]", h))))
