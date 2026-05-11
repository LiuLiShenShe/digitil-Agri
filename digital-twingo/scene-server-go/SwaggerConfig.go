package main

// Swagger 配置说明：
//
// 1. API 注解使用 swaggo 注解格式，放置在 controller 处理函数上。
//
// 2. 启动时自动生成文档：
//   - 服务启动时自动执行 `swag init -g SceneServerApplication.go`
//   - 生成的文件位于 docs/ 目录：docs.go、swagger.json、swagger.yaml
//   - 需要安装 swag CLI: go install github.com/swaggo/swag/cmd/swag@latest
//   - 如果 swag CLI 未安装，会跳过自动生成并使用已有文档
//
// 3. Swagger UI 访问地址：http://localhost:9000/swagger/index.html
//    Swagger JSON 接口：http://localhost:9000/swaggerApi
//
// 4. 生产中禁用 Swagger：application.yml 中设置 swagger.enable: false
