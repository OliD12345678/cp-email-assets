# Club Pilates "Three things worth knowing" intro-class email

`base_woodstock_approved.html` is the approved Woodstock body fragment (ClubReady-ready:
body fragment only, all CSS inline, no `<div>`, spacer cells carry a `height` attribute).

`build_studio.py <vinings|mariettasouth>` regenerates another studio's pair from that base.
Every studio-specific substitution asserts, so a leftover Woodstock phone number or class time
fails the build instead of shipping. The intro-time card row is rebuilt from scratch, so 2-4
classes are supported and the cards, the "N Intro Classes a week" line, and the caption under
the top CTA always agree.

`build_fragment_woodstock.py` rebuilds the Woodstock base itself from the original design export.

Load into ClubReady with `saveit(1)` (NOT the Editor tab's Save, which mangles the markup):
    document.getElementById('mailbody').value = html; setTimeout(()=>saveit(1),150);

Two templates per studio: a clean one for blasts, and a `[content]` copy for Work It 1:1 sends.
A template only appears in Work It if it contains `[content]`; it only appears in the blast
picker if EmailBlastOk is checked AND `[unsubscribe]` is present.
