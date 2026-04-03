# Bootstrap Profiles

These files define the first working version of Ygg bootstrap channels.

## Files

- `components.yaml`
  Canonical component registry for repo roots, URLs, refs, and per-profile enablement.
- `bootstrap-profile.stable.env`
  Safer default channel with a smaller component surface.
- `bootstrap-profile.dev.env`
  Hacking channel with extra tools and optional repos enabled.
- `arch-packages.base.txt`
  Shared Arch packages for every profile.
- `arch-packages.stable.txt`
  Extra packages for the stable channel.
- `arch-packages.dev.txt`
  Extra packages for the dev channel.

## How they are used

Run:

```bash
~/ygg/machine/bootstrap-host.sh --profile stable
~/ygg/machine/bootstrap-host.sh --profile dev
```

The bootstrap script sources the selected profile, renders `components.yaml` into concrete bootstrap variables, loads the listed package manifests, and enables or disables component repos accordingly.
It also renders `ygg-paths.yaml` from the same registry so bootstrap and path registration stay aligned.

## Scope

These are intentionally simple shell/env profiles for now.
They are meant to be easy to inspect and easy to bootstrap from a fresh VM.
