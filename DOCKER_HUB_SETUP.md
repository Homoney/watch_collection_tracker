# Docker Hub Publishing Setup Guide

This guide explains how to set up automated Docker Hub publishing for the Watch Collection Tracker.

## Prerequisites

1. **Docker Hub Account**
   - Create an account at https://hub.docker.com if you don't have one
   - Remember your Docker Hub username (currently set to `dhomoney` in the workflow)

2. **GitHub Repository**
   - Repository should be on GitHub
   - You need admin access to configure secrets

## Step 1: Create Docker Hub Access Token

1. Log in to Docker Hub: https://hub.docker.com
2. Click your username → **Account Settings**
3. Go to **Security** → **Personal Access Tokens**
4. Click **Generate New Token**
   - **Description**: `GitHub Actions - Watch Tracker`
   - **Access permissions**: Select **Read & Write**
5. Click **Generate** and **copy the token** (you won't see it again!)

## Step 2: Add GitHub Secret

1. Go to your GitHub repository
2. Navigate to **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add the following secret:
   - **Name**: `DOCKER_HUB_TOKEN`
   - **Value**: Paste the Docker Hub access token from Step 1
5. Click **Add secret**

## Step 3: Update Docker Hub Username (if needed)

If your Docker Hub username is NOT `dhomoney`, you need to update the workflow:

1. Open `.github/workflows/docker-publish.yml`
2. Change the `DOCKER_USERNAME` line under `env:`:
   ```yaml
   DOCKER_USERNAME: dhomoney  # Change this to your Docker Hub username
   ```
3. Commit the change

## Step 4: Test the Workflow

The workflow will automatically trigger when you:
- Merge a pull request into `main` (the branch rules for `main` require a pull request with passing checks)
- Push a version tag (e.g., `v2.0.1`)
- Manually trigger via GitHub Actions UI

**Every merge to `main` publishes images**, so merge only what is ready to ship.

### Option A: Merge to Main

Merging a pull request creates images tagged `latest` and `main`.

### Option B: Push a Release Tag
```bash
git tag -a v2.0.1 -m "Release 2.0.1"
git push origin v2.0.1
```

This will create images tagged as (no `v` prefix on Docker Hub):
- `2.0.1`
- `2.0`
- `2`
- `latest`

And automatically create a GitHub release with `docker-compose.yml` and `.env.example` attached.

### Option C: Manual Trigger
1. Go to **Actions** tab in GitHub
2. Click **Publish to Docker Hub**
3. Click **Run workflow**
4. Select branch and click **Run workflow**

## Step 5: Verify the Images

After the workflow completes (about 10 minutes):

1. Check Docker Hub: `https://hub.docker.com/r/dhomoney/watch-tracker`

2. Test pulling and running the image:
   ```bash
   docker pull dhomoney/watch-tracker:latest
   docker run --rm -p 8080:8000 -v watch-test:/data dhomoney/watch-tracker:latest
   ```

## Workflow Details

### Triggers
- **Push to main**: Builds and pushes `latest` and `main` tags
- **Version tags** (`v*.*.*`): Builds and pushes version tags + `latest`
- **Manual**: Can trigger anytime via GitHub Actions UI

### Multi-Architecture
The workflow builds for:
- `linux/amd64` (Intel/AMD processors)
- `linux/arm64` (ARM processors, Apple Silicon)

### Image Created
One image, `dhomoney/watch-tracker`, built from the root `Dockerfile`: the web app is built with Node, then served by the FastAPI app with the API and uploaded files.

The old `dhomoney/watch-tracker-backend` and `dhomoney/watch-tracker-frontend` images are no longer built. Mark them deprecated on Docker Hub (repository description) and point to `dhomoney/watch-tracker`.

### Build Time
About 10 minutes for both platforms (recent runs, with the build cache). The arm64 half is built under emulation, so a build without cache takes longer.

## Tagging Strategy

Versions follow semantic versioning, `x.y.z`: patch for fixes, security and dependency updates; minor for new features or changes in behaviour; major for breaking changes (see the README, "Versioning and releases").

| Tag Pattern | Example | When Used |
|-------------|---------|-----------|
| `latest` | `latest` | Every merge to main and every version tag |
| `main` | `main` | Every merge to main |
| `X.Y.Z` | `2.0.1` | Exact version from git tag `v2.0.1` |
| `X.Y` | `2.0` | Minor version from git tag |
| `X` | `2` | Major version from git tag |

## Common Issues

### Issue: "Error: Cannot connect to the Docker daemon"
**Solution**: This shouldn't happen in GitHub Actions, but if it does, ensure Docker Buildx is set up correctly.

### Issue: "unauthorized: incorrect username or password"
**Solution**:
- Verify Docker Hub username in workflow file
- Verify `DOCKER_HUB_TOKEN` secret is set correctly
- Regenerate Docker Hub token if needed

### Issue: "no space left on device"
**Solution**: GitHub Actions has enough space. This might indicate a Docker layer issue. The workflow uses cache, which should prevent this.

### Issue: Build fails on ARM64
**Solution**: Some dependencies might not support ARM64. Check backend/requirements.txt for platform-specific packages.

## Making Your First Release

Once everything is set up and tested:

1. On a release branch, set the new version in `frontend/package.json` (and `package-lock.json`) and `backend/app/main.py`, and add a `CHANGELOG.md` entry.
2. Open a pull request, wait for the required checks, and merge it.
3. Tag the merge commit and push the tag:
   ```bash
   git tag -a v2.0.1 -m "Release 2.0.1"
   git push origin v2.0.1
   ```
4. Wait for the workflow: it pushes the images and creates the GitHub release with `docker-compose.yml` and `.env.example` attached.

## Docker Hub Repository Settings

### Recommended Settings:
1. **Description**: Add a description of your project
2. **README**: Links to your GitHub repository automatically
3. **Visibility**: Public (or Private if preferred)
4. **Automated Builds**: Disabled (we use GitHub Actions instead)

## Next Steps

After publishing to Docker Hub:

1. Test the published image (`docker run` as in Step 5; `/health` should answer)
2. Keep the Docker Hub description in step with `DOCKER_HUB.md`
3. The built image is also scanned by the repository's Security Scanning workflow (Trivy), with results in the GitHub Security tab

## Support

If you run into issues:
- Check GitHub Actions logs
- Open an issue on GitHub
