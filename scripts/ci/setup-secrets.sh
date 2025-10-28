#!/bin/bash
# GitHub Secrets Setup Script
# Usage: ./setup-secrets.sh

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_section() {
    echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
}

# Check prerequisites
check_prerequisites() {
    log_section "Checking Prerequisites"

    # Check if gh CLI is installed
    if ! command -v gh &> /dev/null; then
        log_error "GitHub CLI (gh) is not installed"
        log_info "Install from: https://cli.github.com/"
        log_info "Or run: brew install gh (macOS) | apt install gh (Ubuntu)"
        exit 1
    fi
    log_info "✓ GitHub CLI installed: $(gh --version | head -1)"

    # Check if coolify CLI is installed
    if ! command -v coolify &> /dev/null; then
        log_error "Coolify CLI is not installed"
        log_info "Install from: https://github.com/coollabsio/coolify-cli"
        log_info "Or run: curl -fsSL https://raw.githubusercontent.com/coollabsio/coolify-cli/main/scripts/install.sh | bash"
        exit 1
    fi
    log_info "✓ Coolify CLI installed: $(coolify version)"

    # Check GitHub authentication
    if ! gh auth status &> /dev/null; then
        log_error "Not authenticated with GitHub"
        log_info "Run: gh auth login"
        exit 1
    fi
    log_info "✓ GitHub authenticated"

    # Get repository info
    REPO_NAME=$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null || echo "")
    if [ -z "$REPO_NAME" ]; then
        log_error "Not in a GitHub repository"
        exit 1
    fi
    log_info "✓ Repository: $REPO_NAME"
}

# Collect Coolify information
collect_coolify_info() {
    log_section "Coolify Configuration"

    # Coolify URL
    read -p "Coolify URL [https://coolpanel.jackcwf.com]: " COOLIFY_URL
    COOLIFY_URL=${COOLIFY_URL:-https://coolpanel.jackcwf.com}
    log_info "Coolify URL: $COOLIFY_URL"

    # Coolify API Token
    log_warn "Your Coolify API token (starts with '2|'):"
    read -sp "Token: " COOLIFY_TOKEN
    echo ""

    if [ -z "$COOLIFY_TOKEN" ]; then
        log_error "Coolify token is required"
        exit 1
    fi

    # Verify connection
    log_info "Verifying Coolify connection..."
    if ! coolify context add temp-context "$COOLIFY_URL" "$COOLIFY_TOKEN" --force &> /dev/null; then
        log_error "Failed to connect to Coolify"
        exit 1
    fi

    log_info "✓ Coolify connection verified"

    # Get application UUIDs
    log_info "\nFetching applications..."
    APPS=$(coolify app list --format json 2>/dev/null || echo "[]")

    if [ "$APPS" == "[]" ]; then
        log_warn "No applications found"
    else
        log_info "Available applications:"
        echo "$APPS" | jq -r '.[] | "  - \(.name) (\(.uuid))"'
    fi

    # Collect UUIDs
    echo ""
    read -p "Development app UUID: " DEV_UUID
    read -p "Staging app UUID: " STAGING_UUID
    read -p "Production app UUID: " PROD_UUID

    if [ -z "$DEV_UUID" ] || [ -z "$STAGING_UUID" ] || [ -z "$PROD_UUID" ]; then
        log_error "All UUIDs are required"
        exit 1
    fi

    # Verify UUIDs
    log_info "\nVerifying application UUIDs..."
    for uuid in "$DEV_UUID" "$STAGING_UUID" "$PROD_UUID"; do
        if coolify app get "$uuid" &> /dev/null; then
            log_info "✓ Valid UUID: $uuid"
        else
            log_error "Invalid UUID: $uuid"
            exit 1
        fi
    done
}

# Set repository secrets
set_repository_secrets() {
    log_section "Setting Repository Secrets"

    # Set Coolify URL
    log_info "Setting COOLIFY_URL..."
    echo "$COOLIFY_URL" | gh secret set COOLIFY_URL
    log_info "✓ COOLIFY_URL set"

    # Set Coolify API Token
    log_info "Setting COOLIFY_API_TOKEN..."
    echo "$COOLIFY_TOKEN" | gh secret set COOLIFY_API_TOKEN
    log_info "✓ COOLIFY_API_TOKEN set"

    log_info "\n✓ Repository secrets configured"
}

# Create and configure environments
setup_environments() {
    log_section "Setting Up Environments"

    # Development environment
    log_info "Creating development environment..."
    gh api -X PUT "repos/$REPO_NAME/environments/development" \
        --silent 2>/dev/null || log_warn "Environment may already exist"

    log_info "Setting development secrets..."
    echo "$DEV_UUID" | gh secret set COOLIFY_DEV_APP_UUID --env development
    log_info "✓ Development environment configured"

    # Staging environment
    log_info "\nCreating staging environment..."
    gh api -X PUT "repos/$REPO_NAME/environments/staging" \
        --silent 2>/dev/null || log_warn "Environment may already exist"

    log_info "Setting staging secrets..."
    echo "$STAGING_UUID" | gh secret set COOLIFY_STAGING_APP_UUID --env staging
    log_info "✓ Staging environment configured"

    # Production environment
    log_info "\nCreating production environment..."
    gh api -X PUT "repos/$REPO_NAME/environments/production" \
        -f wait_timer=300 \
        --silent 2>/dev/null || log_warn "Environment may already exist"

    log_info "Setting production secrets..."
    echo "$PROD_UUID" | gh secret set COOLIFY_PROD_APP_UUID --env production
    log_info "✓ Production environment configured"

    log_warn "\nNote: Add required reviewers for production manually:"
    log_info "  Go to Settings → Environments → production → Required reviewers"
}

# Enable GitHub Actions
enable_actions() {
    log_section "Enabling GitHub Actions"

    log_info "Configuring Actions permissions..."

    # Enable Actions
    gh api -X PUT "repos/$REPO_NAME/actions/permissions" \
        -f enabled=true \
        -f allowed_actions=all \
        --silent 2>/dev/null || log_warn "Could not configure Actions"

    # Set workflow permissions
    gh api -X PUT "repos/$REPO_NAME/actions/permissions/workflow" \
        -f default_workflow_permissions=write \
        -f can_approve_pull_request_reviews=true \
        --silent 2>/dev/null || log_warn "Could not configure workflow permissions"

    log_info "✓ GitHub Actions enabled"
}

# Setup branch protection
setup_branch_protection() {
    log_section "Setting Up Branch Protection"

    log_info "Configuring main branch protection..."

    gh api -X PUT "repos/$REPO_NAME/branches/main/protection" \
        -f required_status_checks[strict]=true \
        -f required_status_checks[contexts][]=CI\ Summary \
        -f required_pull_request_reviews[dismiss_stale_reviews]=true \
        -f required_pull_request_reviews[require_code_owner_reviews]=false \
        -f required_pull_request_reviews[required_approving_review_count]=1 \
        -f required_conversation_resolution[enabled]=true \
        -f enforce_admins[enabled]=false \
        -f restrictions=null \
        --silent 2>/dev/null && log_info "✓ Main branch protected" || log_warn "Could not configure branch protection (may need admin access)"

    log_info "\nConfiguring develop branch protection..."

    gh api -X PUT "repos/$REPO_NAME/branches/develop/protection" \
        -f required_status_checks[strict]=true \
        -f required_status_checks[contexts][]=Pre-commit\ Summary \
        -f enforce_admins[enabled]=false \
        -f restrictions=null \
        --silent 2>/dev/null && log_info "✓ Develop branch protected" || log_warn "Could not configure branch protection"
}

# Verify setup
verify_setup() {
    log_section "Verifying Setup"

    log_info "Repository Secrets:"
    gh secret list | grep -E "COOLIFY" || log_warn "No secrets found"

    log_info "\nEnvironment Secrets:"
    for env in development staging production; do
        log_info "\n  $env:"
        gh secret list --env "$env" 2>/dev/null || log_warn "    No secrets found"
    done

    log_info "\nBranch Protection:"
    gh api "repos/$REPO_NAME/branches/main/protection" --jq '.required_status_checks.contexts[]' 2>/dev/null || log_warn "Not configured"
}

# Summary
print_summary() {
    log_section "Setup Complete"

    echo -e "${GREEN}✓ CI/CD pipeline configured successfully!${NC}\n"

    echo "Summary:"
    echo "  Repository: $REPO_NAME"
    echo "  Coolify URL: $COOLIFY_URL"
    echo "  Dev App: $DEV_UUID"
    echo "  Staging App: $STAGING_UUID"
    echo "  Prod App: $PROD_UUID"

    echo -e "\nNext Steps:"
    echo "  1. Add required reviewers for production environment"
    echo "     Settings → Environments → production → Required reviewers"
    echo ""
    echo "  2. Enable Dependabot"
    echo "     Settings → Code security → Enable Dependabot"
    echo ""
    echo "  3. Test the pipeline"
    echo "     git push origin main"
    echo ""
    echo "  4. View workflow runs"
    echo "     https://github.com/$REPO_NAME/actions"
    echo ""

    echo -e "${BLUE}Documentation: docs/deployment/ci-cd.md${NC}"
}

# Main execution
main() {
    log_section "CI/CD Setup Script"

    check_prerequisites
    collect_coolify_info
    set_repository_secrets
    setup_environments
    enable_actions
    setup_branch_protection
    verify_setup
    print_summary
}

# Run main function
main
