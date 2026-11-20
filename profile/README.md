# Borealis Research

An independent open-source research laboratory exploring distributed computing, specialised AI agents and resilient digital infrastructure.

## Projects

| Project | Description | Status |
|---------|-------------|--------|
| [Nyyrikki](https://github.com/borealis-research-lab/security-event-analysis) (`security-event-analysis`) | Identifies potentially suspicious activity in local Windows Security events, with traceable evidence. Deterministic rules; reports in `borealis-agent-report/1`. | Experimental MVP, validated on real Windows data |
| [Ilmarinen](https://github.com/borealis-research-lab/file-integrity) (`file-integrity`) | Detects unexpected content changes to user-selected files by comparing SHA-256 hashes with a protected baseline. Read-only; reports in `borealis-agent-report/1`. | Experimental, tested on Windows and Linux |

## How we work

- **One responsibility per project.** Each project stays narrow and independent.
- **Local first.** Tools are designed to run on your own machine, without mandatory cloud services.
- **Evidence over assertion.** Where AI is used, its output stays grounded in the original input data.
- **Open source.** Projects are published under open-source licences.

All projects are experimental and are not production-ready.

## Architecture

Borealis is designed as independent specialist agents running locally in the environments they protect, with optional central coordination and a separate volunteer compute network. See [Borealis Architecture v1](https://github.com/borealis-research-lab/.github/blob/main/architecture/borealis-architecture-v1.md). Most of it is not yet built.

## Contributing

Each project has its own contribution guidelines and security policy. Please read them before opening an issue or pull request.
