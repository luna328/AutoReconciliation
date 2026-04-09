# MySQL Learning Checklist
## 1) 安装与启动
- [ ] 已安装 MySQL 8
- [ ] MySQL 服务已启动
## 2) 创建数据库与用户（在 mysql 命令行执行）
```sql
CREATE DATABASE IF NOT EXISTS reconciliation DEFAULT CHARACTER SET utf8mb4;
CREATE USER IF NOT EXISTS 'recon_user'@'localhost' IDENTIFIED BY 'recon_pass';
GRANT ALL PRIVILEGES ON reconciliation.* TO 'recon_user'@'localhost';
FLUSH PRIVILEGES;
3) 连接验证命令
- [ ] 本机连接测试：mysql -u recon_user -p -D reconciliation
- [ ] 查看版本：SELECT VERSION();
- [ ] 查看当前库：SELECT DATABASE();
4) 项目环境变量
- [ ] 已创建 .env（可从 .env.example 复制）
- [ ] DATABASE_URL 已配置