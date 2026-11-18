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
