#!/bin/bash
# Monitoring Stack Deployment Script
# Automates the deployment and verification of monitoring services

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
COMPOSE_FILE="$PROJECT_ROOT/docker-compose.monitoring.yml"
ENV_FILE="$PROJECT_ROOT/.env.monitoring"

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi

    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi

    # Check if compose file exists
    if [ ! -f "$COMPOSE_FILE" ]; then
        log_error "Docker Compose file not found: $COMPOSE_FILE"
        exit 1
    fi

    log_info "Prerequisites check passed ✓"
}

setup_environment() {
    log_info "Setting up environment..."

    # Check if .env.monitoring exists
    if [ ! -f "$ENV_FILE" ]; then
        log_warn ".env.monitoring not found. Creating from example..."
        if [ -f "$PROJECT_ROOT/.env.monitoring.example" ]; then
            cp "$PROJECT_ROOT/.env.monitoring.example" "$ENV_FILE"
            log_warn "Please edit .env.monitoring with your configuration"
            log_warn "Especially: GRAFANA_ADMIN_PASSWORD, SMTP credentials, SLACK_WEBHOOK_URL"
            read -p "Press Enter to continue after configuring .env.monitoring..."
        else
            log_error ".env.monitoring.example not found. Cannot create environment file."
            exit 1
        fi
    fi

    log_info "Environment setup complete ✓"
}

create_directories() {
    log_info "Creating data directories..."

    mkdir -p "$PROJECT_ROOT/monitoring/data/prometheus"
    mkdir -p "$PROJECT_ROOT/monitoring/data/grafana"
    mkdir -p "$PROJECT_ROOT/monitoring/data/elasticsearch"
    mkdir -p "$PROJECT_ROOT/monitoring/data/logstash"

    log_info "Data directories created ✓"
}

start_services() {
    log_info "Starting monitoring services..."

    cd "$PROJECT_ROOT"
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d

    log_info "Monitoring services started ✓"
}

wait_for_service() {
    local service_name=$1
    local service_url=$2
    local max_attempts=30
    local attempt=1

    log_info "Waiting for $service_name to be ready..."

    while [ $attempt -le $max_attempts ]; do
        if curl -sf "$service_url" > /dev/null 2>&1; then
            log_info "$service_name is ready ✓"
            return 0
        fi

        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done

    log_error "$service_name failed to start"
    return 1
}

verify_services() {
    log_info "Verifying services..."

    # Wait for Elasticsearch
    wait_for_service "Elasticsearch" "http://localhost:9200/_cluster/health"

    # Wait for Prometheus
    wait_for_service "Prometheus" "http://localhost:9090/-/healthy"

    # Wait for Grafana
    wait_for_service "Grafana" "http://localhost:3001/api/health"

    # Wait for Kibana
    wait_for_service "Kibana" "http://localhost:5601/api/status"

    # Wait for AlertManager
    wait_for_service "AlertManager" "http://localhost:9093/-/healthy"

    log_info "All services are healthy ✓"
}

setup_elasticsearch_indices() {
    log_info "Setting up Elasticsearch indices..."

    # Create index template for langchain-ai logs
    curl -X PUT "http://localhost:9200/_index_template/langchain-ai-template" \
        -H 'Content-Type: application/json' \
        -d '{
            "index_patterns": ["langchain-ai-*"],
            "template": {
                "settings": {
                    "number_of_shards": 1,
                    "number_of_replicas": 0,
                    "index.lifecycle.name": "langchain-ai-policy",
                    "index.lifecycle.rollover_alias": "langchain-ai"
                },
                "mappings": {
                    "properties": {
                        "@timestamp": { "type": "date" },
                        "level": { "type": "keyword" },
                        "message": { "type": "text" },
                        "component": { "type": "keyword" },
                        "request_id": { "type": "keyword" },
                        "duration_ms": { "type": "float" },
                        "status": { "type": "integer" }
                    }
                }
            }
        }' > /dev/null 2>&1

    # Create ILM policy for log retention
    curl -X PUT "http://localhost:9200/_ilm/policy/langchain-ai-policy" \
        -H 'Content-Type: application/json' \
        -d '{
            "policy": {
                "phases": {
                    "hot": {
                        "actions": {
                            "rollover": {
                                "max_age": "1d",
                                "max_size": "50gb"
                            }
                        }
                    },
                    "delete": {
                        "min_age": "30d",
                        "actions": {
                            "delete": {}
                        }
                    }
                }
            }
        }' > /dev/null 2>&1

    log_info "Elasticsearch indices configured ✓"
}

print_access_info() {
    log_info "=================================="
    log_info "Monitoring Stack Deployment Complete!"
    log_info "=================================="
    echo ""
    log_info "Access URLs:"
    echo "  Grafana:       http://localhost:3001 (admin/check .env.monitoring)"
    echo "  Prometheus:    http://localhost:9090"
    echo "  Kibana:        http://localhost:5601"
    echo "  AlertManager:  http://localhost:9093"
    echo "  Elasticsearch: http://localhost:9200"
    echo ""
    log_info "Next Steps:"
    echo "  1. Log in to Grafana and explore dashboards"
    echo "  2. Configure Kibana index patterns (langchain-ai-*)"
    echo "  3. Review Prometheus targets at /targets"
    echo "  4. Test alerts in AlertManager"
    echo ""
    log_info "Useful Commands:"
    echo "  View logs:    docker-compose -f $COMPOSE_FILE logs -f [service]"
    echo "  Stop:         docker-compose -f $COMPOSE_FILE down"
    echo "  Restart:      docker-compose -f $COMPOSE_FILE restart [service]"
    echo "  Status:       docker-compose -f $COMPOSE_FILE ps"
    echo ""
}

show_help() {
    cat << EOF
Monitoring Stack Deployment Script

Usage: $0 [COMMAND]

Commands:
    deploy      Deploy the monitoring stack (default)
    stop        Stop all monitoring services
    restart     Restart all monitoring services
    status      Show status of monitoring services
    logs        Show logs from all services
    clean       Stop and remove all containers and volumes
    verify      Verify services are running
    help        Show this help message

Examples:
    $0 deploy
    $0 logs prometheus
    $0 clean

EOF
}

# Command handlers
deploy_command() {
    log_info "Starting deployment..."
    check_prerequisites
    setup_environment
    create_directories
    start_services
    verify_services
    setup_elasticsearch_indices
    print_access_info
}

stop_command() {
    log_info "Stopping monitoring services..."
    cd "$PROJECT_ROOT"
    docker-compose -f "$COMPOSE_FILE" down
    log_info "Services stopped ✓"
}

restart_command() {
    log_info "Restarting monitoring services..."
    cd "$PROJECT_ROOT"
    docker-compose -f "$COMPOSE_FILE" restart
    log_info "Services restarted ✓"
}

status_command() {
    cd "$PROJECT_ROOT"
    docker-compose -f "$COMPOSE_FILE" ps
}

logs_command() {
    cd "$PROJECT_ROOT"
    if [ -n "$1" ]; then
        docker-compose -f "$COMPOSE_FILE" logs -f "$1"
    else
        docker-compose -f "$COMPOSE_FILE" logs -f
    fi
}

clean_command() {
    log_warn "This will stop and remove all monitoring containers and volumes!"
    read -p "Are you sure? (yes/no): " confirm

    if [ "$confirm" = "yes" ]; then
        cd "$PROJECT_ROOT"
        docker-compose -f "$COMPOSE_FILE" down -v
        log_info "Cleanup complete ✓"
    else
        log_info "Cleanup cancelled"
    fi
}

verify_command() {
    verify_services
}

# Main script
main() {
    local command="${1:-deploy}"

    case "$command" in
        deploy)
            deploy_command
            ;;
        stop)
            stop_command
            ;;
        restart)
            restart_command
            ;;
        status)
            status_command
            ;;
        logs)
            logs_command "$2"
            ;;
        clean)
            clean_command
            ;;
        verify)
            verify_command
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            log_error "Unknown command: $command"
            show_help
            exit 1
            ;;
    esac
}

# Run main
main "$@"
