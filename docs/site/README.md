# Aura GitHub Pages site

Static landing page for project Aura. Plain HTML + CSS, no Jekyll, no build step.

Live (target): https://ShAuRyA-Noodle.github.io/aura-on-device
Live (current Pages config): https://shaurya-noodle.github.io/aura-on-device/docs/site/

> Note: the GitHub Pages REST API only accepts `/` or `/docs` as a source
> path; `/docs/site` is rejected with HTTP 422. Pages was therefore enabled
> with `source.branch=main, source.path=/docs`, and the site is served from
> `/aura/docs/site/` underneath that. To get the bare-root URL to serve the
> landing page, do **one** of the following manual steps:
>
> 1. In the GitHub UI at
>    `https://github.com/ShAuRyA-Noodle/aura-on-device/settings/pages`,
>    switch the source to "GitHub Actions" and add a workflow that uploads
>    `aura/docs/site/` as the Pages artifact (recommended).
> 2. Or copy / symlink the contents of `aura/docs/site/` to repo root
>    `docs/` and re-run
>    `gh api -X PUT /repos/ShAuRyA-Noodle/aura-on-device/pages -f build_type=legacy -F 'source[branch]=main' -F 'source[path]=/docs'`.

## Files

```
index.html        single-page landing site, 10 bento tiles
style.css         locked palette + type scale, CSS Grid, mobile responsive
404.html          minimal not-found page in the same style
robots.txt        allow all
_config.yml       Pages defaults (theme:null, no plugins)
.nojekyll         bypass Jekyll processing on Pages
assets/
  aura_logo.svg   copied from aura/design/brand/aura_logo.svg
```

## External dependencies

- The architecture diagram embeds `../architecture/aura_architecture.svg`. If
  that file is missing the page falls back to a captioned placeholder and the
  rest of the page still renders.
- Google Fonts: Fraunces, Inter Tight, JetBrains Mono.

## Preview locally

```
cd aura/docs/site
python -m http.server 8000
# open http://localhost:8000
```

## Deploy

The repo is configured to serve Pages from `main` branch, `/docs/site` path.

```
git add aura/docs/site
git commit -m "site: ship landing page"
git push origin main

# one-time enable (already run):
gh repo edit ShAuRyA-Noodle/aura-on-device --enable-pages
gh api -X PATCH /repos/ShAuRyA-Noodle/aura-on-device/pages \
  -f source.branch=main -f source.path=/docs/site
```

If `gh api` rejects the path setting, set it manually at
`https://github.com/ShAuRyA-Noodle/aura-on-device/settings/pages`:
Source = "Deploy from a branch", Branch = `main`, Folder = `/docs/site`.

## Constraints honoured

- No frameworks, no Tailwind, no JS bundle.
- Locked palette: `#FAF8F5` background, `#0E0E0E` ink, `#FF5B2E` accent.
- Locked type: Fraunces (display), Inter Tight (body), JetBrains Mono (code).
- Page weight under 300 KB including fonts.
- Semantic HTML5, alt text on every image, keyboard navigable, WCAG AAA on body
  text contrast (`#0E0E0E` on `#FAF8F5` ≈ 18.7:1).
