# Icon proposals for Sail-event

Palette: `#0F3057` (dark navy) + `#00A8CC` (ocean teal) + white.

| File | Idea | Best for |
|------|------|----------|
| `a-sail-wordmark.svg` | SAIL text / sailboat / EVENT stacked as one mark | Header, social preview (text unreadable below 64 px) |
| `b-sail-mark.svg` | Single curved sail + mast + hull arc, no words | Favicon, app icon, header (reads at 16 px) |
| `c-sail-calendar.svg` | Calendar tile with a sail filling the date area | Social preview, about page (calendar detail lost below 32 px) |

**Selected:** `b-sail-mark.svg` supplies the sail, mast and hull used by the app.

Implemented in [frontend/public/favicon.svg](../../frontend/public/favicon.svg) with dark-mode ink, and in [SailMark.tsx](../../frontend/src/components/SailMark.tsx). The original proposals remain here for reference.
