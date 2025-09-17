# GitHub Branch Protection Setup Guide

This guide will walk you through setting up branch protection rules to ensure all PRs pass the quality gates before being merged into the main branch.

## Prerequisites

1. You must be an admin of the repository
2. The GitHub Actions workflows must be committed to the `main` branch
3. The repository must have GitHub Actions enabled

## Step-by-Step Setup

### Step 1: Navigate to Branch Protection Settings

1. Go to your GitHub repository
2. Click on **Settings** (in the repository navigation bar)
3. In the left sidebar, click on **Branches**

### Step 2: Create Branch Protection Rule

1. Click the **Add rule** button
2. In the "Branch name pattern" field, enter: `main`
3. Configure the following settings:

#### Required Settings:

✅ **Require a pull request before merging**
- Check this box
- Set "Required number of reviewers" to `1` (or your preferred number)
- Optional: Check "Dismiss stale PR approvals when new commits are pushed"

✅ **Require status checks to pass before merging**
- Check this box
- Check "Require branches to be up to date before merging"
- In the search box, add these required status checks:
  - `PR Quality Gate / quality-gate`
  - `Backend CI / test` (if you want individual workflow checks)
  - `Frontend CI / test` (if you want individual workflow checks)

✅ **Require conversation resolution before merging**
- Check this box to ensure all PR comments are resolved

#### Optional but Recommended Settings:

✅ **Restrict pushes that create files**
- This prevents large files from being committed

✅ **Do not allow bypassing the above settings**
- This ensures even admins follow the rules

### Step 3: Save the Rule

1. Scroll down and click **Create** to save the branch protection rule

## Testing the Setup

### Test 1: Create a Test PR

1. Create a new branch: `git checkout -b test-quality-gate`
2. Make a small change to any file
3. Commit and push: 
   ```bash
   git add .
   git commit -m "test: trigger quality gate"
   git push origin test-quality-gate
   ```
4. Create a PR on GitHub
5. Verify that the GitHub Actions workflow runs automatically

### Test 2: Verify Protection Works

1. Try to merge the PR before checks complete - you should see it's blocked
2. Wait for checks to complete
3. If checks pass, you should be able to merge
4. If checks fail, the merge button should remain disabled

## Workflow Overview

The protection setup includes three main workflows:

### 1. `backend-ci.yml`
- Runs Python linting (flake8)
- Checks code formatting (black)
- Runs tests with pytest
- Performs security checks
- Tests Docker build

### 2. `frontend-ci.yml` 
- Runs ESLint for code quality
- Performs TypeScript type checking
- Runs Jest tests
- Builds the Next.js application
- Runs Lighthouse performance checks
- Performs npm security audit

### 3. `pr-quality-gate.yml` (Main orchestrator)
- Detects which parts of the codebase changed
- Runs appropriate checks based on changes
- Only runs backend checks if backend files changed
- Only runs frontend checks if frontend files changed
- Provides a single pass/fail status for the entire PR

## Troubleshooting

### Common Issues:

1. **Status checks not appearing**: 
   - Ensure workflows are on the main branch
   - Make sure workflow names match exactly in branch protection settings
   - Check that GitHub Actions are enabled for the repository

2. **Workflows failing due to missing dependencies**:
   - Check that `requirements.txt` (backend) and `package.json` (frontend) are up to date
   - Verify all necessary dependencies are listed

3. **Tests failing**:
   - Run tests locally first: `cd backend && pytest tests/`
   - For frontend: `cd frontend/flowstate && npm test`

4. **Lint failures**:
   - Run linting locally: `cd backend && flake8 .` or `black --check .`
   - For frontend: `cd frontend/flowstate && npm run lint`

### Getting Help:

- Check the **Actions** tab in your GitHub repository for detailed logs
- Each workflow step shows detailed output to help debug issues
- Failed checks will block the PR merge until resolved

## Customization

You can customize the workflows by:

1. **Adjusting code quality standards**: Edit `.flake8` or `pyproject.toml` for Python
2. **Modifying test requirements**: Update the workflow files in `.github/workflows/`
3. **Adding new checks**: Create additional jobs in the existing workflows
4. **Changing review requirements**: Adjust the number of required reviewers in branch protection

## Security Considerations

- The workflows run with limited permissions
- No secrets are exposed in logs
- Security audits are included for both backend and frontend
- Consider adding additional security scanning tools for production use

Remember: These settings help maintain code quality, but the real value comes from your team's commitment to writing good tests and following the established patterns!