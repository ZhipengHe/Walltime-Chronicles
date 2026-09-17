# Cmd+Opt+Remote

Developing on Aqua from your own machine: editing, moving files, and keeping your environments and permissions working on the other side.

- :material-keyboard: [Surviving without VS Code Remote SSH](Surviving-without-VS-Code-Remote-SSH.md) — tunnels, Jupyter, sshfs, and the editor-side options that don't need Remote SSH.
- :material-folder-eye-outline: [The .DS_Store Strikes Back: Finder Edition](The-DS_Store-Strikes-Back.md) — stop macOS from littering `._*` and `.DS_Store` files across your Aqua home dir.
- :material-account-group-outline: [Permissions Don't Move: A /work/group Survival Guide](Permissions-Dont-Move.md) — get the group, the mode bits, and the ACL right when files land in a shared `/work/<group>/` folder, and why `mv` from `~/` breaks all three.
- :material-package-variant-closed: [uv on Aqua: Cache + Envs Placement](uv-on-aqua.md) — the same-filesystem rule, the bench numbers behind it, three placement patterns, and the `env.sh` idiom for team projects on `/work`.
