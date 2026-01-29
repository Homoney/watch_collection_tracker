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
2. Change line 12:
   ```yaml
   DOCKER_USERNAME: dhomoney  # Change this to YOUR Docker Hub username
   ```
3. Commit the change

## Step 4: Test the Workflow

The workflow will automatically trigger when you:
- Push to the `main` branch
- Create a version tag (e.g., `v1.0.0`)
- Manually trigger via GitHub Actions UI

### Option A: Push to Main (Test Build)
```bash
git add .
git commit -m "Add Docker Hub publishing"
git push origin main
```

This will create images tagged as `latest` and `main`.

### Option B: Create a Release Tag (Production)
```bash
git tag v1.0.0
git push origin v1.0.0
```

This will create images tagged as:
- `v1.0.0`
- `v1.0`
- `v1`
- `latest`

And automatically create a GitHub release with the docker-compose.hub.yml file.

### Option C: Manual Trigger
1. Go to **Actions** tab in GitHub
2. Click **Publish to Docker Hub**
3. Click **Run workflow**
4. Select branch and click **Run workflow**

## Step 5: Verify the Images

After the workflow completes (takes 10-15 minutes):

1. Check Docker Hub:
   - Backend: `https://hub.docker.com/r/dhomoney/watch-tracker-backend`
   - Frontend: `https://hub.docker.com/r/dhomoney/watch-tracker-frontend`

2. Test pulling the images:
   ```bash
   docker pull dhomoney/watch-tracker-backend:latest
   docker pull dhomoney/watch-tracker-frontend:latest
   ```

3. Test running with docker-compose:
   ```bash
   docker-compose -f docker-compose.hub.yml up -d
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

### Images Created
The workflow creates two images:
1. `dhomoney/watch-tracker-backend` - FastAPI backend
2. `dhomoney/watch-tracker-frontend` - React frontend (served by nginx)

### Build Time
- First build: ~10-15 minutes (no cache)
- Subsequent builds: ~5-8 minutes (with cache)

## Tagging Strategy

The workflow uses semantic versioning:

| Tag Pattern | Example | When Used |
|-------------|---------|-----------|
| `latest` | `latest` | Every main branch push and version tag |
| `main` | `main` | Every main branch push |
| `v1.0.0` | `v1.0.0` | Exact version from git tag |
| `v1.0` | `v1.0` | Minor version from git tag |
| `v1` | `v1` | Major version from git tag |

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

```bash
# 1. Update version in any relevant files
# 2. Commit all changes
git add .
git commit -m "Release v1.0.0"

# 3. Create and push the tag
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin main
git push origin v1.0.0

# 4. Wait for GitHub Actions to complete
# 5. Check the Release page on GitHub
# 6. Images will be available on Docker Hub
```

## Docker Hub Repository Settings

### Recommended Settings:
1. **Description**: Add a description of your project
2. **README**: Links to your GitHub repository automatically
3. **Visibility**: Public (or Private if preferred)
4. **Automated Builds**: Disabled (we use GitHub Actions instead)

## Next Steps

After publishing to Docker Hub:

1. ✅ Test the images work correctly
2. ✅ Update README badges (optional)
3. ✅ Announce on social media/forums
4. ✅ Create documentation for users
5. ✅ Set up vulnerability scanning (Docker Hub has this built-in)

## Support

If you run into issues:
- Check GitHub Actions logs
- Check Docker Hub build logs
- Open an issue on GitHub
