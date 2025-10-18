#!/bin/bash

# MCP Account Switching Script
# Usage: ./switch-mcp-account.sh [account1|account2]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CURSOR_DIR="$HOME/.cursor"
PROJECT_CURSOR_DIR="$SCRIPT_DIR/.cursor"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if account configuration exists
check_account_config() {
    local account=$1
    local config_file="$PROJECT_CURSOR_DIR/mcp-account${account}.json"
    
    if [[ ! -f "$config_file" ]]; then
        print_error "Configuration file for account $account not found: $config_file"
        exit 1
    fi
}

# Function to backup current MCP configuration
backup_current_config() {
    local backup_file="$CURSOR_DIR/mcp.json.backup.$(date +%Y%m%d_%H%M%S)"
    
    if [[ -f "$CURSOR_DIR/mcp.json" ]]; then
        cp "$CURSOR_DIR/mcp.json" "$backup_file"
        print_status "Backed up current MCP configuration to: $backup_file"
    fi
}

# Function to switch to account 1
switch_to_account1() {
    print_status "Switching to Atlassian Account 1..."
    
    check_account_config "1"
    backup_current_config
    
    # Copy account 1 configuration to global Cursor directory
    cp "$PROJECT_CURSOR_DIR/mcp-account1.json" "$CURSOR_DIR/mcp.json"
    
    # Load environment variables for account 1
    if [[ -f "$SCRIPT_DIR/env.account1.template" ]]; then
        print_warning "Please create .env.account1 file with your actual credentials:"
        print_warning "cp env.account1.template .env.account1"
        print_warning "Then edit .env.account1 with your actual values"
    fi
    
    print_success "Switched to Atlassian Account 1"
    print_status "You may need to restart Cursor for changes to take effect"
}

# Function to switch to account 2
switch_to_account2() {
    print_status "Switching to Atlassian Account 2..."
    
    check_account_config "2"
    backup_current_config
    
    # Copy account 2 configuration to global Cursor directory
    cp "$PROJECT_CURSOR_DIR/mcp-account2.json" "$CURSOR_DIR/mcp.json"
    
    # Load environment variables for account 2
    if [[ -f "$SCRIPT_DIR/env.account2.template" ]]; then
        print_warning "Please create .env.account2 file with your actual credentials:"
        print_warning "cp env.account2.template .env.account2"
        print_warning "Then edit .env.account2 with your actual values"
    fi
    
    print_success "Switched to Atlassian Account 2"
    print_status "You may need to restart Cursor for changes to take effect"
}

# Function to show current status
show_status() {
    print_status "Current MCP Configuration Status:"
    
    if [[ -f "$CURSOR_DIR/mcp.json" ]]; then
        echo ""
        print_status "Active MCP configuration:"
        cat "$CURSOR_DIR/mcp.json" | jq '.mcpServers | keys' 2>/dev/null || cat "$CURSOR_DIR/mcp.json"
    else
        print_warning "No MCP configuration found in $CURSOR_DIR/mcp.json"
    fi
    
    echo ""
    print_status "Available account configurations:"
    for config in "$PROJECT_CURSOR_DIR"/mcp-account*.json; do
        if [[ -f "$config" ]]; then
            echo "  - $(basename "$config")"
        fi
    done
}

# Function to show help
show_help() {
    echo "MCP Account Switching Script"
    echo ""
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  account1    Switch to Atlassian Account 1"
    echo "  account2    Switch to Atlassian Account 2"
    echo "  status      Show current configuration status"
    echo "  help        Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 account1     # Switch to account 1"
    echo "  $0 account2     # Switch to account 2"
    echo "  $0 status       # Show current status"
}

# Main script logic
main() {
    case "${1:-help}" in
        "account1")
            switch_to_account1
            ;;
        "account2")
            switch_to_account2
            ;;
        "status")
            show_status
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            print_error "Unknown command: $1"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"
