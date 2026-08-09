# Project Skills

The skill directories in this folder are vendored from the
[Superpowers](https://github.com/obra/superpowers) skills library by
Jesse Vincent (obra), so they are available as project skills in every
Claude Code session that uses this repository — including remote/web
sessions where the Superpowers plugin is not installed.

- Source: https://github.com/obra/superpowers
- Version: 6.2.0 (commit `44c9b2d`)
- License: MIT (see [LICENSE](LICENSE) in this folder)

## Local modifications

- Cross-skill references were rewritten from the plugin-prefixed form
  (`superpowers:skill-name`) to plain skill names (`skill-name`), because
  vendored project skills are addressed without a plugin prefix.
- The upstream plugin's SessionStart hook is not included; skills are
  discovered via their frontmatter descriptions instead.

## Updating

To pull in a newer upstream version, copy the contents of the upstream
`skills/` directory over the skill folders here, re-apply the reference
rewrite, and update the version/commit noted above:

```bash
git clone --depth 1 https://github.com/obra/superpowers /tmp/superpowers
cp -a /tmp/superpowers/skills/. .claude/skills/
cp /tmp/superpowers/LICENSE .claude/skills/LICENSE
find .claude/skills -name '*.md' -exec sed -i -E 's/superpowers:([a-z-]+)/\1/g' {} +
```
