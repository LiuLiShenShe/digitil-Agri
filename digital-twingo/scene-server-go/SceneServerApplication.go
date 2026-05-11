package main

import (
	"fmt"
	"log"
	"os"
	"os/exec"
	"path/filepath"

	"scene-server-go/config"
	"scene-server-go/controller"
	"scene-server-go/iot"
	"scene-server-go/mapper"

	"github.com/gin-contrib/cors"
	"github.com/gin-gonic/gin"
	_ "github.com/go-sql-driver/mysql"
	"github.com/jmoiron/sqlx"
	swaggerFiles "github.com/swaggo/files"
	ginSwagger "github.com/swaggo/gin-swagger"

	_ "scene-server-go/docs"
)

// @title          三维数字孪生场景设计器接口文档
// @description    三维数字孪生场景设计器接口文档
// @version        v1.0.0
// @contact.name   北京煜邦电力技术股份有限公司
// @contact.url    www.yupont.com
// @contact.email  tiany@yupont.com
func main() {
	// Load config
	err := config.LoadConfig("application.yml")
	if err != nil {
		log.Fatalf("Failed to load config: %v", err)
	}

	// Init logger
	if err := config.InitLogger("/data/fj/数字孪生/logs/backend.log"); err != nil {
		log.Fatalf("Failed to initialize logger: %v", err)
	}
	config.Log("INFO", "Scene Server starting...")

	// Connect to MySQL
	dsn := config.AppConfig.Spring.Datasource.URL
	db, err := sqlx.Connect("mysql", dsn)
	if err != nil {
		log.Fatalf("Failed to connect to database: %v", err)
	}
	defer db.Close()

	db.SetMaxOpenConns(25)
	db.SetMaxIdleConns(5)

	fmt.Println("数据库连接成功")
	config.Log("INFO", "Database connected")

	// Initialize database handle for all mappers
	mapper.SetDB(db)
	iot.SetDB(db)
	if err := iot.EnsureSchema(); err != nil {
		log.Fatalf("Failed to ensure IoT schema: %v", err)
	}

	// Initialize IoT services
	alertSvc := iot.NewAlertService()
	deviceSvc := iot.InitDeviceService(alertSvc)
	alertSvc.SetDeviceService(deviceSvc)

	// Start MQTT adapter (non-blocking)
	go func() {
		deviceSvc.InitMqtt()
	}()

	// Start IoT simulator
	if config.AppConfig.Iot.SimulatorEnabled {
		go deviceSvc.StartSimulator()
		config.Log("INFO", "IoT Simulator started")
	}

	// Create Gin router (already logs to gin.DefaultWriter → log file)
	r := gin.Default()

	// CORS configuration
	r.Use(cors.New(cors.Config{
		AllowCredentials: true,
		AllowOriginFunc:  func(origin string) bool { return true },
		AllowMethods:     []string{"GET", "POST", "DELETE", "PUT"},
		AllowHeaders:     []string{"*"},
		MaxAge:           1800,
	}))

	// Serve generated GLB assets and thumbnails
	r.Static("/scene-assets", "./scene-assets")

	// API routes
	contextPath := config.AppConfig.Server.Servlet.ContextPath
	api := r.Group(contextPath)
	{
		controller.RegisterSceneRoutes(api)
		controller.RegisterModelRoutes(api)
		controller.RegisterDataSvrRoutes(api)
		controller.RegisterBackgroundRoutes(api)
		controller.RegisterAssetRoutes(api)
		controller.RegisterAdminRoutes(api)
		controller.RegisterMonitorRoutes(api)

		// Phase 4: IoT routes
		iot.RegisterIotRoutes(api)
	}

	// Swagger
	if config.AppConfig.Swagger.Enable {
		// Auto-generate swagger docs at startup
		autoGenerateSwagger()

		r.GET("/swagger/*any", ginSwagger.WrapHandler(swaggerFiles.Handler))
		// Serve swagger.json file
		r.GET("/swaggerApi", func(c *gin.Context) {
			swaggerPath := filepath.Join(getProjectDir(), "docs", "swagger.json")
			c.File(swaggerPath)
		})
		port := config.AppConfig.Server.Port
		fmt.Printf("Swagger 已启用，访问地址: http://localhost:%s/swagger/index.html\n", port)
		fmt.Printf("Swagger JSON: http://localhost:%s/swaggerApi\n", port)
	}

	// Start server
	port := config.AppConfig.Server.Port
	config.Log("INFO", "Server starting on port %s", port)
	fmt.Printf("服务启动中，端口: %s ...\n", port)
	if err := r.Run(":" + port); err != nil {
		log.Fatalf("Failed to start server: %v", err)
	}
}

// autoGenerateSwagger runs swag init to regenerate swagger docs at startup.
func autoGenerateSwagger() {
	projectDir := getProjectDir()
	if projectDir == "" {
		fmt.Println("⚠ 未找到项目目录，跳过 Swagger 文档自动生成")
		return
	}

	// Check if swag CLI is available
	if _, err := exec.LookPath("swag"); err != nil {
		fmt.Println("⚠ swag CLI 未安装，使用已有的 Swagger 文档")
		return
	}

	cmd := exec.Command("swag", "init", "-g", "SceneServerApplication.go")
	cmd.Dir = projectDir
	output, err := cmd.CombinedOutput()
	if err != nil {
		fmt.Printf("⚠ Swagger 文档自动生成失败: %v\n%s\n", err, string(output))
		return
	}
	fmt.Println("✓ Swagger API 文档已自动生成 (docs/swagger.json)")
}

// getProjectDir finds the project root directory.
// It tries the current working directory first (for go run), then the executable directory.
func getProjectDir() string {
	// Try current working directory
	cwd, err := os.Getwd()
	if err == nil {
		// Verify by checking if SceneServerApplication.go exists
		mainFile := filepath.Join(cwd, "SceneServerApplication.go")
		if _, err := os.Stat(mainFile); err == nil {
			return cwd
		}
	}

	// Try executable directory
	exePath, err := os.Executable()
	if err == nil {
		exeDir := filepath.Dir(exePath)
		mainFile := filepath.Join(exeDir, "SceneServerApplication.go")
		if _, err := os.Stat(mainFile); err == nil {
			return exeDir
		}
	}

	return ""
}
