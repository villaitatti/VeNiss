# IIIF server migration: Digilib → Cantaloupe (minimal repoint)

## Why
Digilib 2.9.1 has no TIFF reader and decodes whole images into RAM (the cause of
TIFFs not rendering and large images failing). Cantaloupe is the upstream RS 4.0
default IIIF server and natively handles TIFF/BigTIFF/pyramidal + large images.

This is a **minimal repoint**: all `/proxy/IIIF/{id}/...` frontend URLs stay the same;
only the proxy *target* changes from Digilib to Cantaloupe. No template churn, no Java build.

## What's in this folder
- `cantaloupe.properties` — Cantaloupe 5.x config (FilesystemSource, TIFF, cache).
- `docker-compose.snippet.yml` — the `cantaloupe` service to add to the prod compose.

The repo-side proxy override already lives (commented) in `apps/VeNiss/config/proxy.prop`.

## Activation runbook (coordinated — do in order)
1. **Stand up Cantaloupe.** Add the `cantaloupe` service to the prod docker-compose on
   the SAME network as the RS platform, mounting the SAME images dir Digilib used
   (`runtime-data/images/file` → `/imageroot:ro`) and `cantaloupe.properties`. Pin a real
   Cantaloupe 5.x image and confirm its config path/env var.
2. **Verify Cantaloupe directly** (from inside the network), e.g.:
   - `curl http://cantaloupe:8182/iiif/2/<a-known-file.jpg>/info.json`
   - `curl -o /tmp/t.jpg http://cantaloupe:8182/iiif/2/<a-known-file.tif>/full/!640,480/0/default.jpg`
3. **Activate the proxy override:** uncomment the two `config.proxy.IIIF.*` lines in
   `apps/VeNiss/config/proxy.prop`, then commit → push → server `git pull` → RS reload.
4. **Verify through the platform:**
   - `https://veniss.net/proxy/IIIF/<known-jpg>/full/!640,480/0/default.jpg` (regression)
   - `https://veniss.net/proxy/IIIF/<known-tif>/full/!640,480/0/default.jpg` (TIFF now serves)
   - Open an entity's image Preview modal — no "Invalid image ID"; hero + "More images".
5. **Decommission Digilib** once stable.

## Rollback
Re-comment the two `config.proxy.IIIF.*` lines in `config/proxy.prop` and reload — the
platform falls back to the baked-in Digilib default.

## Notes
- IIIF `{id}` = the bare filename in `rso:PX_has_file_name` (flat layout, no slashes).
  Filenames with spaces are percent-encoded in the URL; Cantaloupe decodes them.
- TIFFs only serve once their record resolves a literal filename — see the image-model
  data audit (`apps/VeNiss/audit/2026-06-15/AUDIT_IMAGE_MODELS.md`).
- The form upload handler (`FileUploadHandler`) renames uploads to `.jpg` without
  transcoding; a future server-side fix should transcode TIFF→JPEG on ingest. Low
  priority now since Cantaloupe serves real TIFFs directly.
