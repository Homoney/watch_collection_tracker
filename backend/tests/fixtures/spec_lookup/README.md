Saved responses for the reference look-up tests (no live calls in CI).

- `wb_*.json`: WatchBase Data Feed API answers in its JSON format, shaped
  like the examples in https://watchbase.com/manuals/datafeed (search/refnr
  and watch). Values for 126610LN and SBGE201 follow the research notes
  (126610LN has no case height; SBGE201 has no lug width).
- `cc_sitemap*.xml`: a few `<loc>` lines in Caliber Corner's post-sitemap
  format.
- `cc_rolex_3235.html`: Caliber Corner's caliber spec table (facts only,
  same markup as the live page), wrapped in a minimal page.
- `wb_photo_*.png`: stand-in images for WatchBase's photo server (a drawn
  placeholder, not a real WatchBase photo); `wb_photo_small.png` is below the
  200 px minimum.
- `site_*`: WatchBase's public site, saved on 2026-11-18 with the app's
  User-Agent: `/filter/results?q=` answers for 126610LN (one watch), 5711/1A
  (five) and an unknown reference (none), and the `<head>` of the 126610LN
  watch page (its `og:image` tag; the body is trimmed).
- `wb_live_*.json`: real WatchBase Data Feed API answers recorded on
  2026-11-18 with David's key (2 Watch calls, 3 searches): search/refnr for
  126610LN, SBGE201 and an unknown reference, and the Watch answers for ids
  42294 (126610LN-0001) and 31034 (SBGE201). Long `description` texts are
  trimmed; the key is not in them. The hand-made `wb_*.json` files above are
  kept for the error and choice cases.
- `cc_live_sitemap*.xml`: Caliber Corner's real sitemap format (saved
  2026-11-18), cut to a few `<url>` entries: each URL is wrapped in
  `<![CDATA[...]]>` and entries carry `<image:loc>` photo URLs, which the
  index must skip. `cc_sitemap*.xml` are the older plain-`<loc>` form.
- `wb_search_126610L_two.json`: the live search answer for 126610LN with a
  second (made-up) 126610LV entry added, for the choice-then-pick test.
