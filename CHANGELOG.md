# Changelog

Versions follow [Semantic Versioning](https://semver.org/). Patch releases (x.y.Z) are fixes and maintenance only.

## [1.0.1] - 2026-11-18

Maintenance release: CI, dependency and container fixes since 1.0.0. No feature changes.

### Security
- Containers (backend, frontend, nginx) now run as a non-root user.
- Updated vulnerable dependencies: FastAPI, Pillow, python-multipart, python-dotenv, and frontend packages via `npm audit` fixes; backend dependencies are pinned to exact versions.
- Replaced `python-jose` with `PyJWT` for token handling (removes the ecdsa, cryptography and pyasn1 transitive dependencies).

### Fixed
- CI pipeline: backend tests, linting (flake8, black, isort, ESLint), TypeScript compilation, integration tests under Docker Compose V2, and CodeQL action upgraded to v4.
- Tests expect `401` for unauthenticated requests.
- Duplicate database indexes; `package-lock.json` added.
- Frontend image builds on `node:20-slim` with `npm ci`.

### Changed
- Backend test coverage raised to 83.5%.

## [1.0.0] - 2026-01-29

Initial release: collections, watches, images, service history, market values and analytics, comparison, user management, movement accuracy tracking.
