# NASA Space Apps 2026 — Solquira Next Station — submission copy

**Submission deadline:** 15 November 2026, 11:59 PM local event time. Confirm in the NASA Space Apps submission form before submitting.  
**Selected challenge:** Field Shift: Adapting Farms with NASA Data  
**Team:** R4Logic  
**Project name:** Solquira — Next Station

## Project Summary (English; 50–200 words, under 1500 characters)

Farmers face different water challenges: prolonged dry periods in semi-arid landscapes, and excess rainfall and restricted field access in humid regions. Solquira — Next Station extends the open-source Solquira geospatial platform to help growers, advisers, and communities explore these contrasting conditions before planning a new season.

Users select and confirm a location, inspect historical NASA POWER precipitation and temperature data, and compare complete growing-season windows. They can then add their own knowledge of soil texture and drainage, or activate clearly labelled hypothetical demonstration profiles. Transparent, deterministic indicators compare four illustrative crop-rotation pathways and highlight questions to verify in the field.

Using Chile's Coquimbo, Maule, and Chiloé as starting examples, the application demonstrates a workflow applicable across wider regions. It distinguishes historical environmental evidence from forecasts, separates assumptions from observations, and never claims to certify agronomic suitability. Next Station turns NASA data into an accessible starting point for informed seasonal adaptation.

## Project Details (English)

**Problem.** A single prescribed crop-rotation pattern cannot address both drought and high-rainfall conditions. Decisions depend on the land, season, soil characteristics, local constraints, and a grower's priorities. Weather-grid datasets are powerful, but difficult for non-specialists to interpret responsibly.

**Solution.** Solquira — Next Station adapts an existing, openly developed geospatial Studio to the Field Shift challenge. It retains the complete Territory, Anticipation, Guidance, and Evidence workspaces rather than creating a minimal replacement. Users may select any valid coordinates in a CesiumJS 3D/2D geographic interface, review the marker, and explicitly confirm the point. The Field Shift module queries NASA POWER's daily AG dataset for precipitation (PRECTOTCORR) and 2-m air temperature (T2M) between 2021 and 2025. It summarizes April–September and October–March seasonal windows, discards incomplete seasons, and refuses to invent missing observations.

**From NASA evidence to comparisons.** The interface presents seasonal precipitation totals, frequencies of days with less than 1 mm of rain, and days receiving at least 20 mm. These signals feed deterministic comparison rules for four illustrative rotation pathways: continue a cereal baseline, diversify with legumes, use living cover, or integrate forage. The 0–100 indices are explanatory comparisons; they are not event probabilities, yield forecasts, or validated agronomic prescriptions. Unknown drainage does not receive a fabricated intermediate value. Historical NASA POWER grid-point estimates are not on-site measurements.

**Field knowledge and inclusion.** Farmers may report soil texture and drainage or leave them unknown. Optional demonstration profiles allow visitors to see how assumptions affect the comparison, but the response explicitly records their hypothetical provenance. The Studio supports Spanish and English, accessible presentations, light/dark modes, and mobile interaction. The Chilean demonstration places—Coquimbo (dryland), Maule (seasonal transition), and Chiloé (rainfall/excess-water context)—illustrate a method transferable internationally.

**Engineering.** React, TypeScript, Vite, CesiumJS, Python, Pydantic, deterministic hydrometeorological rules, NASA POWER Daily Point AG API, NASA GIBS for imagery in the wider Studio, OpenStreetMap mapping resources, Vercel serverless execution, and an existing FastAPI Studio backend. User authorization uses opaque sessions, CSRF and bounded admission. Field Shift runs in a separate Vercel function and reuses existing Studio authentication without changing the original Solquira application or its Akamai server.

**Outcome and limits.** This is a working, open-source decision-support prototype: it clarifies past climate variability, makes assumptions visible, and guides what a user should investigate next. It does not claim validated crop suitability, predict future seasonal weather, or replace soil testing and local agronomic advice. Further validation would require local soil and crop evidence, independent field trials, and farmer feedback.

## Public project link (Project*)

https://solquira-next-station.vercel.app

Additional open repository:
https://github.com/Shinken009/solquira-next-station

## Project demonstration link (Project Demonstration*)

**TO COMPLETE:** paste the final published YouTube video link after checking (a) duration <=30.0 s in the exported master, (b) visibility unrestricted in a private browsing window, (c) on-screen watermark of AI-generated footage, (d) audio and code AI disclosures in description/metadata, (e) legitimate real-product captures. Do not paste a protected Magnific editor or Vercel preview link as the required public demonstration.

## NASA Data (*)

- NASA POWER Prediction Of Worldwide Energy Resources — Daily Point API (AG), 2 m temperature T2M and precipitation PRECTOTCORR, UTC: https://power.larc.nasa.gov/docs/services/api/temporal/daily/
- NASA Earthdata Global Imagery Browse Services (GIBS) — spatial imagery layers used within the existing geospatial Studio: https://gibs.earthdata.nasa.gov/
- NASA GIBS API and attribution: https://nasa-gibs.github.io/gibs-api-docs/

NASA imagery acknowledgment: *We acknowledge the use of imagery provided by services from NASA's Global Imagery Browse Services (GIBS), part of NASA's Earth Science Data and Information System (ESDIS).*

## Space Agency Partner and Other Data / Tools

- Original Solquira platform and source: https://github.com/Shinken009/solquira
- CesiumJS interactive 3D and 2D globe: https://cesium.com/platform/cesiumjs/
- OpenStreetMap maps and contributors, with attribution: https://www.openstreetmap.org/copyright
- React: https://react.dev/
- TypeScript: https://www.typescriptlang.org/
- Vite: https://vite.dev/
- Python: https://www.python.org/
- Pydantic: https://docs.pydantic.dev/
- FastAPI: https://fastapi.tiangolo.com/
- Vercel hosting/functions: https://vercel.com/
- Magnific creative/video tooling: https://www.magnific.com/
- OpenAI ChatGPT and Codex for code, scientific-copy and testing assistance: https://openai.com/

List any further assets, fonts, third-party music, datasets or libraries actually used in the final video/app before submitting. Do not imply a dataset directly drives the rotation calculation unless it really does.

## Use of Super Intelligence (SI*)

Generated code and text: Generative AI assistants (OpenAI ChatGPT/Codex, and Google Antigravity if applicable during development) assisted with code drafting, localization, testing and review; the human creator remained responsible for engineering choices, data interpretation and final validation. Source code and this README describe these contributions. NASA POWER readings themselves were queried from NASA and were never artificially generated.

Generated video: Magnific (including AI-generated environmental footage and AI-assisted editing/motion) was used only where identified. Every frame of generated footage must include a clear visible watermark reading **AI-GENERATED FOOTAGE**. Authentic screen captures represent the working application and are not reconstructed with generative AI.

Generated audio: Any AI-synthesized narration or soundtrack should be declared in the YouTube description, production metadata and/or source credits. Generated soundtrack and voice are not NASA recordings.

Do **not** add a generated NASA logo, flag, mission identifier, or design element to the video or website.

## Publish checklist

- [ ] Project summary, details and name checked in English.
- [ ] Independent anonymous browser can access the web app without a password, approval or registration.
- [ ] Main product demo runs with real NASA POWER historical evidence.
- [ ] Demo video duration **strictly <= 30 seconds**; all AI-generated footage visibly watermarked.
- [ ] Video audio/description explicitly identifies AI usage.
- [ ] Final YouTube link works in incognito without password, request for permission, or account sign-in.
- [ ] All NASA source and third-party tool links listed and verified.
- [ ] Submit in the NASA Space Apps interface before the local deadline.
