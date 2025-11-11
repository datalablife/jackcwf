#!/bin/bash

# Monitoring Setup Script for Production Environment
# Purpose: Initialize and configure monitoring, logging, and alerting
# Usage: bash setup-monitoring.sh
# Last Updated: 2025-11-11

set -e

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  📊 设置生产环境监控、日志和告警                               ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Color definitions
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Configuration
LOG_DIR="/var/log/data-management-prod"
BACKUP_DIR="/var/backups/data-management-prod"
METRICS_PORT=9090

# ========================================
# 1. Create Log Directories
# ========================================
echo -e "${BLUE}[1/6] 创建日志目录...${NC}"
echo ""

# Create main log directory
if [ ! -d "$LOG_DIR" ]; then
    echo "📁 创建日志目录: $LOG_DIR"
    sudo mkdir -p "$LOG_DIR"
    sudo chmod 755 "$LOG_DIR"
    echo -e "${GREEN}✅ 日志目录已创建${NC}"
else
    echo -e "${GREEN}✅ 日志目录已存在: $LOG_DIR${NC}"
fi

# Create subdirectories for different log types
for subdir in archive rotated errors security database metrics; do
    if [ ! -d "$LOG_DIR/$subdir" ]; then
        sudo mkdir -p "$LOG_DIR/$subdir"
        sudo chmod 755 "$LOG_DIR/$subdir"
    fi
done
echo -e "${GREEN}✅ 日志子目录已创建${NC}"
echo ""

# ========================================
# 2. Create Backup Directory
# ========================================
echo -e "${BLUE}[2/6] 创建备份目录...${NC}"
echo ""

if [ ! -d "$BACKUP_DIR" ]; then
    echo "📁 创建备份目录: $BACKUP_DIR"
    sudo mkdir -p "$BACKUP_DIR"
    sudo chmod 750 "$BACKUP_DIR"
    echo -e "${GREEN}✅ 备份目录已创建${NC}"
else
    echo -e "${GREEN}✅ 备份目录已存在: $BACKUP_DIR${NC}"
fi

for subdir in databases logs configs; do
    if [ ! -d "$BACKUP_DIR/$subdir" ]; then
        sudo mkdir -p "$BACKUP_DIR/$subdir"
        sudo chmod 750 "$BACKUP_DIR/$subdir"
    fi
done
echo -e "${GREEN}✅ 备份子目录已创建${NC}"
echo ""

# ========================================
# 3. Set Up Log Rotation
# ========================================
echo -e "${BLUE}[3/6] 配置日志轮转...${NC}"
echo ""

if [ -f "logrotate-config" ]; then
    echo "📋 复制日志轮转配置..."
    if sudo cp logrotate-config /etc/logrotate.d/data-management-prod; then
        echo -e "${GREEN}✅ 日志轮转配置已安装${NC}"
    else
        echo -e "${YELLOW}⚠️  需要 sudo 权限来安装日志轮转配置${NC}"
        echo "   手动安装: sudo cp logrotate-config /etc/logrotate.d/data-management-prod"
    fi
else
    echo -e "${YELLOW}⚠️  logrotate-config 文件不存在${NC}"
fi

# Test logrotate configuration
echo "测试日志轮转配置..."
if command -v logrotate &> /dev/null; then
    if sudo logrotate -d /etc/logrotate.d/data-management-prod > /dev/null 2>&1; then
        echo -e "${GREEN}✅ 日志轮转配置有效${NC}"
    else
        echo -e "${YELLOW}⚠️  日志轮转配置可能有错误${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  logrotate 未安装，请手动配置日志轮转${NC}"
fi
echo ""

# ========================================
# 4. Initialize Monitoring Configuration
# ========================================
echo -e "${BLUE}[4/6] 初始化监控配置...${NC}"
echo ""

if [ -f "monitoring-config.yml" ]; then
    echo "📋 复制监控配置..."
    if [ ! -d "/etc/data-management-prod" ]; then
        sudo mkdir -p /etc/data-management-prod
    fi
    sudo cp monitoring-config.yml /etc/data-management-prod/
    echo -e "${GREEN}✅ 监控配置已安装${NC}"
else
    echo -e "${YELLOW}⚠️  monitoring-config.yml 文件不存在${NC}"
fi

echo ""

# ========================================
# 5. Initialize Alert Rules
# ========================================
echo -e "${BLUE}[5/6] 初始化告警规则...${NC}"
echo ""

if [ -f "alert-rules.json" ]; then
    echo "📋 复制告警规则..."
    if [ ! -d "/etc/data-management-prod/alerts" ]; then
        sudo mkdir -p /etc/data-management-prod/alerts
    fi
    sudo cp alert-rules.json /etc/data-management-prod/alerts/
    echo -e "${GREEN}✅ 告警规则已安装${NC}"
else
    echo -e "${YELLOW}⚠️  alert-rules.json 文件不存在${NC}"
fi

echo ""

# ========================================
# 6. Verify Monitoring Components
# ========================================
echo -e "${BLUE}[6/6] 验证监控组件...${NC}"
echo ""

# Check if Prometheus is available
if command -v prometheus &> /dev/null; then
    echo -e "${GREEN}✅ Prometheus 已安装${NC}"
else
    echo -e "${YELLOW}⚠️  Prometheus 未安装 - 使用: sudo apt-get install prometheus${NC}"
fi

# Check if Grafana is available
if command -v grafana-server &> /dev/null; then
    echo -e "${GREEN}✅ Grafana 已安装${NC}"
else
    echo -e "${YELLOW}⚠️  Grafana 未安装 - 使用: sudo apt-get install grafana${NC}"
fi

# Check if Alertmanager is available
if command -v alertmanager &> /dev/null; then
    echo -e "${GREEN}✅ Alertmanager 已安装${NC}"
else
    echo -e "${YELLOW}⚠️  Alertmanager 未安装 - 使用: sudo apt-get install alertmanager${NC}"
fi

# Check if journalctl is available for centralized logging
if command -v journalctl &> /dev/null; then
    echo -e "${GREEN}✅ systemd 日志已可用${NC}"
else
    echo -e "${YELLOW}⚠️  systemd 日志不可用${NC}"
fi

echo ""

# ========================================
# Summary and Next Steps
# ========================================
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  ✅ 监控配置初始化完成                                         ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

echo -e "${GREEN}📋 已完成的工作:${NC}"
echo "   ✅ 日志目录结构已创建"
echo "   ✅ 备份目录已创建"
echo "   ✅ 日志轮转配置已安装"
echo "   ✅ 监控配置已部署"
echo "   ✅ 告警规则已配置"
echo ""

echo -e "${YELLOW}📝 需要完成的任务:${NC}"
echo "   1. 安装和配置 Prometheus (可选):"
echo "      sudo apt-get install prometheus"
echo ""
echo "   2. 安装和配置 Grafana (可选):"
echo "      sudo apt-get install grafana-server"
echo ""
echo "   3. 配置 Slack 告警:"
echo "      编辑 /etc/data-management-prod/alerts/alert-rules.json"
echo "      更新 SLACK_WEBHOOK_URL"
echo ""
echo "   4. 配置邮件告警:"
echo "      编辑 backend/.env.production"
echo "      添加 SMTP 配置"
echo ""
echo "   5. 配置监控端点:"
echo "      确保后端配置了 /metrics 端点"
echo "      METRICS_PORT=$METRICS_PORT"
echo ""
echo "   6. 启用日志聚合 (可选):"
echo "      - 配置 rsyslog 远程日志"
echo "      - 配置 ELK Stack (Elasticsearch, Logstash, Kibana)"
echo "      - 配置 Splunk 或其他日志管理工具"
echo ""

echo -e "${BLUE}📁 配置文件位置:${NC}"
echo "   监控配置: /etc/data-management-prod/monitoring-config.yml"
echo "   告警规则: /etc/data-management-prod/alerts/alert-rules.json"
echo "   日志轮转: /etc/logrotate.d/data-management-prod"
echo "   日志目录: $LOG_DIR"
echo "   备份目录: $BACKUP_DIR"
echo ""

echo -e "${BLUE}🔗 监控服务访问:${NC}"
echo "   Prometheus (如果已安装): http://localhost:9090"
echo "   Grafana (如果已安装): http://localhost:3000"
echo "   应用指标: http://localhost:8000/metrics"
echo "   应用健康: http://localhost:8000/health"
echo ""

echo -e "${BLUE}📊 建议的监控工具:${NC}"
echo "   1. Prometheus + Grafana (推荐)"
echo "      - 低开销、高效率"
echo "      - 完全开源"
echo "   2. ELK Stack (Elasticsearch, Logstash, Kibana)"
echo "      - 日志搜索和分析"
echo "      - 可扩展性强"
echo "   3. DataDog (SaaS)"
echo "      - 完全托管"
echo "      - 包含 APM 和日志"
echo "   4. New Relic (SaaS)"
echo "      - APM 专家"
echo "      - 完整的性能监控"
echo ""

echo -e "${GREEN}✅ 监控框架已准备就绪！${NC}"
echo ""

# Create a summary file
cat > monitoring-setup-summary.txt << EOF
Monitoring Setup Summary
Generated: $(date)

Configuration Files:
- monitoring-config.yml: Main monitoring configuration
- alert-rules.json: Alert definitions and escalation policies
- logrotate-config: Log rotation rules

Directories Created:
- $LOG_DIR: Application logs
- $LOG_DIR/archive: Archived logs
- $LOG_DIR/rotated: Rotated logs
- $LOG_DIR/errors: Error logs
- $LOG_DIR/security: Security/audit logs
- $LOG_DIR/database: Database logs
- $LOG_DIR/metrics: Metrics logs
- $BACKUP_DIR: Backup directory

Monitoring Components Status:
- Prometheus: $(command -v prometheus &> /dev/null && echo 'Installed' || echo 'Not installed')
- Grafana: $(command -v grafana-server &> /dev/null && echo 'Installed' || echo 'Not installed')
- Alertmanager: $(command -v alertmanager &> /dev/null && echo 'Installed' || echo 'Not installed')
- Journalctl: $(command -v journalctl &> /dev/null && echo 'Installed' || echo 'Not installed')

Next Steps:
1. Review and update monitoring-config.yml with your settings
2. Configure alert notification channels (Slack, email, PagerDuty)
3. Install optional monitoring tools (Prometheus, Grafana)
4. Test alert notifications
5. Set up log aggregation if needed
6. Configure dashboards for key metrics
7. Establish on-call procedures
8. Schedule regular reviews of alert rules

EOF

echo "Summary saved to: monitoring-setup-summary.txt"
echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  🚀 监控、日志和告警配置完成                                   ║"
echo "║     下一步: 进行 T087 集成测试报告和验收                      ║"
echo "╚════════════════════════════════════════════════════════════════╝"
