# Known Issues — architecture-design-agent

---

## ISSUE 1: Badge Icons Lost Between Rebuilds

**Symptom**: Badge icons (small workload logos like Data Engineering, Data Factory, Power BI) render as empty `<img>` tags after rebuilding.

**Root Cause**: The extraction regex for badge icons matches `style="height:20px;"`, but if the previous rebuild used `height:16px`, the regex finds 0 matches. Icon data is permanently lost.

**Fix**: Use text-only badges (no `<img>` tag). Text badges look clean and don't require maintaining separate icon data.

**Prevention**: If you must use image badges, keep the height consistent across all rebuilds (always `20px` or always `16px`). Better: just use text badges.

---

## ISSUE 2: Browser Blocks Cross-Folder SVG References

**Symptom**: Icons show as broken images when opening the HTML file locally.

**Root Cause**: Browser `file://` protocol blocks loading SVGs from different folders (CORS-like restriction for local files). The `icons/` directory is in a different path than the HTML file.

**Fix**: Embed all icons as base64 data URIs directly in the HTML.

**Prevention**: NEVER use `<img src="../../icons/Fabric.svg">`. Always use `<img src="data:image/svg+xml;base64,...">`.

---

## ISSUE 3: OneLake Icon Sometimes Missing from Extraction

**Symptom**: `Found 12 icons` instead of expected 13 — OneLake is not extracted.

**Root Cause**: If the previous HTML version didn't include an OneLake component, there's no `alt="OneLake"` tag to extract.

**Impact**: Low — OneLake is implicit in Lakehouse. If needed, re-embed from the original SVG.

**Fix**: Download OneLake SVG and embed manually, or copy from an older HTML version that had it.

---

## ISSUE 4: HTML File Size Grows with Each Icon Addition

**Symptom**: Architecture HTML file is 60-80KB for a simple diagram.

**Root Cause**: Each base64-encoded SVG icon adds 4-8KB to the HTML file.

**Impact**: Minimal — files render fast and are fully self-contained. Acceptable tradeoff.

**Mitigation**: Don't add unused icons. Only embed icons that appear in the diagram.

---

## ISSUE 5: f-string Double Braces in CSS

**Symptom**: Python `SyntaxError` or CSS renders literally as `{property}` instead of applying styles.

**Root Cause**: Python f-strings use `{}` for interpolation. CSS also uses `{}` for rule blocks. Must double all CSS braces: `{{ }}`.

**Fix**: Every `{` in CSS becomes `{{` and every `}` becomes `}}` inside the f-string.

**Prevention**: Keep the f-string template clean. Test with a simple `print(new_html[:200])` before writing to file.

---

## ISSUE 6: Semantic Model Mislabeled as "Power BI"

**Symptom**: Diagram shows "Power BI" badge on the Semantic Model component.

**Root Cause**: Historical association — semantic models were formerly "Power BI datasets". But in Fabric, the Semantic Model is a cross-workload first-class item.

**Fix**: Use a dedicated "Semantic Model" badge (orange: `#fff7ed` / `#c2410c` / `#fdba74`).

**Prevention**: Never assign "Power BI" badge to anything except Reports and PBI-specific features.

---

## ISSUE 7: Pipeline and Notebook Zone Placement

**Symptom**: Diagram merges Pipeline/Notebook into the Lakehouse zone, making it look like one big blob.

**Root Cause**: Treating Pipeline/Notebook as an orchestration overlay within the same zone as the Lakehouse.

**Correct Architecture**: Pipeline and Notebook belong in their own "Ingest & Transform" zone, SEPARATE from the "Store" zone containing the Lakehouse. Pipeline triggers Notebook → Notebook writes Delta tables INTO the Lakehouse.

**Fix**: Create a purple "Ingest & Transform" zone (Pipeline + Notebook) with a step arrow labeled "writes Delta tables" pointing to a green "Store" zone (Lakehouse only).

---

## Debugging Checklist

1. **Icons not rendering?** → Check base64 data URIs are present (not empty `src=""`)
2. **Layout broken?** → Check `flex:1` on Fabric zone, `align-items:stretch` on outer `.h-flow`
3. **Rebuild script error?** → Check f-string `{{` doubling for CSS braces
4. **Wrong icon count?** → Compare `icons.keys()` output to expected list of 12-13 icons
5. **Badges empty?** → Switch to text-only badges (remove `<img>` from badge div)
6. **Arrow labels overlapping?** → Add `<br>` tags for multi-line labels, check `flex-shrink:0`
