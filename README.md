# The American Century

A cinematic history in four acts, 1898 to 1969. Every slide lives on one continuous 3D timeline, and a camera travels through time as you advance.

This is a static website: plain HTML, CSS and JavaScript with no build step and no dependencies. Fonts load from Google Fonts.

## Deploy on Vercel

1. Push this folder to a GitHub repository (the contents of this folder go at the root of the repo).
2. In Vercel, choose **Add New → Project** and import the repository.
3. Set **Framework Preset** to **Other**. Leave **Build Command** empty and **Output Directory** as the default (the repo root).
4. Click **Deploy**. Every push to the main branch redeploys automatically.

## Presenting

| Action | Keys |
| --- | --- |
| Next | → , space, scroll down, swipe left, or click the right side |
| Back | ← , scroll up, swipe right, or click the left side |
| Full screen | F |
| Speaker notes | N |
| Notes in a second window | P |
| First or last slide | Home or End |
| Black screen | B or . |
| All keys | ? |

Each slide has its own address (for example `/#pearl-harbor`), so you can link straight to a moment.

## Preview locally

```
python3 -m http.server 8000
```

Then open http://localhost:8000.

## Editing

`index.html` is generated. To change content, edit the files in `source/` and rebuild:

- `source/deck/slides/*.html`: the slide content, one file per slide, with speaker notes in each slide's `<aside>`.
- `source/deck/deck.json`: slide order.
- `source/engine.html`: the timeline world, camera, controls and styles.
- `source/american-century.proto.html`: the six opening slides built for the timeline.

```
python3 source/build.py
```

Maps live in `assets/` and load only as their slides approach.
