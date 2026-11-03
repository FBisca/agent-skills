# Third-party notices

The code and text of this repository are MIT-licensed (see `LICENSE`) except where a skill folder says otherwise. This file lists everything derived from, copied from, or built on someone else's work. Upstream skills this repo does not carry are listed in `skills.lock.json` and installed from their owners.

## Derived or copied from mattpocock/skills (MIT)

Source: https://github.com/mattpocock/skills, Copyright (c) 2026 Matt Pocock.

| Skill here | Relation |
|---|---|
| `handoff` | Derived: rewritten to ask for a path and to suggest next skills |
| `teach` | Derived: modified from an earlier upstream version |
| `caveman` | Unmodified copy; removed upstream, so `npx skills add` can no longer fetch it |
| `zoom-out` | Unmodified copy; removed upstream, so `npx skills add` can no longer fetch it |

Upstream license text:

```
MIT License

Copyright (c) 2026 Matt Pocock

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## frontend-design: Anthropic (Apache-2.0)

Derived from the `frontend-design` skill in https://github.com/anthropics/skills. Apache License 2.0; full text in `skills/frontend-design/LICENSE`, attribution and change note in `skills/frontend-design/NOTICE.md`. Not endorsed by Anthropic.

## cold-read: Google (Apache-2.0)

`skills/cold-read/reader.md` is adapted from `agents/comprehension.md` in the Elephant-Goldfish Model, https://github.com/google/elephant-goldfish-model. Apache License 2.0; full text in `skills/cold-read/LICENSE`, attribution and change note in `skills/cold-read/NOTICE.md`. Not endorsed by Google.

## Used, not distributed

- **HyperFrames** (https://github.com/heygen-com/hyperframes, Apache-2.0, Copyright HeyGen). `explain-video` drives the HyperFrames CLI and, for its frozen v0.8.184 workflow pieces, fetches them with `skills/explain-video/scripts/fetch-hyperframes.sh`. The `hyperframes`, `hyperframes-cli`, `hyperframes-registry` and `media-use` skills are installed from upstream (`skills.lock.json`), not copied here.
- **Kokoro** (local text-to-speech, via the npm packages pinned in `skills/explain-video/narrator/pnpm-lock.yaml`): see each package's license.
